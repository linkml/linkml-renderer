from dataclasses import dataclass, field
from typing import List

from airium import Airium

from linkml_renderer.paths.context import Context


@dataclass
class HTMLContext(Context):
    """A context for HTML rendering"""

    airium: Airium = None
    target_path: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return super().__repr__()
