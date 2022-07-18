import logging

from .config import cfg
from .ids import get_ids_tree
from .system import get_system

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def plot(*, dry_run, **kwargs):
    """Plot subroutine to create plots from datas."""
    import matplotlib.pyplot as plt
    import numpy as np
    info('Extracting imas data')
    # Gather all results and put them in a in-memory format
    # (they should be small enough)
    profiles = []
    runs = cfg.workspace.runs

    for run in runs:
        imas_loc = get_system().get_imas_location(run)
        info('Reading %s', imas_loc)

        profile = get_ids_tree(imas_loc, 'core_profiles')
        if 'profiles_1d' not in profile:
            logger.warning('No data in entry, skipping...')
            continue

        profiles.append(profile)

    for i, plot in enumerate(cfg.plot.plots):
        info('Creating plot number %04i', i)

        fig, ax = plt.subplots()

        ax.set_title(plot.y)
        ax.set_xlabel(plot.get_xlabel())
        ax.set_ylabel(plot.get_ylabel())

        for j, profile in enumerate(profiles):
            y = profile.flat_fields[plot.y]

            if plot.x:
                x = profile.flat_fields[plot.x]
            else:
                x = np.linspace(0, 1, len(y))

            ax.plot(x, y, label=j)

        ax.legend()
        if not dry_run:
            fig.savefig(f'plot_{i:04d}.png')
