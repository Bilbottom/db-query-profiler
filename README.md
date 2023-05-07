# Database Query Profiler 🗃️⏱️

Lightweight database query profiler.

This tool is database-agnostic -- just provide a class that connects to your database with an `execute` method, and the queries that you want to profile.

## Installation ⬇️

This is currently only available on GitHub, so you'll need to supply the GitHub URL to `pip`:

```
pip install git+https://github.com/Bilbottom/db-query-profiler.git
```

## Sample Output 📝

Given a set of queries (details below), this package prints the average time in seconds taken to run each query, as well as the percentage of the total time taken by each query.

The [`tqdm`](https://github.com/tqdm/tqdm) package is used to show progress of the queries being run.

A typical output will look something like this:

```
Start time: 2023-05-07 12:38:06.879738
----------------------------------------
100%|██████████| 5/5 [00:01<00:00,  3.29it/s]
query-1.sql: 0.10063192 (33.4%)
query-2.sql: 0.20044784 (66.6%)
----------------------------------------
End time: 2023-05-07 12:38:08.757555
```

## Usage 📖

The package exposes a single method, `time_queries`, which currently requires:

1. A database connection/cursor class that implements an `execute` method.
2. The number of times to re-run each query.
3. A directory containing the SQL files with the queries to run.

There should only be a single query in each file, and the file name will be used as the query name in the output.

For the following examples, assume that there are 2 SQL files in the `queries` directory.

### SQLite Example
> Official documentation: https://docs.python.org/3/library/sqlite3.html

```python
import sqlite3
import db_query_profiler


def main() -> None:
    db_conn = sqlite3.connect(":memory:")  # Or a path to a database file
    db_query_profiler.time_queries(
        conn=db_conn,
        repeat=5,
        directory="queries"
    )

    
if __name__ == "__main__":
    main()
```


## Warnings ⚠️

This package will open and run all the files in the specified directory, so be careful about what you put in there -- potentially unsafe SQL commands could be run.

This package only reads from the database, so it's encouraged to configure your database connection in a read-only way.

### SQLite
> Official documentation:
> - https://docs.python.org/3/library/sqlite3.html#sqlite3.connect
> - https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris

To connect to a SQLite database in a read-only way, use the `uri=True` parameter with `file:` and `?mode=ro` surrounding the database path when connecting:
```python
db_conn = sqlite3.connect("file:path/to/database.db?mode=ro", uri=True)
```
