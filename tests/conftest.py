import shutil
import sqlite3
from pathlib import Path

import pytest

HERE = Path(__file__).parent


@pytest.fixture
def db_connection():
    yield sqlite3.connect(":memory:")


@pytest.fixture(scope="session")
def directory():
    """
    Create a directory with two files in it, and a subdirectory with one
    file in it.

    The subdirectory tests that the functions only look at the files in
    _their_ directory, and not the files in any subdirectory.
    """
    directory = HERE / "unit/test-directory"
    subdirectory = directory / "subdirectory"

    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir()
    subdirectory.mkdir()

    (directory / "query-1.sql").touch()
    (directory / "query-2.sql").touch()
    (subdirectory / "query-3.sql").touch()

    yield directory

    shutil.rmtree(directory)
