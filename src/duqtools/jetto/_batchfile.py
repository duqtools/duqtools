"""Function to create llcmd file."""
from __future__ import annotations

import stat
from os.path import commonpath
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import jetto_tools

from ..models import Locations

if TYPE_CHECKING:
    from ..models import Job


def write_batchfile(run_dir: Path,
                    jset: jetto_tools.jset.JSET,
                    tag: str | None = None):
    """Write batchfile (`.llcmd`) to start jetto.

    Parameters
    ----------
    run_dir : Path
        Directory to place batch file into.
    jset: JSET
        Jetto settings object (from jetto-pythontools)
    tag : str | None
        Tag the job, defaults to 'jetto'.
    """
    if not tag:
        tag = 'jetto'

    llcmd_path = run_dir / '.llcmd'

    rjettov_path = run_dir / 'rjettov'
    rel_path = run_dir.resolve().relative_to(Locations().jruns_path.resolve())

    build_name = jset['JobProcessingPanel.name']
    build_user_name = jset['JobProcessingPanel.userid']
    machine_number = jset['JobProcessingPanel.machineNumber']
    num_proc = jset['JobProcessingPanel.numProcessors']
    wall_time = jset['JobProcessingPanel.wallTime']

    string = f"""#!/bin/sh
#SBATCH -J duqtools.{tag}.{run_dir.name}
#SBATCH -i /dev/null
#SBATCH -o {run_dir / 'll.out'}
#SBATCH -e {run_dir / 'll.err'}
#SBATCH -p {machine_number}

#SBATCH -N 1
#SBATCH -n {num_proc}
#SBATCH -t {wall_time}:00:00

cd {run_dir}
{rjettov_path} -S -I -p -xmpi -x64 {rel_path} \
{build_name} {build_user_name}"""

    with open(llcmd_path, 'w') as f:
        f.write(string)

    llcmd_path.chmod(llcmd_path.stat().st_mode | stat.S_IXUSR)


def write_array_batchfile(jobs: Sequence[Job], max_jobs: int):
    """Write array batchfile to start jetto runs.

    Parameters
    ----------
    jobs : Sequence[Job]
        List of jobs to run.
    max_jobs : int
        Maximum number of jobs to run at the same time.
    """
    common_dir = Path(commonpath(job.dir for job in jobs))  # type: ignore
    logs_dir = common_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Get the first jobs submission script as a template
    lines = open(jobs[0].submit_script)
    sbatch_lines = (line for line in lines if line.startswith('#SBATCH'))
    option_lines = (line for line in sbatch_lines
                    if line.split()[1] not in ('-o', '-e', '-J'))
    options = ''.join(option_lines)

    # Append our own options, later options have precedence
    out_file = logs_dir / 'duqtools-%A_%a.out'
    err_file = logs_dir / 'duqtools-%A_%a.err'

    scripts = '\n'.join(f'    {job.submit_script}' for job in jobs)

    string = f"""#!/bin/sh
{options}
#SBATCH -o {out_file}
#SBATCH -e {err_file}
#SBATCH --array=0-{len(jobs)-1}%{max_jobs}
#SBATCH -J duqtools-array

scripts=(
{scripts}
)
echo executing ${{scripts[$SLURM_ARRAY_TASK_ID]}}
${{scripts[$SLURM_ARRAY_TASK_ID]}} || true
"""

    with open('duqtools_slurm_array.sh', 'w') as f:
        f.write(string)
