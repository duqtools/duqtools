from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..config.imaslocation import ImasLocation

if TYPE_CHECKING:
    from ._jset import JettoSettings

logger = logging.getLogger(__name__)


def imas_from_jset_input(jset: JettoSettings) -> ImasLocation:
    """Get IMAS input location from jetto settings.

    Parameters
    ----------
    jset : JettoSettings
        Jetto settings.

    Returns
    -------
    destination : ImasLocation
        Returns the destination.
    """
    return ImasLocation(
        db=jset.machine_in,  # type: ignore
        user=jset.user_in,  # type: ignore
        run=jset.run_in,  # type: ignore
        shot=jset.shot_in)  # type: ignore


def imas_from_jset_output(jset: JettoSettings) -> ImasLocation:
    """Get IMAS output location from jetto settings.

    Parameters
    ----------
    jset : JettoSettings
        Jetto settings.

    Returns
    -------
    destination : ImasLocation
        Returns the destination.
    """
    return ImasLocation(
        db=jset.machine_out,  # type: ignore
        run=jset.run_out,  # type: ignore
        shot=jset.shot_out)  # type: ignore
