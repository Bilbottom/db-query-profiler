import contextlib
from pathlib import Path

import pytest

import query_timer


@pytest.mark.parametrize(
    "numerator, denominator, expected",
    [
        (1.0, 2.0, 0.5),
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    ],
)
def test__safe_divide(numerator: float, denominator: float, expected: float):
    assert query_timer._safe_divide(numerator, denominator) == expected


def test__get_query_filepaths(directory):
    expected = [
        directory / "query-1.sql",
        directory / "query-2.sql",
    ]
    actual = list(query_timer._get_query_filepaths(directory))

    assert actual == expected


def test__get_query_filepaths__with_warning(directory):
    file_path = Path(directory / "temp.py")
    file_path.touch()

    with pytest.warns(UserWarning):
        list(query_timer._get_query_filepaths(directory))

    file_path.unlink()


# def test__create_query_runners(db_connection, directory):
#     expected = [
#         query_timer.Runner(
#             name="query-1.sql",
#             runner=lambda: db_connection.execute(""),
#         ),
#         query_timer.Runner(
#             name="query-2.sql",
#             runner=lambda: db_connection.execute(""),
#         ),
#     ]
#     actual = query_timer._create_query_runners(
#         directory=directory, db_conn=db_connection
#     )
#
#     # The underlying functions have different memory addresses, so we can't
#     # rely on the `__repr__` that is implicitly called.
#     assert [str(runner) for runner in actual] == [str(runner) for runner in expected]
