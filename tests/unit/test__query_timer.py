import contextlib
import io
from pathlib import Path

import pytest  # noqa

import db_query_profiler.query_timer as query_timer


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


def test__print_runner_stats(directory):
    expected = [
        "query-1.sql: 0.00000000 (0.0%)",
        "query-2.sql: 0.00000000 (0.0%)",
    ]

    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        query_timer._print_runner_stats(
            runners=[
                query_timer.Runner(
                    name="query-1.sql",
                    runner=lambda: None,
                ),
                query_timer.Runner(
                    name="query-2.sql",
                    runner=lambda: None,
                ),
            ],
        )
    actual = stdout.getvalue().splitlines()

    assert actual == expected


def test__time_queries__with_error(db_connection):
    with pytest.raises(FileNotFoundError):
        query_timer.time_queries(
            conn=db_connection,
            repeat=1,
            directory="some-dir-that-does-not-exist",
        )
