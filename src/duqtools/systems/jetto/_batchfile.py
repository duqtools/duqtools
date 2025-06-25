"""Function to create llcmd file."""
from __future__ import annotations

import stat
from os.path import commonpath
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import jetto_tools

if TYPE_CHECKING:
    from duqtools.api import Job
    from duqtools.config import Config


def write_batchfile(
    run_dir: Path,
    jset: jetto_tools.jset.JSET,
    *,
    cfg: Config,
    jruns_path: Path,
):
    return
    """Write batchfile (`.llcmd`) to start jetto.

    Parameters
    ----------
    run_dir : Path
        Directory to place batch file into.
    jset: JSET
        Jetto settings object (from jetto-pythontools)
    cfg : Config
        Duqtools config.
    jruns_path : Path
        Path where runs can be run with slurm
    """
    tag = cfg.tag if cfg.tag else 'jetto'

    llcmd_path = run_dir / '.llcmd'

    rjettov_path = (run_dir / 'rjettov').resolve()
    rel_path = run_dir.resolve().relative_to(jruns_path.resolve())

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


def write_array_batchfile(jobs: Sequence[Job], max_jobs: int,
                          max_array_size: int):
    """Write array batchfile to start jetto runs.

    Parameters
    ----------
    jobs : Sequence[Job]
        List of jobs to run.
    max_jobs : int
        Maximum number of jobs to run at the same time.
    """
    common_dir = Path(commonpath(job.path for job in jobs))  # type: ignore
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

    # Calculate array size
    array_size = min(len(jobs), max_array_size)

    string = f"""#!/bin/sh
{options}
#SBATCH -o {out_file}
#SBATCH -e {err_file}
#SBATCH --array=0-{array_size-1}%{max_jobs}
#SBATCH -J duqtools-array

scripts=(
{scripts}
)
i=$SLURM_ARRAY_TASK_ID
while [ $i -le {len(jobs)} ]; do
    echo executing ${{scripts[$i]}}
    ${{scripts[$i]}} || true
    i=$((i+{array_size}))
done

"""

    with open('duqtools_slurm_array.sh', 'w') as f:
        f.write(string)
