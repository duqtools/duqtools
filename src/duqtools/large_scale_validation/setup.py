from __future__ import annotations

from ..setup import substitute_templates
from ..utils import read_imas_handles_from_file


def setup(*, template_file, input_file, force: bool, output: str, **kwargs):
    """Setup large scale validation runs for template."""
    if not input_file:
        raise OSError('Input file not defined.')

    handles = read_imas_handles_from_file(input_file)

    substitute_templates(
        handles=handles,
        template_file=template_file,
        force=force,
        output=output,
    )
