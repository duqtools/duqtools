import itertools
import shutil
from enum import Enum
from logging import debug
from pathlib import Path
from typing import List

from pydantic import BaseModel, DirectoryPath

from duqtools.config import Config as cfg

from .ids import write_ids
from .jetto import JettoSettings


class Sources(Enum):
    jetto_in = 'jetto.in'
    jetto_jset = 'jetto.jset'
    ids = 'ids'


class Variable(BaseModel):
    source: Sources
    key: str
    values: list

    def expand(self):
        return tuple({
            'source': self.source,
            'key': self.key,
            'value': value
        } for value in self.values)


class ConfigCreate(BaseModel):
    matrix: List[Variable] = []
    template: DirectoryPath


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
    debug('copied files to %s' % target_drc)


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

    options = cfg().create

    template_drc = options.template
    matrix = options.matrix

    expanded_vars = tuple(var.expand() for var in matrix)

    combinations = itertools.product(*expanded_vars)

    jset = JettoSettings.from_directory(template_drc)

    for i, combination in enumerate(combinations):
        for var in combination:
            debug('{source}: {key}={value}'.format(**var))

        sub_drc = f'run_{i:04d}'
        target_drc = cfg().workspace / sub_drc
        target_drc.mkdir(parents=True, exist_ok=True)

        patch = {
            d['key']: d['value']
            for d in combination if d['source'] == Sources.jetto_jset
        }
        jset_patched = jset.copy_and_patch(settings=patch)
        jset_patched.to_directory(target_drc)

        ids_data = {
            d['key']: d['value']
            for d in combination if d['source'] == Sources.ids
        }

        write_ids(target_drc / 'ids.yaml', ids_data)

        copy_files(template_drc, target_drc)

        write_batchfile(target_drc)
