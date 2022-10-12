"""Function to create llcmd file."""
from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import jetto_tools

if TYPE_CHECKING:
    from duqtools.models import WorkDirectory


def write_batchfile(workspace: WorkDirectory, run_name: str,
                    jset: jetto_tools.jset.JSET):
    """Write batchfile (`.llcmd`) to start jetto.

    Parameters
    ----------
    target_drc : Path
        Directory to place batch file into.
    """
    run_drc = workspace.cwd / run_name
    llcmd_path = run_drc / '.llcmd'

    full_path = workspace.cwd / run_name
    rjettov_path = full_path / 'rjettov'
    rel_path = workspace.subdir / run_name

    build_name = jset['JobProcessingPanel.name']
    build_user_name = jset['JobProcessingPanel.userid']
    machine_number = jset['JobProcessingPanel.machineNumber']
    num_proc = jset['JobProcessingPanel.numProcessors']
    wall_time = jset['JobProcessingPanel.wallTime']

    with open(llcmd_path, 'w') as f:
        f.write(f"""#!/bin/sh
#SBATCH -J duqtools.jetto.{run_name}
#SBATCH -i /dev/null
#SBATCH -o {full_path}/ll.out
#SBATCH -e {full_path}/ll.err
#SBATCH -p {machine_number}

#SBATCH -N 1
#SBATCH -n {num_proc}
#SBATCH -t {wall_time}:00:00

cd {full_path}
{rjettov_path} -S -I -p -xmpi -x64 {rel_path} \
{build_name} {build_user_name}""")

    llcmd_path.chmod(llcmd_path.stat().st_mode | stat.S_IXUSR)
