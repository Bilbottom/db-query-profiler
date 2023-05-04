import sqlite3
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def db_connection():
    yield sqlite3.connect(":memory:")


@pytest.fixture(scope="session")
def setup():
    """
    Create a directory with two files in it, and a subdirectory with one
    file in it.
    """
    directory = Path("tests/dummy-directory").absolute()
    subdirectory = directory / "sub-directory"

    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir()
    subdirectory.mkdir()

    (directory / "query-1.sql").touch()
    (directory / "query-2.sql").touch()
    (subdirectory / "query-3.sql").touch()

    yield directory

    shutil.rmtree(directory)
