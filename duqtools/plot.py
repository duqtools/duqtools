import logging

import matplotlib.pyplot as plt
import numpy as np

from .config import Config as cfg

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def plot(**kwargs):
    """Plot subroutine to create plots from datas.

    Parameters
    ----------
    kwargs :
        kwargs
    """

    info('Extracting imas data')
    # Gather all results and put them in a in-memory format
    # (they should be small enough)
    profiles = []
    for entry in cfg().plot.data:
        debug('Extracting database: %s' % entry)
        profiles.append(entry.get_simple_IDS('core_profiles'))

    for i, plot in enumerate(cfg().plot.plots):
        info('Creating plot number %04i' % i)
        for profile in profiles:
            y = profile.flat_fields[plot.y]

            if plot.x:
                x = profile.flat_fields[plot.x]
            else:
                x = np.linspace(0, 1, len(y))

            plt.xlabel(plot.xlabel)
            plt.ylabel(plot.ylabel)

            plt.plot(x, y)
        plt.savefig('plot_%04i.png' % i)
