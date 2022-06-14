import logging

import matplotlib.pyplot as plt
import numpy as np

from duqtools.ids.ids_location import ImasLocation

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
        debug('Extracting database: %s, %s, %s, %s' %
              (entry.db, entry.shot, entry.run, entry.user))
        source = ImasLocation(db=entry.db,
                              shot=entry.shot,
                              run=entry.run,
                              user=entry.user)
        profiles.append(source.get_simple_IDS('core_profiles'))

    for i, plot in enumerate(cfg().plot.plots):
        info('Creating plot number %i' % i)
        for profile in profiles:
            y = profile.flat_fields[plot.y]
            if plot.ylabel:
                plt.ylabel(plot.ylabel)
            else:
                plt.ylabel(plot.y)

            if plot.x:
                x = profile.flat_fields[plot.x]
            else:
                x = np.linspace(0, 1, len(y))
            if plot.xlabel:
                plt.xlabel(plot.xlabel)
            else:
                plt.xlabel(plot.x)

            plt.plot(x, y)
        plt.savefig('%i_plot.png' % i)
