import sqlite3
import shutil
import time
from pathlib import Path

import query_timer


def create_database_connection() -> sqlite3.Connection:
    """
    Create a database with a ``SLEEP`` function.
    """
    db_conn = sqlite3.connect(":memory:")
    db_conn.create_function("sleep", 1, time.sleep)

    return db_conn


def end_to_end_directory_teardown(path: Path) -> None:
    """
    Drop the temporary directory.
    """
    shutil.rmtree(path, ignore_errors=True)


def end_to_end_directory_setup(path: Path) -> None:
    """
    Create a directory with two files in it.
    """
    path.mkdir()
    (path / "query-1.sql").write_text("SELECT SLEEP(0.1)")
    (path / "query-2.sql").write_text("SELECT SLEEP(0.2)")


def main() -> None:
    """
    Entry point into the query profiling.

    https://stackoverflow.com/questions/72712965/does-the-src-folder-in-pypi-packaging-have-a-special-meaning-or-is-it-only-a-co
    """
    db_conn = create_database_connection()
    directory = Path("tests/end-to-end/queries").absolute()
    end_to_end_directory_teardown(path=directory)
    end_to_end_directory_setup(path=directory)
    query_timer.time_queries(directory=directory, repeat=5, conn=db_conn)
    end_to_end_directory_teardown(path=directory)


if __name__ == "__main__":
    main()
