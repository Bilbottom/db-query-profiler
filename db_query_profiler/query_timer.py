"""
A module for timing SQL queries.
"""

import datetime
import functools
import inspect
import pathlib
import timeit
import warnings
from collections.abc import Generator
from typing import Any, Callable, List, Protocol, Union

import tqdm


class DatabaseConnection(Protocol):
    """
    Database connector to run SQL against the database.
    """

    def execute(self) -> Any:
        """
        Execute a statement.
        """


def _safe_divide(numerator: float, denominator: float) -> float:
    """
    Return the result of dividing ``numerator`` by ``denominator`` if
    ``denominator`` is not 0, else return 0.

    Source:

    - https://stackoverflow.com/a/68118106/8213085
    """
    return denominator and numerator / denominator


class Runner:
    """
    Callable object representing a function.

    Wrapped into an object rather than left as a function to assign
    additional properties to the functions, making them easier to monitor
    and summarise their statistics.
    """

    def __init__(self, runner: Callable, name: str):
        self.runner = runner
        self.name = name

        self.repeat: int = 0
        self.total_time: float = 0.0

    def __repr__(self):
        return f"Runner(runner={self.runner}, name='{self.name}')"

    def __str__(self):
        sig = inspect.signature(self.runner)

        return f"Runner(runner=[[{sig.parameters}], {sig.return_annotation}], name={self.name})"

    def __call__(self, time_it: bool = True):
        if time_it:
            self.repeat += 1
            self.total_time += timeit.timeit(self.runner, number=1)
        else:
            self.runner()

    @property
    def average_time(self) -> float:
        """
        The average time, in seconds, that this function has taken to run.

        If the function has not been run, returns 0.
        """
        return _safe_divide(self.total_time, self.repeat)

    def format_runtime(self, total_avg_time: float) -> str:
        """
        Return a string containing the name and average time, in seconds, of
        this runner.

        This will additionally include the average time of this runner as a
        percentage of the average time of all runners for comparison.
        """
        return f"{self.name}: {self.average_time:.8f}s ({_safe_divide(self.average_time, total_avg_time):.1%})"


def _get_query_filepaths(directory: pathlib.Path) -> Generator:
    """
    Return the full file name paths of the files at ``directory``.
    """
    for path in directory.glob("*"):
        if path.is_file():
            if path.suffix != ".sql":
                warnings.warn(
                    f"File {path} does not end with '.sql'. Non-SQL code might attempt to be executed."
                )

            yield path


def _create_query_runners(
    directory: pathlib.Path,
    db_conn: DatabaseConnection,
) -> List[Runner]:
    """
    Return a list of ``Runners`` each corresponding to the files in the
    ``filepath``.
    """
    # Closures in Python capture _variables_, not _values_, so the `file`
    # variable by itself would be the last file in the directory for each
    # lambda. This is why we need to use the variable `f` to 'freeze' the
    # value of the `file` variable.
    #
    # https://docs.python.org/3/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result
    return [
        Runner(
            runner=lambda f=file: db_conn.execute(f.read_text()),
            name=file.name,
        )
        for file in _get_query_filepaths(directory)
    ]


def _run_runners(runners: List[Runner], repeat: int) -> None:
    """
    Run the ``runners`` ``repeat`` times.

    This will always run the runners once before the repeat loop to set up
    the temp tables in the database (there's no way to avoid these implicit
    tables).
    """
    # Set the 'temp' tables
    for runner in runners:
        runner(time_it=False)

    # Keep running them 'side-by-side' to account for database traffic
    for _ in tqdm.trange(repeat):
        for runner in runners:
            runner()


def _print_runner_stats(runners: List[Runner]) -> None:
    """
    Print the average run times of the ``runners``.

    :param runners: The list of ``Runner``s to run.
    """
    total_avg_time = sum(runner.average_time for runner in runners)
    for runner in runners:
        print(runner.format_runtime(total_avg_time))


def _print_times() -> Callable:
    """
    Print the start and end times of the wrapped function.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            print(f"Start time: {datetime.datetime.now()}")
            print(40 * "-")
            func(*args, **kwargs)
            print(40 * "-")
            print(f"End time: {datetime.datetime.now()}")

        return wrapper

    return decorator


@_print_times()
def time_queries(
    # This API is likely to change in the future, so requiring kwargs makes
    # changes to the API less likely to break downstream usage in the future
    *,
    conn: DatabaseConnection,
    repeat: int,
    directory: Union[str, pathlib.Path],
) -> None:
    """
    Time the SQL queries in the directory and print the results.

    .. warning::
        This function's signature is likely to change in a later release, so
        to avoid breaking downstream usage, this function currently requires
        the use of keyword arguments::

            from db_query_profiler import time_queries

            time_queries(
                conn=your_database_connection,
                repeat=10,
                directory="path/to/your/sql/files",
            )

    :param conn: The database connector. Must implement an ``execute``
        method.
    :param repeat: The number of times to run each query. Note that the
        queries will all be run once before the repeat loop to set up the
        temp tables in the database (there's no way to avoid these implicit
        tables).
    :param directory: The path to the directory containing the SQL queries.
    """
    directory = pathlib.Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist.")

    runners: List[Runner] = _create_query_runners(
        directory=directory,
        db_conn=conn,
    )

    _run_runners(runners=runners, repeat=repeat)
    _print_runner_stats(runners=runners)
