from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..ids import ImasHandle

if TYPE_CHECKING:
    from ._jetto_settings import JettoSettings

logger = logging.getLogger(__name__)


def imas_from_jset_input(jetto_settings: JettoSettings) -> ImasHandle:
    """Get IMAS input location from jetto settings.

    Parameters
    ----------
    jetto_settings : JettoSettings
        Jetto settings.

    Returns
    -------
    destination : ImasHandle
        Returns the destination.
    """
    return ImasHandle(
        db=jetto_settings.machine_in,  # type: ignore
        user=jetto_settings.user_in,  # type: ignore
        run=jetto_settings.run_in,  # type: ignore
        shot=jetto_settings.shot_in)  # type: ignore


def imas_from_jset_output(jetto_settings: JettoSettings) -> ImasHandle:
    """Get IMAS output location from jetto settings.

    Parameters
    ----------
    jetto_settings : JettoSettings
        Jetto settings.

    Returns
    -------
    destination : ImasHandle
        Returns the destination.
    """
    return ImasHandle(
        db=jetto_settings.machine_out,  # type: ignore
        run=jetto_settings.run_out,  # type: ignore
        shot=jetto_settings.shot_out)  # type: ignore
