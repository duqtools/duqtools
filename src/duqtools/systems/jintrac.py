from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..ids import ImasHandle


class V210921Mixin:
    """Data handler Mixin for v220922."""

    def get_data_in_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data input."""
        from duqtools.ids import ImasHandle

        return ImasHandle(
            user=options.user,
            db=options.imasdb,
            shot=source.shot,
            run=options.run_in_start_at + seq_number,
        )

    def get_data_out_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data output."""
        from duqtools.ids import ImasHandle

        return ImasHandle(
            user=options.user,
            db=options.imasdb,
            shot=source.shot,
            run=options.run_out_start_at + seq_number,
        )


class V220922Mixin:
    """Data handler Mixin for v220922."""

    def get_data_in_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data input."""
        from duqtools.ids import ImasHandle

        relative_location: Optional[str] = str(
            os.path.relpath((dirname / 'imasdb').resolve()))
        if relative_location:
            if relative_location.startswith('..'):
                relative_location = None
        return ImasHandle(user=str((dirname / 'imasdb').resolve()),
                          db=source.db,
                          shot=source.shot,
                          run=1,
                          relative_location=relative_location)

    def get_data_out_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data output."""
        from duqtools.ids import ImasHandle

        relative_location: Optional[str] = str(
            os.path.relpath((dirname / 'imasdb').resolve()))
        if relative_location:
            if relative_location.startswith('..'):
                relative_location = None
        return ImasHandle(user=str((dirname / 'imasdb').resolve()),
                          db=source.db,
                          shot=source.shot,
                          run=2,
                          relative_location=relative_location)
