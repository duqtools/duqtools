import itertools
from enum import Enum
from typing import List

from pydantic import BaseModel, DirectoryPath

import duqtools.config


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

    for combination in combinations:
        for var in combination:
            print('{source}: {key}={value}'.format(**var))
        print()

        # create dir
        # write jetto.jset, jetto.in

    # breakpoint()

    # # Create all variations
    # combinations = list(itertools.product(*val))

    # for combination in combinations:
    #     params = dict(zip(keys,combination))
    #     print(params)
    #     new_cfg = cfg
    #     nicename = []
    #     for key, val in params.items():
    #         new_cfg[key[0]][key[1]] = val
    #         nicename.append(key[1] + "=" + val)

    #     # Write config
    #     cfg_dir = os.path.dirname(sys.argv[1])
    #     with open(cfg_dir + "/" + "-".join(nicename) + ".cfg", "w") as f:
    #         new_cfg.write(f)
