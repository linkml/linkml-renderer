from dataclasses import dataclass, field
from typing import List, Optional, Union

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ClassDefinitionName, SlotDefinitionName

from src.linkml_renderer.style.model import Configuration, RenderElementType, RenderRule

SLOT_NAME = Union[SlotDefinitionName, str]


@dataclass
class StyleEngine:
    """
    A style engine computes which style elements should be applied to a particular element.
    """

    schemaview: SchemaView
    configuration: Configuration = field(default_factory=lambda: Configuration())

    def slot_by_curie(
        self, class_name: ClassDefinitionName, curies: List[str]
    ) -> Optional[SlotDefinitionName]:
        sv = self.schemaview
        slots = [s for s in sv.class_induced_slots(class_name) if sv.get_uri(s.name) in curies]
        if slots:
            return slots[0].name

    def title_slot(self, class_name: ClassDefinitionName) -> Optional[SlotDefinitionName]:
        return self.slot_by_curie(class_name, ["dcterms:title"])

    def description_slot(self, class_name: ClassDefinitionName) -> Optional[SlotDefinitionName]:
        return self.slot_by_curie(class_name, ["dcterms:description", "skos:definition"])

    def configure_slot(self, slot_name: SLOT_NAME, render_as: RenderElementType, **kwargs) -> None:
        self.configuration.rules.append(
            RenderRule(applies_to_slots=[slot_name], render_as=render_as, **kwargs)
        )

    def configure_slots(
        self, slot_names: List[SLOT_NAME], render_as: RenderElementType, **kwargs
    ) -> None:
        for slot_name in slot_names:
            self.configure_slot(slot_name, render_as, **kwargs)

    def slot_render_as(self, slot_name: SlotDefinitionName) -> Optional[RenderElementType]:
        for rule in self.configuration.rules:
            if slot_name in rule.applies_to_slots:
                return rule.render_as
