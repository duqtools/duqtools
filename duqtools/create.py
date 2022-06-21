import logging
import shutil
import stat
from pathlib import Path
from typing import List

import yaml
from pydantic import DirectoryPath

from duqtools.config import IDSOperation, WorkDirectory, cfg

from ._types import BaseModel
from .ids import IDSMapping, ImasLocation
from .jetto import JettoSettings

logger = logging.getLogger(__name__)


class Run(BaseModel):
    dirname: DirectoryPath
    data: ImasLocation
    operations: List[IDSOperation]


class Runs(BaseModel):
    __root__: List[Run] = []


def copy_files(source_drc: Path, target_drc: Path):
    """Copy files for jetto run to destination directory.

    Parameters
    ----------
    source_drc : Path
        Source (template) directory.
    target_drc : Path
        Target directory.
    """
    for filename in (
            # '.llcmd',
            'jetto.in',
            'rjettov',
            'utils_jetto',
            'jetto.ex',
            'jetto.sin',
            'jetto.sgrid',
            # 'jetto.jset',
    ):
        src = source_drc / filename
        dst = target_drc / filename
        shutil.copyfile(src, dst)

    for filename in ('rjettov', 'utils_jetto'):
        path = target_drc / filename
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    logger.debug('copied files to %s' % target_drc)


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


def create(**kwargs):
    """Create input for jetto and IDS data structures.

    Parameters
    ----------
    **kwargs
        Unused.
    """
    options = cfg.create

    if cfg.workspace.runs_yaml.exists():
        raise IOError(
            'Directory is not empty, use `duqtools clean` to clear or '
            '`--force` to override.')

    template_drc = options.template
    matrix = options.matrix
    sampler = options.sampler

    jset = JettoSettings.from_directory(template_drc)

    source = ImasLocation.from_jset_input(jset)
    assert source.path().exists()

    variables = tuple(var.expand() for var in matrix)
    combinations = sampler(*variables)

    locations = (ImasLocation(db=options.data.db,
                              shot=source.shot,
                              run=options.data.run_in_start_at + i)
                 for i in range(len(combinations)))

    any_exists = False
    for location in locations:
        if location.exists():
            logger.info('Target %s already exists', location)
            any_exists = True
    if any_exists:
        raise IOError(
            'Found existing target location(s), use `duqtools clean` to '
            'remove or `--force` to override.')

    runs = []

    for i, combination in enumerate(combinations):
        run_name = f'run_{i:04d}'
        run_drc = cfg.workspace.cwd / run_name
        run_drc.mkdir(parents=True, exist_ok=True)

        target_in = ImasLocation(db=options.data.db,
                                 shot=source.shot,
                                 run=options.data.run_in_start_at + i)
        target_out = ImasLocation(db=options.data.db,
                                  shot=source.shot,
                                  run=options.data.run_out_start_at + i)

        jset_copy = jset.set_imas_locations(inp=target_in, out=target_out)
        jset_copy.to_directory(run_drc)

        source.copy_ids_entry_to(target_in)

        core_profiles = target_in.get('core_profiles')
        ids_mapping = IDSMapping(core_profiles)

        for operation in combination:
            operation.apply(ids_mapping)

        with target_in.open() as data_entry_target:
            logger.info('Writing data entry: %s' % target_in)
            core_profiles.put(db_entry=data_entry_target)

        copy_files(template_drc, run_drc)
        write_batchfile(cfg.workspace, run_name)

        runs.append({
            'dirname': run_name,
            'data': target_in.dict(),
            'operations': [op.dict() for op in combination]
        })

    runs = Runs.parse_obj(runs)

    with open(cfg.workspace.runs_yaml, 'w') as f:
        yaml.dump(yaml.safe_load(runs.json()), stream=f)
