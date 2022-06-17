import logging
import shutil
from pathlib import Path

from duqtools.config import cfg

from .ids import IDSMapping, ImasLocation
from .jetto import JettoSettings

logger = logging.getLogger(__name__)


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
    logger.debug('copied files to %s' % target_drc)


def write_batchfile(target_drc: Path):
    """Write batchfile (`.llcmd`) to start jetto.

    Parameters
    ----------
    target_drc : Path
        Directory to place batch file into.
    """
    drc_name = target_drc.name
    with open(target_drc / '.llcmd', 'w') as f:
        f.write(f"""#!/bin/sh
./rjettov -S -I -p -xmpi -x64 {drc_name} v210921_gateway_imas g2fkoech
""")


def create(**kwargs):
    """Create input for jetto and IDS data structures.

    Parameters
    ----------
    **kwargs
        Unused.
    """
    options = cfg.create

    template_drc = options.template
    matrix = options.matrix
    sampler = options.sampler

    jset = JettoSettings.from_directory(template_drc)

    source = ImasLocation.from_jset_input(jset)
    assert source.path().exists()

    variables = tuple(var.expand() for var in matrix)
    combinations = sampler(*variables)

    for i, combination in enumerate(combinations):
        sub_drc = f'run_{i:04d}'
        target_drc = cfg.workspace / sub_drc
        target_drc.mkdir(parents=True, exist_ok=True)

        copy_files(template_drc, target_drc)
        write_batchfile(target_drc)

        target_in = ImasLocation(db=options.data.db,
                                 shot=source.shot,
                                 run=options.data.run_in_start_at + i)
        target_out = ImasLocation(db=options.data.db,
                                  shot=source.shot,
                                  run=options.data.run_out_start_at + i)

        jset_copy = jset.set_imas_locations(inp=target_in, out=target_out)
        jset_copy.to_directory(target_drc)

        source.copy_ids_entry_to(target_in)

        core_profiles = target_in.get('core_profiles')
        ids_mapping = IDSMapping(core_profiles)

        for operation in combination:
            operation.apply(ids_mapping)

        with target_in.open() as data_entry_target:
            logger.info('Writing data entry: %s' % target_in)
            core_profiles.put(db_entry=data_entry_target)
