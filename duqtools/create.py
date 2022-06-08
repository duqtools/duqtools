import itertools
from enum import Enum
from logging import debug
from typing import List

from pydantic import BaseModel, DirectoryPath

import duqtools.config

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


def create():
    cfg = duqtools.config.Config()

    options = cfg.create

    template_drc = options.template
    matrix = options.matrix

    expanded_vars = tuple(var.expand() for var in matrix)

    combinations = itertools.product(*expanded_vars)

    jset = JettoSettings.from_directory(template_drc)

    for i, combination in enumerate(combinations):
        for var in combination:
            debug('{source}: {key}={value}'.format(**var))

        subdir = cfg.workspace / f'run_{i:04d}'
        subdir.mkdir(parents=True, exist_ok=True)

        patch = {
            d['key']: d['value']
            for d in combination if d['source'] == Sources.jetto_jset
        }
        jset_patched = jset.copy_and_patch(settings=patch)
        jset_patched.to_directory(subdir)

        ids_data = {
            d['key']: d['value']
            for d in combination if d['source'] == Sources.ids
        }

        write_ids(subdir / 'ids.yaml', ids_data)
