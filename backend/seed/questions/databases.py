"""Curated fallback questions for Databases. Code is Markdown."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- Relational foundations -------------------------------------------------------------
    "db_data_models": [
        q("Which kind of database stores data in tables of rows and columns linked by keys?",
          "A relational database", ("A key-value store", "A document database", "A graph database"),
          "Relational databases organise data in tables and connect them with primary and foreign keys; SQL "
          "queries them."),
        q("Which data model is built around nodes and the relationships between them?", "A graph database",
          ("A key-value store", "A relational database", "A column-family store"),
          "Graph databases store relationships directly, which makes following connections fast."),
        q("What does a database management system (DBMS) do?",
          "Stores data and handles queries, concurrent access and recovery",
          ("Converts spreadsheets into web pages automatically", "Designs the tables for you from your application code",
           "Encrypts files on the disk so nobody can read them"),
          "A DBMS such as PostgreSQL manages storage, answers queries, lets many users work at once safely, "
          "and recovers after crashes."),
    ],
    "db_keys_constraints": [
        q("A foreign key on `orders.customer_id` references `customers.id`. What does it guarantee?",
          "Every non-null customer_id matches an existing customer",
          ("Every customer has at least one order", "No two orders share the same customer_id",
           "customer_id values are generated automatically"),
          "A foreign key stops orders pointing at customers that don't exist. It says nothing about how many "
          "orders a customer has."),
        q("A table has `PRIMARY KEY (id)`. What does that enforce on id?", "Unique and not NULL",
          ("Unique, but NULL is allowed", "Not NULL, but duplicates are allowed", "Automatically increasing by 1"),
          "A primary key identifies each row, so it must be unique and present. Auto-increment is a separate "
          "default, not part of the key."),
        q("Which constraint stops a price below zero from being stored?", "`CHECK (price >= 0)`",
          ("`UNIQUE (price)`", "`NOT NULL`", "`DEFAULT 0`"),
          "A CHECK constraint rejects any row for which its condition is false. DEFAULT only fills in a value "
          "when none is given."),
    ],
    "db_sql_joins": [
        q("customers has 3 rows and 2 of them have orders. What does `customers LEFT JOIN orders` return for "
          "the customer without orders?", "One row with NULLs in the orders columns",
          ("No row at all", "A row repeated for every order", "An error, because the match is missing"),
          "A left join keeps every row of the left table; where there is no match, the right table's columns "
          "are NULL. An inner join would drop the row."),
        q("Which join keeps only rows that have a match in both tables?", "INNER JOIN",
          ("LEFT JOIN", "FULL OUTER JOIN", "CROSS JOIN"),
          "INNER JOIN returns matching pairs only. Outer joins also keep unmatched rows, and CROSS JOIN pairs "
          "every row with every row."),
        q("employees has a manager_id column pointing at another employee. How do you list each employee next "
          "to their manager's name?", "Join employees to itself, using two aliases",
          ("Use GROUP BY on the manager_id column", "Create a second copy of the table first",
           "It needs a subquery; joins can't do it"),
          "A self-join treats the table as two: `FROM employees e JOIN employees m ON e.manager_id = m.id`."),
    ],
    "db_sql_aggregation": [
        q("What is the difference between WHERE and HAVING?",
          "WHERE filters rows before grouping; HAVING filters groups after",
          ("HAVING filters rows before grouping; WHERE filters groups after",
           "They are the same; HAVING is an older spelling", "WHERE works on numbers; HAVING works on text"),
          "WHERE can't use aggregates because groups don't exist yet; HAVING runs on the grouped results, "
          "e.g. `HAVING COUNT(*) > 5`."),
        q("A column holds 4, NULL and 8. What does `AVG` of the column return?", "6", ("4", "NULL", "An error"),
          "Aggregates other than COUNT(*) skip NULLs, so AVG averages 4 and 8."),
        q("What does each row of `SELECT dept, COUNT(*) FROM staff GROUP BY dept` show?",
          "One department and how many staff it has",
          ("Every staff member with their department", "The total number of staff", "The departments sorted by size"),
          "GROUP BY makes one row per department, and COUNT(*) counts the rows in each group. Order isn't "
          "guaranteed without ORDER BY."),
    ],
    "db_subqueries_ctes": [
        q("What does a WITH clause (a common table expression) let you do?", "Name a subquery and use it in the main query",
          ("Store a table permanently in the database", "Run two queries at exactly the same time",
           "Lock a table while the query runs"),
          "A CTE gives a subquery a name for the rest of the statement, so complex queries read as steps. It "
          "isn't stored afterwards."),
        q("Which query lists customers who have placed at least one order?",
          "`SELECT * FROM customers c WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)`",
          ("`SELECT * FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)`",
           "`SELECT * FROM customers WHERE id = (SELECT customer_id FROM orders)`",
           "`SELECT * FROM customers c WHERE EXISTS (SELECT 1 FROM orders)`"),
          "The correlated EXISTS checks each customer for a matching order. With = the subquery may return "
          "several rows and fail, and an uncorrelated EXISTS is true for everyone once any order exists."),
        q("Why can `WHERE id NOT IN (SELECT customer_id FROM orders)` return no rows at all?",
          "If the subquery returns a NULL, NOT IN is never true",
          ("NOT IN can't be used together with a subquery", "Subqueries in WHERE always run before the table exists",
           "NOT IN only compares the first row of the subquery"),
          "Comparing with NULL gives unknown, so `x NOT IN (1, NULL)` is never true. NOT EXISTS avoids this "
          "trap."),
    ],
    "db_window_functions": [
        q("How does a window function differ from GROUP BY aggregation?",
          "It adds a value to each row instead of collapsing rows into groups",
          ("It can only be used on tables that have a date column", "It collapses rows into one row per group, like GROUP BY",
           "It runs faster because it skips the ORDER BY clause"),
          "With OVER (...), every row stays in the result and gets a value computed from its window, such as "
          "its rank or a running total."),
        q("Scores are 90, 90 and 80, ranked from highest. What do `RANK()` and `DENSE_RANK()` give the 80?",
          "RANK gives 3; DENSE_RANK gives 2", ("RANK gives 2; DENSE_RANK gives 3", "Both give 3", "Both give 2"),
          "Both give the tied 90s rank 1. RANK then skips to 3 because two rows came first; DENSE_RANK leaves "
          "no gaps."),
        q("Which expression gives a running total of amount in date order?", "`SUM(amount) OVER (ORDER BY date)`",
          ("`SUM(amount) GROUP BY date`", "`SUM(amount) OVER (PARTITION BY date)`", "`COUNT(amount) OVER (ORDER BY date)`"),
          "With ORDER BY in the window, the sum covers every row up to the current one. PARTITION BY date alone "
          "gives each date's total, and COUNT counts rows instead of adding amounts."),
    ],
    "db_schema_design": [
        q("Students take many courses and courses have many students. How is this usually modelled?",
          "A third table linking student and course IDs",
          ("A courses column listing IDs in each student row", "One table holding both students and courses",
           "A foreign key from students to courses"),
          "A many-to-many relationship needs a junction table with one row per enrolment and foreign keys to "
          "both tables."),
        q("Every order row stores the customer's name and email. What problem does that cause?",
          "Changing an email means updating many rows, which can disagree",
          ("The database can't store more than one order per customer", "Emails can't be indexed when they repeat",
           "Queries on orders always need a join to work"),
          "Duplicated facts can drift apart (an update anomaly). Normalising keeps customer details in one "
          "customers row referenced by orders."),
        q("When is denormalising (storing some data twice) a reasonable choice?",
          "When reads far outnumber writes and joins are too slow",
          ("When you want the data to stay consistent automatically", "Whenever a table has more than ten columns",
           "When the database doesn't support foreign keys"),
          "Denormalising trades extra work keeping copies in step for faster reads, so it pays off for "
          "read-heavy data such as reports."),
    ],
    # --- Performance and correctness ------------------------------------------------------------
    "db_indexes": [
        q("Which statement is an index on `users.email` most likely to speed up?",
          "`SELECT * FROM users WHERE email = 'a@b.com'`",
          ("`SELECT * FROM users WHERE LOWER(name) = 'ana'`", "`INSERT INTO users (email) VALUES ('a@b.com')`",
           "`SELECT * FROM users WHERE created_at > '2026-01-01'`"),
          "An index on email finds rows by email without scanning the table. The other queries filter on "
          "other columns, and an insert has to update the index, which makes it slower."),
        q("What is the main cost of adding many indexes to a table?", "Every insert and update must also update each index",
          ("Queries that use the indexed columns get slower", "The table can no longer have a primary key",
           "Each index limits the table to fewer rows"),
          "Indexes speed up reads but must be maintained on every write, and they take disk space."),
        q("What does EXPLAIN show?", "The plan the database will use to run a query",
          ("The meaning of each column in a table", "The SQL errors in a query, explained in plain words",
           "The history of queries run on a table"),
          "EXPLAIN shows the chosen plan, such as an index scan or a sequential scan, with cost estimates; "
          "EXPLAIN ANALYZE also runs the query and reports real timings."),
    ],
    "db_transactions": [
        q("A transfer debits one account and credits another. Why put both in one transaction?",
          "So either both changes happen or neither does",
          ("So the two updates run in parallel and finish sooner", "So other users can never read either account again",
           "So the database skips the constraint checks"),
          "Atomicity: if anything fails between the two updates, the transaction rolls back and no money "
          "disappears."),
        q("What does ROLLBACK do?", "Undoes every change made since the transaction began",
          ("Undoes only the last statement in the transaction", "Restores the database from last night's backup",
           "Saves the changes and ends the transaction"),
          "ROLLBACK discards the whole transaction's changes. COMMIT is the one that saves them."),
        q("Which ACID property means committed changes survive a power cut?", "Durability",
          ("Atomicity", "Isolation", "Consistency"),
          "Durability: once COMMIT returns, the change is on stable storage (via the write-ahead log) and "
          "survives crashes."),
    ],
    "db_isolation_locking": [
        q("A transaction reads a row twice and gets different values because another transaction committed in "
          "between. What is this called?", "A non-repeatable read",
          ("A dirty read", "A phantom read", "A deadlock"),
          "A dirty read sees uncommitted data, and a phantom is a new row matching a repeated query. Higher "
          "isolation levels such as REPEATABLE READ prevent non-repeatable reads."),
        q("Two transactions each hold a lock the other is waiting for. What does PostgreSQL do?",
          "Detects the deadlock and aborts one of them",
          ("Waits forever until someone restarts the server", "Lets both continue and merges their changes",
           "Gives both locks to the transaction that started first"),
          "PostgreSQL checks for deadlocks after a short wait and cancels one transaction with an error so the "
          "other can finish; the application can retry."),
        q("Why use `SELECT ... FOR UPDATE` before changing a row based on its current value?",
          "It locks the row so others can't change it in between",
          ("It copies the row so the original is never changed", "It updates the row and returns its old value",
           "It tells the database to skip the row's indexes"),
          "Without the lock, two transactions can read the same balance and both write back a result, losing "
          "one update."),
    ],
    "db_python_access": [
        q("Which line safely passes a user's `name` to a query with sqlite3?",
          "`cur.execute('SELECT * FROM users WHERE name = ?', (name,))`",
          ("`cur.execute(f\"SELECT * FROM users WHERE name = '{name}'\")`",
           "`cur.execute('SELECT * FROM users WHERE name = ' + name)`",
           "`cur.execute('SELECT * FROM users WHERE name = %s' % name)`"),
          "The ? placeholder sends the value separately from the SQL. The others paste user input into the "
          "query text, which allows SQL injection."),
        q("Why are parameterised queries safer than building SQL with string formatting?",
          "The values are sent separately, so they can't change the SQL",
          ("They encrypt the values before sending them", "They run the query twice to check the result",
           "They make the database ignore unknown columns"),
          "Input such as `' OR 1=1 --` stays a plain value instead of becoming part of the query."),
        q("With sqlite3, inserted rows seem to work but vanish when the program ends. What is missing?",
          "`conn.commit()`", ("`cur.fetchall()`", "`conn.cursor()`", "`cur.close()`"),
          "sqlite3 opens a transaction for changes; without commit, they are rolled back when the connection "
          "closes. Using the connection as a context manager commits on success."),
    ],
    "db_scaling": [
        q("What is a read replica?", "A copy kept up to date from the primary that serves reads",
          ("A backup file restored once a day for reporting", "A second primary that accepts writes from all users",
           "A cache that stores the results of recent queries"),
          "Replicas receive the primary's changes continuously and take read traffic off it; writes still go to "
          "the primary."),
        q("Why isn't a backup proven until you have restored it?",
          "Backups can be incomplete or unusable without anyone noticing",
          ("Databases delete a backup unless it is restored within a week", "A backup only counts once it has been copied to a replica",
           "Restoring is the step that compresses the backup file"),
          "Only a test restore shows that the backup is complete and that the steps to recover actually work."),
        q("What does sharding do?", "Splits rows across several servers, each holding part of the data",
          ("Copies all rows to several servers for faster reads", "Breaks a table into smaller tables with fewer columns",
           "Compresses old rows so the table takes less space"),
          "Sharding spreads data (and writes) by a key such as user ID. Copying everything to several servers is "
          "replication."),
    ],
    "db_data_warehousing": [
        q("What is the main difference between OLTP and OLAP workloads?",
          "OLTP handles many small transactions; OLAP runs large analytical queries",
          ("OLTP stores only text; OLAP stores only numbers and dates", "OLTP runs in the cloud; OLAP only runs on local servers",
           "OLTP is used for reports; OLAP processes customer orders"),
          "An online store's orders are OLTP; scanning a year of orders for trends is OLAP, which warehouses "
          "are built for."),
        q("In a star schema, what does a fact table hold?", "Measurable events, such as sales, with keys to dimensions",
          ("Descriptive details, such as product names and regions", "A copy of every source table, unchanged",
           "Only the totals for each month, already summed"),
          "Facts are the numbers being analysed; dimension tables around them describe the who, what, where "
          "and when."),
        q("Why do analytical databases often store data by column instead of by row?",
          "Queries read a few columns of many rows, and columns compress well",
          ("Column storage makes single-row updates much faster", "Rows can't be stored once a table has a million rows",
           "It removes the need for any indexes or a query planner"),
          "Reading only the needed columns, packed together, saves a lot of I/O. The trade-off is slower "
          "single-row writes."),
    ],
    # --- Beyond relational ------------------------------------------------------------------------
    "db_nosql": [
        q("Which is a common reason to choose a document database?",
          "Records vary in shape and are read as whole documents",
          ("Data needs many joins across strictly related tables", "Every record must follow one fixed schema",
           "The data is a network of relationships to traverse"),
          "Documents suit self-contained records with varying fields. Heavily related data suits relational "
          "tables, and networks of connections suit graphs."),
        q("What does horizontal scaling mean?", "Adding more servers and spreading the data across them",
          ("Moving to one bigger server with more memory", "Adding more columns to every table",
           "Storing tables side by side in the same file"),
          "A bigger single server is vertical scaling. Many NoSQL systems are designed to spread across many "
          "machines."),
        q("Many NoSQL systems offer eventual consistency. What does that mean?",
          "Replicas may briefly differ but converge if writes stop",
          ("Every read always sees the latest write", "Data is only saved when the server shuts down",
           "Writes are checked against a schema eventually"),
          "Replicas apply updates asynchronously, so a read may be stale for a moment. Strong consistency would "
          "guarantee the latest write."),
    ],
    "db_mongodb": [
        q("A blog post's few comments are always shown with it. How would you usually model this in MongoDB?",
          "Embed the comments as an array inside the post document",
          ("Store each comment in a separate database", "Put posts and comments in one SQL table",
           "Store the comments as a single long string"),
          "Data read together is usually embedded, so one read fetches it. Many or independently used items "
          "are better referenced."),
        q("Which MongoDB query finds users older than 30?", "`db.users.find({ age: { $gt: 30 } })`",
          ("`db.users.find({ age: > 30 })`", "`db.users.select({ age: { $gt: 30 } })`", "`db.users.find({ $gt: { age: 30 } })`"),
          "Query operators such as $gt go inside the field's condition. The first option isn't valid syntax, "
          "and collections have no select method."),
        q("Why add an index on a field you often filter by in MongoDB?",
          "So queries avoid scanning every document in the collection",
          ("So the field becomes required in every document", "So duplicate values in the field are merged together",
           "So the field can hold any type of value"),
          "As in relational databases, an index finds matching documents directly instead of checking each one."),
    ],
    "db_redis": [
        q("Where does Redis keep its data while it runs?", "In memory, optionally saved to disk",
          ("Only on disk, read for every request", "In the browser's local storage", "In a relational table on another server"),
          "Redis is an in-memory store, which makes it very fast; snapshots or an append-only file can persist "
          "data to disk."),
        q("What does setting an expiry (TTL) on a cached key do?", "Redis deletes the key automatically after that time",
          ("Redis refuses to return the key until the time passes", "The key is copied to disk after that time",
           "The key's value is locked until the time passes"),
          "Expiring keys stop a cache serving data that is too old and free memory without manual cleanup."),
        q("With caching, a user updates their profile but still sees the old one. What is the usual fix?",
          "Delete or update the cached entry when the data changes",
          ("Make the cache larger so it holds more entries", "Read from the cache twice to make sure",
           "Store the cache in the same table as the data"),
          "Invalidating the cache on writes (or a short TTL) keeps cached copies from going stale."),
    ],
    "db_graph_databases": [
        q("Which question is a graph database especially good at answering?",
          "Which friends of my friends also like this film?",
          ("What is the total of all sales last month?", "Which rows have a price above 100?",
           "How many characters are in each name?"),
          "Following chains of relationships is what graph databases are built for; the others are simple "
          "filters and totals any database handles."),
        q("In Cypher, what does `(a:Person)-[:KNOWS]->(b:Person)` describe?",
          "A KNOWS relationship from one Person node to another",
          ("A table join between two Person tables", "Two Person nodes that are not connected",
           "A Person node with a property called KNOWS"),
          "Parentheses are nodes with labels, square brackets a relationship with its type, and the arrow its "
          "direction."),
        q("In a property graph, where can properties (key-value data) be stored?", "On both nodes and relationships",
          ("Only on nodes", "Only on relationships", "In a separate table linked by keys"),
          "A relationship such as KNOWS can carry its own data, e.g. `{since: 2020}`."),
    ],
}
