from pathlib import Path

import query_timer


def test__get_query_filepaths(setup):
    directory = Path("tests/dummy-directory").absolute()
    expected = [
        directory / "query-1.sql",
        directory / "query-2.sql",
    ]
    actual = list(query_timer.get_query_filepaths(directory))

    assert actual == expected
