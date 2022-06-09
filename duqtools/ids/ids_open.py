import logging

import imas
from imas import imasdef

from .ids_location import ImasLocation

logger = logging.getLogger(__name__)


def open_and_get_core_profiles(location: ImasLocation):
    data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND,
                              location.db,
                              location.shot,
                              location.run,
                              user_name=location.user)

    op = data_entry.open()

    if op[0] < 0:
        cp = data_entry.create()
        if cp[0] == 0:
            logger.info('data entry created')
    elif op[0] == 0:
        logger.info('data entry opened')

    core_profiles = data_entry.get('core_profiles')
    data_entry.close()

    return (core_profiles)
