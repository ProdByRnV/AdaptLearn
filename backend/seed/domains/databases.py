"""Databases: storing and querying data well, from relational design and SQL to NoSQL and scaling.

SQL Basics is defined in Web Development and shared here. Data Formats (Foundations) leads into
document databases and Errors & Exceptions (Python) into using databases from Python.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Relational foundations -------------------------------------------------------------
    Topic(
        "db_data_models", "Databases & Data Models",
        "What a database management system does and the main ways to model data: relational tables "
        "with rows and keys, documents, key-value pairs and graphs, and when each fits.",
        1,
        (
            article("IBM: What is a database?", "https://www.ibm.com/think/topics/database"),
            video("7 Database Paradigms (Fireship)", "https://www.youtube.com/watch?v=W2Z7fbCLSTw"),
        ),
    ),
    Topic(
        "db_keys_constraints", "Keys & Constraints",
        "Letting the database protect its own data: primary and foreign keys, NOT NULL, UNIQUE and "
        "CHECK constraints, and what happens to related rows on delete.",
        2,
        (
            docs("PostgreSQL docs: Constraints", "https://www.postgresql.org/docs/current/ddl-constraints.html"),
        ),
    ),
    Topic(
        "db_sql_joins", "SQL Joins in Depth",
        "Combining tables: inner joins, left, right and full outer joins, joining a table to itself, "
        "and how missing matches turn into NULLs.",
        2,
        (
            docs("PostgreSQL docs: Joins between tables", "https://www.postgresql.org/docs/current/tutorial-join.html"),
            article("SQLBolt: Multi-table queries with JOINs", "https://sqlbolt.com/lesson/select_queries_with_joins"),
        ),
    ),
    Topic(
        "db_sql_aggregation", "Aggregation & Grouping",
        "Summarising rows with COUNT, SUM, AVG, MIN and MAX, grouping with GROUP BY, filtering groups "
        "with HAVING, and how aggregates treat NULLs.",
        2,
        (
            docs("PostgreSQL docs: Aggregate functions", "https://www.postgresql.org/docs/current/tutorial-agg.html"),
            article("SQLBolt: Queries with aggregates", "https://sqlbolt.com/lesson/select_queries_with_aggregates"),
        ),
    ),
    Topic(
        "db_subqueries_ctes", "Subqueries & CTEs",
        "Queries inside queries: subqueries in WHERE and FROM, EXISTS and IN, and common table "
        "expressions (WITH) that break a complex query into readable named steps.",
        3,
        (
            docs("PostgreSQL docs: WITH queries (common table expressions)", "https://www.postgresql.org/docs/current/queries-with.html"),
        ),
    ),
    Topic(
        "db_window_functions", "Window Functions",
        "Calculations across related rows without collapsing them: OVER and PARTITION BY, ranking "
        "with ROW_NUMBER and RANK, running totals, and comparing a row with the one before it.",
        3,
        (
            docs("PostgreSQL docs: Window functions", "https://www.postgresql.org/docs/current/tutorial-window.html"),
        ),
    ),
    Topic(
        "db_schema_design", "Schema Design & Normalisation",
        "Designing tables that stay consistent: entities and relationships, one-to-many and "
        "many-to-many links, the first three normal forms, and when denormalising is worth it.",
        3,
        (
            article("IBM: What is database normalisation?", "https://www.ibm.com/think/topics/database-normalization"),
            article("freeCodeCamp: Database normalisation, 1NF, 2NF, 3NF", "https://www.freecodecamp.org/news/database-normalization-1nf-2nf-3nf-table-examples/"),
            video("Database Design Course (freeCodeCamp)", "https://www.youtube.com/watch?v=ztHopE5Wnpc"),
        ),
    ),
    # --- Performance and correctness ------------------------------------------------------------
    Topic(
        "db_indexes", "Indexes & Query Performance",
        "Making queries fast: how a B-tree index finds rows, which queries an index helps, the cost "
        "of indexes on writes, and reading a query plan with EXPLAIN.",
        3,
        (
            docs("PostgreSQL docs: Indexes", "https://www.postgresql.org/docs/current/indexes.html"),
            docs("PostgreSQL docs: Using EXPLAIN", "https://www.postgresql.org/docs/current/using-explain.html"),
            article("Use The Index, Luke (free book)", "https://use-the-index-luke.com/"),
        ),
    ),
    Topic(
        "db_transactions", "Transactions & ACID",
        "Keeping data correct when several changes belong together: BEGIN, COMMIT and ROLLBACK, and "
        "what atomicity, consistency, isolation and durability each guarantee.",
        3,
        (
            docs("PostgreSQL docs: Transactions", "https://www.postgresql.org/docs/current/tutorial-transactions.html"),
        ),
    ),
    Topic(
        "db_isolation_locking", "Isolation Levels & Locking",
        "What happens when transactions run at the same time: dirty reads, non-repeatable reads and "
        "phantoms, the standard isolation levels, row locks and SELECT FOR UPDATE, and deadlocks.",
        4,
        (
            docs("PostgreSQL docs: Transaction isolation", "https://www.postgresql.org/docs/current/transaction-iso.html"),
        ),
    ),
    Topic(
        "db_python_access", "Using Databases from Python",
        "Talking to a database from code: connections and cursors with sqlite3, parameterised "
        "queries that prevent SQL injection, committing transactions, and what an ORM such as "
        "SQLAlchemy adds.",
        3,
        (
            docs("Python docs: sqlite3", "https://docs.python.org/3/library/sqlite3.html"),
            docs("OWASP: SQL injection prevention cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"),
            docs("SQLAlchemy: Unified tutorial", "https://docs.sqlalchemy.org/en/20/tutorial/index.html"),
        ),
    ),
    Topic(
        "db_scaling", "Replication, Backups & Scaling",
        "Keeping data safe and available as it grows: backups and restoring them, read replicas, "
        "failover, sharding data across servers, and the trade-offs the CAP theorem describes.",
        4,
        (
            docs("PostgreSQL docs: Backup and restore", "https://www.postgresql.org/docs/current/backup.html"),
            docs("PostgreSQL docs: High availability and replication", "https://www.postgresql.org/docs/current/high-availability.html"),
            article("AWS: What is database sharding?", "https://aws.amazon.com/what-is/database-sharding/"),
        ),
    ),
    Topic(
        "db_data_warehousing", "Data Warehouses & Analytics",
        "Databases built for analysis: OLTP versus OLAP, star schemas with fact and dimension "
        "tables, column-oriented storage, and loading data with ETL pipelines.",
        3,
        (
            article("IBM: OLAP vs OLTP", "https://www.ibm.com/think/topics/olap-vs-oltp"),
            article("AWS: What is a data warehouse?", "https://aws.amazon.com/what-is/data-warehouse/"),
        ),
    ),
    # --- Beyond relational ------------------------------------------------------------------------
    Topic(
        "db_nosql", "NoSQL Databases",
        "Databases without fixed tables: document, key-value, wide-column and graph stores, flexible "
        "schemas, horizontal scaling, and the consistency they may trade away.",
        2,
        (
            article("MongoDB: What is NoSQL?", "https://www.mongodb.com/resources/basics/databases/nosql-explained"),
            article("IBM: What is a NoSQL database?", "https://www.ibm.com/think/topics/nosql-databases"),
        ),
    ),
    Topic(
        "db_mongodb", "Document Databases (MongoDB)",
        "Storing JSON-like documents in MongoDB: collections and documents, embedding versus "
        "referencing related data, querying with filters, and indexes on fields.",
        3,
        (
            docs("MongoDB docs: Database manual", "https://www.mongodb.com/docs/manual/"),
            docs("MongoDB docs: CRUD operations", "https://www.mongodb.com/docs/manual/crud/"),
            video("MongoDB in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=-bt_y4Loofg"),
        ),
    ),
    Topic(
        "db_redis", "Key-Value Stores & Caching (Redis)",
        "Fast in-memory data with Redis: keys and values, data types such as lists, hashes and sets, "
        "expiring keys, and caching database results without serving stale data for too long.",
        3,
        (
            docs("Redis docs: Data types", "https://redis.io/docs/latest/develop/data-types/"),
            docs("Redis docs: Quick starts", "https://redis.io/docs/latest/develop/get-started/"),
            video("Redis in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=G1rOthIU-uo"),
        ),
    ),
    Topic(
        "db_graph_databases", "Graph Databases",
        "Data as nodes and relationships: when connections matter more than rows, property graphs, "
        "and querying paths with Cypher in a database such as Neo4j.",
        3,
        (
            docs("Neo4j: What is a graph database?", "https://neo4j.com/docs/getting-started/graph-database/"),
            docs("Neo4j: What is Cypher?", "https://neo4j.com/docs/getting-started/cypher/"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("sql_basics", "db_keys_constraints"),
    ("db_data_models", "db_keys_constraints"),
    ("sql_basics", "db_sql_joins"),
    ("sql_basics", "db_sql_aggregation"),
    ("db_sql_joins", "db_subqueries_ctes"),
    ("db_sql_aggregation", "db_subqueries_ctes"),
    ("db_subqueries_ctes", "db_window_functions"),
    ("db_keys_constraints", "db_schema_design"),
    ("db_sql_joins", "db_schema_design"),

    ("db_sql_joins", "db_indexes"),
    ("db_keys_constraints", "db_indexes"),
    ("db_keys_constraints", "db_transactions"),
    ("db_transactions", "db_isolation_locking"),
    ("db_keys_constraints", "db_python_access"),
    ("python_exceptions", "db_python_access"),
    ("db_transactions", "db_scaling"),
    ("db_indexes", "db_scaling"),
    ("db_schema_design", "db_data_warehousing"),
    ("db_sql_aggregation", "db_data_warehousing"),

    ("db_data_models", "db_nosql"),
    ("db_nosql", "db_mongodb"),
    ("data_formats", "db_mongodb"),
    ("db_nosql", "db_redis"),
    ("db_nosql", "db_graph_databases"),
)

DATABASES = Domain(
    id="databases",
    name="Databases",
    description=(
        "Storing and querying data well: relational design and SQL in depth, indexes and "
        "transactions, databases from code, NoSQL stores such as MongoDB, Redis and graph "
        "databases, and keeping data safe as it grows."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
    shared=("sql_basics",),
)
