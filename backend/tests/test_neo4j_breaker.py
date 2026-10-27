"""Neo4j fail-fast (Phase 19): during an outage, queries are refused at once instead of each one
waiting seconds for the driver, and one query at a time checks whether Neo4j is back."""

import pytest
from neo4j import RoutingControl
from neo4j.exceptions import ServiceUnavailable, SessionExpired

from db import neo4j_db


class Record:
    def __init__(self, data):
        self._data = data

    def data(self):
        return self._data


class FakeDriver:
    """Answers or fails as scripted; counts the queries that reached it."""

    def __init__(self):
        self.calls = []
        self.fail_with = None

    def execute_query(self, query, params, routing_):
        self.calls.append((query, params, routing_))
        if self.fail_with:
            raise self.fail_with
        return [Record({"ok": 1})], None, None


@pytest.fixture()
def driver(monkeypatch):
    fake = FakeDriver()
    monkeypatch.setattr(neo4j_db, "get_driver", lambda: fake)
    return fake


@pytest.fixture()
def now(monkeypatch):
    clock = {"t": 1000.0}
    monkeypatch.setattr(neo4j_db.time, "monotonic", lambda: clock["t"])
    return clock


def test_queries_pass_through_while_neo4j_is_up(driver, now):
    assert neo4j_db.read("MATCH (n) RETURN n", domain="x") == [{"ok": 1}]
    assert neo4j_db.write("CREATE (n)") == [{"ok": 1}]
    assert driver.calls == [
        ("MATCH (n) RETURN n", {"domain": "x"}, RoutingControl.READ),
        ("CREATE (n)", {}, RoutingControl.WRITE),
    ]


@pytest.mark.parametrize("error", [ServiceUnavailable("down"), SessionExpired("gone")])
def test_after_a_failure_queries_fail_at_once(driver, now, error):
    driver.fail_with = error
    with pytest.raises(type(error)):
        neo4j_db.read("Q")
    driver.fail_with = None  # even if Neo4j came back, the next few seconds don't wait on it
    now["t"] += neo4j_db.RETRY_AFTER_SECONDS - 0.1
    with pytest.raises(ServiceUnavailable, match="not retrying yet"):
        neo4j_db.read("Q")
    with pytest.raises(ServiceUnavailable):
        neo4j_db.write("Q")
    assert len(driver.calls) == 1


def test_one_query_checks_after_the_wait_and_recovery_clears_the_state(driver, now):
    driver.fail_with = ServiceUnavailable("down")
    with pytest.raises(ServiceUnavailable):
        neo4j_db.read("Q")
    now["t"] += neo4j_db.RETRY_AFTER_SECONDS
    driver.fail_with = None
    assert neo4j_db.read("Q") == [{"ok": 1}]
    assert neo4j_db.read("Q") == [{"ok": 1}]
    assert len(driver.calls) == 3


def test_a_failed_check_starts_another_wait(driver, now):
    driver.fail_with = ServiceUnavailable("down")
    with pytest.raises(ServiceUnavailable):
        neo4j_db.read("Q")
    now["t"] += neo4j_db.RETRY_AFTER_SECONDS
    with pytest.raises(ServiceUnavailable):
        neo4j_db.read("Q")  # the check, which reaches the driver and fails
    assert len(driver.calls) == 2
    now["t"] += 1
    with pytest.raises(ServiceUnavailable, match="not retrying yet"):
        neo4j_db.read("Q")
    assert len(driver.calls) == 2


def test_while_one_query_checks_the_others_still_fail_fast(driver, now, monkeypatch):
    driver.fail_with = ServiceUnavailable("down")
    with pytest.raises(ServiceUnavailable):
        neo4j_db.read("Q")
    now["t"] += neo4j_db.RETRY_AFTER_SECONDS
    driver.fail_with = None
    seen_during_check = []

    def slow_query(query, params, routing_):
        # Another request arrives while this check is still running.
        with pytest.raises(ServiceUnavailable, match="not retrying yet"):
            neo4j_db.read("other")
        seen_during_check.append(True)
        return [Record({"ok": 1})], None, None

    monkeypatch.setattr(driver, "execute_query", slow_query)
    assert neo4j_db.read("Q") == [{"ok": 1}]
    assert seen_during_check == [True]


def test_other_errors_do_not_trip_it(driver, now):
    driver.fail_with = ValueError("bad query")
    with pytest.raises(ValueError):
        neo4j_db.read("Q")
    driver.fail_with = None
    assert neo4j_db.read("Q") == [{"ok": 1}]


def test_reset_forgets_a_failure(driver, now):
    driver.fail_with = ServiceUnavailable("down")
    with pytest.raises(ServiceUnavailable):
        neo4j_db.read("Q")
    neo4j_db.reset_breaker()
    driver.fail_with = None
    assert neo4j_db.read("Q") == [{"ok": 1}]
