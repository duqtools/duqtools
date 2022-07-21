from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..ids import ImasHandle

if TYPE_CHECKING:
    from ._jset import JettoSettings

logger = logging.getLogger(__name__)


def imas_from_jset_input(jset: JettoSettings) -> ImasHandle:
    """Get IMAS input location from jetto settings.

    Parameters
    ----------
    jset : JettoSettings
        Jetto settings.

    Returns
    -------
    destination : ImasHandle
        Returns the destination.
    """
    return ImasHandle(
        db=jset.machine_in,  # type: ignore
        user=jset.user_in,  # type: ignore
        run=jset.run_in,  # type: ignore
        shot=jset.shot_in)  # type: ignore


def imas_from_jset_output(jset: JettoSettings) -> ImasHandle:
    """Get IMAS output location from jetto settings.

    Parameters
    ----------
    jset : JettoSettings
        Jetto settings.

    Returns
    -------
    destination : ImasHandle
        Returns the destination.
    """
    return ImasHandle(
        db=jset.machine_out,  # type: ignore
        run=jset.run_out,  # type: ignore
        shot=jset.shot_out)  # type: ignore
