"""Function to create llcmd file."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from duqtools.models import WorkDirectory


def write_batchfile(workspace: WorkDirectory, run_name: str):
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

    with open(llcmd_path, 'w') as f:
        f.write(f"""#!/bin/sh
#SBATCH -J jetto.{run_name}
#SBATCH -i /dev/null
#SBATCH -o ll.out
#SBATCH -e ll.err
#SBATCH -p gw

#SBATCH -N 1
#SBATCH -n 2
#SBATCH -t 24:00:00

cd {full_path}
{rjettov_path} -S -I -p -xmpi -x64 {rel_path} v210921_gateway_imas g2fkoech
""")
