import threading
import time
from typing import Any

from neo4j import Driver, GraphDatabase, NotificationMinimumSeverity, RoutingControl
from neo4j.exceptions import ServiceUnavailable, SessionExpired

from config import get_settings

_driver: Driver | None = None

# Fail fast while Neo4j is down. Each failed query takes several seconds (connection attempts and
# retries), so during an outage concurrent requests pile up past the browser's 15 s timeout and
# hold server threads. After a failure, queries are refused at once for RETRY_AFTER_SECONDS; then
# one query at a time is let through to see whether Neo4j is back.
RETRY_AFTER_SECONDS = 5.0
_breaker_lock = threading.Lock()
_failing = False
_retry_at = 0.0


def get_driver() -> Driver:
    """Return the shared Neo4j driver, creating it on first use."""
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=5.0,
            connection_acquisition_timeout=10.0,
            # Default is 30s of retries, which leaves requests hanging when Neo4j is down.
            max_transaction_retry_time=5.0,
            # Skip INFORMATION notices such as "constraint already exists" on every startup.
            notifications_min_severity=NotificationMinimumSeverity.WARNING,
        )
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def reset_breaker() -> None:
    """Forget any recent failure (tests, or after reconnecting by hand)."""
    global _failing, _retry_at
    with _breaker_lock:
        _failing = False
        _retry_at = 0.0


def _execute(query: str, params: dict[str, Any], routing: RoutingControl) -> list[dict[str, Any]]:
    global _failing, _retry_at
    with _breaker_lock:
        if _failing:
            now = time.monotonic()
            if now < _retry_at:
                raise ServiceUnavailable("Neo4j failed moments ago; not retrying yet")
            _retry_at = now + RETRY_AFTER_SECONDS  # this query checks; others keep failing fast meanwhile
    try:
        records, _, _ = get_driver().execute_query(query, params, routing_=routing)
    except (ServiceUnavailable, SessionExpired):
        with _breaker_lock:
            _failing = True
            _retry_at = time.monotonic() + RETRY_AFTER_SECONDS
        raise
    with _breaker_lock:
        _failing = False
    return [record.data() for record in records]


def read(query: str, **params: Any) -> list[dict[str, Any]]:
    """Run a parameterized read query and return each record as a dict."""
    return _execute(query, params, RoutingControl.READ)


def write(query: str, **params: Any) -> list[dict[str, Any]]:
    """Run a parameterized write query and return each record as a dict."""
    return _execute(query, params, RoutingControl.WRITE)


def check_connection() -> None:
    """Raise if Neo4j is unreachable or the credentials are wrong (single attempt, no retries)."""
    get_driver().verify_connectivity()
