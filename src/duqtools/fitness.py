import csv
import subprocess as sp
from contextlib import contextmanager
from pathlib import Path
from sys import stdout

from .models import Locations
from .utils import work_directory


@contextmanager
def file_or_stdout(output):
    if output:
        f = open(output, 'w')
        try:
            yield f
        finally:
            f.close()
    else:
        yield stdout


def fitness(script: str, output: str, **kwargs):
    runs = Locations().runs

    results = []
    for run in runs:
        script_abs = Path(script).resolve()
        with work_directory(run.dirname):
            ret = sp.run(script_abs, capture_output=True, check=True)
        results.append([run.dirname, ret.stdout.decode().rstrip('\n')])

    header = ['directory', 'fitness']
    with file_or_stdout(output) as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(results)
