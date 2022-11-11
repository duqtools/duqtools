"""Function to create llcmd file."""
from __future__ import annotations

import stat
from pathlib import Path

import jetto_tools

from ..models import Locations


def write_batchfile(run_dir: Path, jset: jetto_tools.jset.JSET):
    """Write batchfile (`.llcmd`) to start jetto.

    Parameters
    ----------
    target_drc : Path
        Directory to place batch file into.
    """
    llcmd_path = run_dir / '.llcmd'

    rjettov_path = run_dir / 'rjettov'
    rel_path = run_dir.relative_to(Locations().jruns_path.resolve())

    build_name = jset['JobProcessingPanel.name']
    build_user_name = jset['JobProcessingPanel.userid']
    machine_number = jset['JobProcessingPanel.machineNumber']
    num_proc = jset['JobProcessingPanel.numProcessors']
    wall_time = jset['JobProcessingPanel.wallTime']

    with open(llcmd_path, 'w') as f:
        f.write(f"""#!/bin/sh
#SBATCH -J duqtools.jetto.{run_dir.name}
#SBATCH -i /dev/null
#SBATCH -o {run_dir / 'll.out'}
#SBATCH -e {run_dir / 'll.err'}
#SBATCH -p {machine_number}

#SBATCH -N 1
#SBATCH -n {num_proc}
#SBATCH -t {wall_time}:00:00

cd {run_dir}
{rjettov_path} -S -I -p -xmpi -x64 {rel_path} \
{build_name} {build_user_name}""")

    llcmd_path.chmod(llcmd_path.stat().st_mode | stat.S_IXUSR)
