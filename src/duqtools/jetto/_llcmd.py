"""Function to create llcmd file."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ._jset import JettoSettings

if TYPE_CHECKING:
    from duqtools.models import WorkDirectory


def write_batchfile(workspace: WorkDirectory, run_name: str,
                    jset: JettoSettings):
    """Write batchfile (`.llcmd`) to start jetto.

    Parameters
    ----------
    target_drc : Path
        Directory to place batch file into.
    """
    settings = jset.settings
    file_details = jset.raw_mapping['File Details']
    run_drc = workspace.cwd / run_name
    llcmd_path = run_drc / '.llcmd'

    full_path = workspace.cwd / run_name
    rjettov_path = full_path / 'rjettov'
    rel_path = workspace.subdir / run_name

    with open(llcmd_path, 'w') as f:
        f.write(f"""#!/bin/sh
#SBATCH -J jetto.{run_name}
#SBATCH -i /dev/null
#SBATCH -o {full_path}/ll.out
#SBATCH -e {full_path}/ll.err
#SBATCH -p {settings['JobProcessingPanel.machineNumber']}

#SBATCH -N 1
#SBATCH -n {settings['JobProcessingPanel.numProcessors']}
#SBATCH -t {settings['JobProcessingPanel.wallTime']}:00:00

cd {full_path}
{rjettov_path} -S -I -p -xmpi -x64 {rel_path} \
{file_details['Version']} {settings['JobProcessingPanel.userid']}""")
