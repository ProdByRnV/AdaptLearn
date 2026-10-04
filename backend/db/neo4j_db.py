from typing import Any

from neo4j import Driver, GraphDatabase, NotificationMinimumSeverity, RoutingControl

from config import get_settings

_driver: Driver | None = None


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


def read(query: str, **params: Any) -> list[dict[str, Any]]:
    """Run a parameterized read query and return each record as a dict."""
    records, _, _ = get_driver().execute_query(query, params, routing_=RoutingControl.READ)
    return [record.data() for record in records]


def write(query: str, **params: Any) -> list[dict[str, Any]]:
    """Run a parameterized write query and return each record as a dict."""
    records, _, _ = get_driver().execute_query(query, params, routing_=RoutingControl.WRITE)
    return [record.data() for record in records]


def check_connection() -> None:
    """Raise if Neo4j is unreachable or the credentials are wrong (single attempt, no retries)."""
    get_driver().verify_connectivity()
