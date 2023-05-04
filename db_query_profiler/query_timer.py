"""
Query profiling.
"""
import datetime
import functools
import timeit
from pathlib import Path
from typing import Any, Callable, Generator, List, Union
from typing_extensions import Protocol

import tqdm

Filepath = Union[str, Path]


class DatabaseConnection(Protocol):
    """
    Database connector to run SQL against the database.
    """

    def execute(self, *args, **kwargs) -> Any:
        """Execute a statement."""


def get_file_contents(filepath: Filepath) -> str:
    """
    Return the contents of the file at ``filepath``.

    :param filepath: The path to the file to read.
    """
    with open(filepath, "r") as f:
        return f.read()


def get_query_filepaths(directory: Filepath) -> Generator:
    """
    Return the full file name paths of the files at ``directory``.
    """
    for path in directory.glob("*"):
        if path.is_file():
            yield path


def execute_query(query: str, db_conn: DatabaseConnection) -> None:
    """
    Run the SQL query contained inside the file at the file path.
    """
    db_conn.execute(query)


class Runner:
    """
    Callable object representing a function.

    Wrapped into an object rather than left as a function to assign
    additional properties to the functions, making them easier to monitor
    and summarise their statistics.
    """

    def __init__(self, runner: Callable, filepath: Filepath):
        self.runner = runner
        self.filepath = Path(filepath)

        self.repeat: int = 0
        self.total_time: float = 0.0

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
        return self.repeat and self.total_time / self.repeat

    @property
    def file_name(self) -> str:
        """
        The name of the file containing the code to run.
        """
        return self.filepath.name

    def format_runtime(self, total_avg_time: float) -> str:
        """
        Return a string containing the name and average time of this runner.

        This will additionally include the average time of this runner as a
        percentage of the average time of all runners for comparison.
        """
        return f"{self.file_name}: {self.average_time:.8f} ({self.average_time / total_avg_time:.1%})"


def create_query_runners(filepath: Filepath, conn: DatabaseConnection) -> List[Runner]:
    """
    Create a list of Runners each corresponding to the queries in the query
    filepath.
    """
    return [
        Runner(
            runner=functools.partial(
                execute_query,
                query=get_file_contents(file),
                db_conn=conn,
            ),
            filepath=file,
        )
        for file in get_query_filepaths(filepath)
    ]


def print_runner_stats(list_of_runners: List[Runner]) -> None:
    """
    Print the average run times of the runners.
    """
    total_avg_time = sum(runner.average_time for runner in list_of_runners)
    [print(runner.format_runtime(total_avg_time)) for runner in list_of_runners]


def print_times() -> Callable:
    """
    Print the start and end times of the wrapped function.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            print(f"Start time: {datetime.datetime.now()}")
            func(*args, **kwargs)
            print(f"End time: {datetime.datetime.now()}")

        return wrapper

    return decorator


@print_times()
def time_queries(directory: Filepath, repeat: int, conn: DatabaseConnection) -> None:
    """
    Time the SQL queries in the directory and print the results.

    :param directory: The path to the directory containing the SQL queries.
    :param repeat: The number of times to run each query.
    :param conn: The database connector. Must implement a
     ``run_query_from_file`` method.
    """
    directory = Path(directory)
    runners: List[Runner] = create_query_runners(
        filepath=directory,
        conn=conn,
    )

    # Set the 'temp' tables
    for runner in runners:
        runner(time_it=False)

    # Keep running them 'side-by-side' to account for database traffic
    for _ in tqdm.trange(repeat):
        for runner in runners:
            runner()

    print_runner_stats(list_of_runners=runners)
