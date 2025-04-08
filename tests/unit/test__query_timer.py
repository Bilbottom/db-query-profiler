"""
Unit tests for the ``db_query_profiler.query_timer`` module.
"""

import contextlib
import io
import re
import sqlite3
from pathlib import Path

import pytest

from db_query_profiler import query_timer


@pytest.fixture
def runner_1():
    return query_timer.Runner(
        runner=lambda: None,
        name="query-1.sql",
    )


@pytest.fixture
def runner_2():
    return query_timer.Runner(
        runner=lambda: None,
        name="query-2.sql",
    )


def test__runner__repr(runner_1: query_timer.Runner):
    """
    Test the Runner's ``__repr__`` method.

    This should test that Runner's ``__repr__`` creates an identical object,
    but passing in a lambda/partial is making this fiddly. Instead, this
    just tests the returned ``__repr__`` pattern.
    """
    expected = re.compile(
        r"Runner\(runner=<function runner_1\.<locals>\.<lambda> at 0x[a-zA-Z0-9]+>, name='query-1\.sql'\)"
    )
    actual = repr(runner_1)

    assert expected.match(actual)


def test__runner__str(runner_1: query_timer.Runner):
    """
    Test the Runner's ``__str__`` method.
    """
    expected = "Runner(runner=[[OrderedDict()], <class 'inspect._empty'>], name=query-1.sql)"

    assert str(runner_1) == expected


def test__runner__call_without_timeit(runner_1: query_timer.Runner):
    """
    Test that calling a Runner without ``time_it`` doesn't change the
    property values.
    """
    runner_1(time_it=False)

    assert runner_1.repeat == 0
    assert runner_1.total_time == 0


def test__runner__call_with_timeit(runner_1: query_timer.Runner):
    """
    Test that calling a Runner with ``time_it`` changes the property values.
    """
    runner_1(time_it=True)

    assert runner_1.repeat == 1
    assert runner_1.total_time > 0


def test__runner__average_time(runner_1: query_timer.Runner):
    """
    Test the Runner's ``average_time`` computation.
    """
    for _ in range(3):
        runner_1(time_it=True)

    assert runner_1.repeat == 3
    assert runner_1.average_time == (runner_1.total_time / runner_1.repeat)


@pytest.mark.parametrize(
    "numerator, denominator, expected",
    [
        (1.0, 2.0, 0.5),
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    ],
)
def test__safe_divide(numerator: float, denominator: float, expected: float):
    """
    Test the ``_safe_divide`` function.
    """
    assert query_timer._safe_divide(numerator, denominator) == expected


def test__get_query_filepaths(directory: Path):
    """
    Test the ``_get_query_filepaths`` function.
    """
    expected = [
        directory / "query-1.sql",
        directory / "query-2.sql",
    ]
    actual = list(query_timer._get_query_filepaths(directory))

    assert sorted(actual) == sorted(expected)


def test__get_query_filepaths__with_warning(directory: Path):
    """
    Test the ``_get_query_filepaths`` function.
    """
    file_path = Path(directory / "temp.py")
    file_path.touch()

    with pytest.warns(UserWarning):
        list(query_timer._get_query_filepaths(directory))

    file_path.unlink()


def test__create_query_runners(
    db_connection: sqlite3.Connection, directory: Path
):
    """
    Test the ``_create_query_runners`` function.
    """
    actual = query_timer._create_query_runners(
        directory=directory,
        db_conn=db_connection,
    )
    expected = [
        f"""Runner(runner=[[OrderedDict([('f', <Parameter "f={repr(directory / "query-1.sql")}">)])], <class 'inspect._empty'>], name=query-1.sql)""",  # noqa
        f"""Runner(runner=[[OrderedDict([('f', <Parameter "f={repr(directory / "query-2.sql")}">)])], <class 'inspect._empty'>], name=query-2.sql)""",  # noqa
    ]

    # fmt: off
    assert ([
        str(runner) for runner in actual].sort()
        == [str(runner) for runner in expected].sort()
    )
    # fmt: on


def test__run_runners(
    runner_1: query_timer.Runner, runner_2: query_timer.Runner
):
    """
    Test the ``_run_runners`` function.
    """
    query_timer._run_runners(
        runners=[runner_1, runner_2],
        repeat=3,
    )

    assert runner_1.repeat == 3
    assert runner_2.repeat == 3
    assert runner_1.total_time > 0
    assert runner_2.total_time > 0


def test__print_runner_stats(directory: Path):
    """
    Test the ``_print_runner_stats`` function.
    """
    expected = [
        "query-1.sql: 0.00000000s (0.0%)",
        "query-2.sql: 0.00000000s (0.0%)",
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


@pytest.mark.skip("Need to figure out how to unit test a decorator.")
def test__print_times():
    """
    Test the ``_print_times`` function.
    """
    pass


def test__time_queries__with_error(db_connection: sqlite3.Connection):
    """
    Test that the ``time_queries`` function raises an error when the
    directory doesn't exist.
    """
    with pytest.raises(FileNotFoundError):
        query_timer.time_queries(
            conn=db_connection,
            repeat=1,
            directory="some-dir-that-does-not-exist",
        )
