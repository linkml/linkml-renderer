"""Base class for renderers that render LinkML instances to a format such as HTML, Markdown, etc."""
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ClassDefinition, SlotDefinition
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_renderer.paths.context import Context
from linkml_renderer.style.style_engine import StyleEngine

LINKML_INSTANCE = Union[YAMLRoot, BaseModel, Dict[str, Any]]


@dataclass
class AttributeBlock:
    """A block of attributes"""

    name: str
    """Name of the block. This may be the name of the slot group."""

    attributes: List[SlotDefinition]
    """Ordering of attributes within a block."""

    title: Optional[str] = None
    """Display title for the block."""

    def __repr__(self):
        return f"{self.name}: {[s.name for s in self.attributes]}"


@dataclass
class Renderer(ABC):
    """
    Base class for engines that render LinkML instances to a format such as HTML, Markdown, etc.
    """

    style_engine: Optional[StyleEngine] = None
    """Configuration for mappings between schema elements and render engine elements."""

    @abstractmethod
    def render(
        self,
        element: LINKML_INSTANCE,
        schemaview: SchemaView,
        source_element_name: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Render an element and all its children.

        :param element: LinkML instance to render
        :param schemaview: SchemaView which the element conforms to
        :param source_element_name: Root element name, inferred from tree_root if not present
        :param kwargs: additional args
        :return: rendering as a string
        """
        raise NotImplementedError

    def slots(self, context: Context) -> List[SlotDefinition]:
        sv = context.schemaview
        cls = context.current_element_type
        if not isinstance(cls, ClassDefinition):
            raise TypeError(f"Expected ClassDefinition, got {cls}")
        slots = sv.class_induced_slots(cls.name)
        # TODO: move to schemaview
        for slot in slots:
            if slot.inlined_as_list:
                slot.inlined = True
            if not slot.inlined:
                if slot.range in sv.all_classes():
                    if not sv.get_identifier_slot(slot.range):
                        slot.inlined = True
        return slots

    def attribute_blocks(self, context: Context) -> List[AttributeBlock]:
        slots = self.slots(context)
        blocks = []
        groups = defaultdict(list)

        def rank(slot: SlotDefinition) -> int:
            if slot.rank is not None:
                return slot.rank
            if slot.key or slot.identifier:
                return 0
            return 9999

        slots = sorted(slots, key=lambda s: rank(s))
        for slot in slots:
            slot_group = slot.slot_group
            if slot_group is None:
                if slot.identifier or slot.key:
                    slot_group = "key"
            groups[slot_group].append(slot)
        for group, slots in groups.items():
            blocks.append(AttributeBlock(name=group, attributes=slots))
        return blocks

    def ordered_slots(self, context: Context) -> List[SlotDefinition]:
        return [s for b in self.attribute_blocks(context) for s in b.attributes]


def _empty(v: Any) -> bool:
    return v is None or v == [] or v == {}


def _dict(obj: Union[BaseModel, YAMLRoot, dict]) -> dict:
    if isinstance(obj, BaseModel):
        return obj.dict()
    elif isinstance(obj, YAMLRoot):
        return obj.__dict__
    elif isinstance(obj, dict):
        return obj
    else:
        raise ValueError(f"Cannot convert {obj} to dict")
