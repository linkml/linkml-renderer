import logging
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Dict, Optional, Union

from linkml_runtime import SchemaView
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_renderer.paths.context import Context
from linkml_renderer.renderers.renderer import Renderer, _dict, _empty
from linkml_renderer.style.model import LineStyle, Shape

logger = logging.getLogger(__name__)


def _escape(v: Any):
    v = str(v)
    bad_chars = ["@", "[", "]", ">", "<", "{", "}", "|", "\\", "^", "~", "`", "*"]
    for c in bad_chars:
        v = v.replace(c, "")
    return v


SHAPE_MAP = {
    Shape.ROUNDED_SQUARE: ("(", ")"),
    Shape.SQUARE: ("[", "]"),
    Shape.DIAMOND: ("{", "}"),
    Shape.CIRCLE: ("((", "))"),
}


@dataclass
class MermaidWriter:
    s: StringIO = field(default_factory=lambda: StringIO())

    def header(self, text: str):
        self.s.write(f"{text}\n")

    def line(self, text: str):
        self.s.write(f"    {text}\n")

    def entity(
        self, id: str, text: str = None, shape: Shape = None, right_side_shape: Shape = None
    ):
        if shape is None:
            shape = Shape.ROUNDED_SQUARE
        if right_side_shape is None:
            right_side_shape = shape
        left = SHAPE_MAP.get(shape)[0]
        right = SHAPE_MAP.get(right_side_shape)[1]
        self.line(f"{id}{left}{text}{right}")

    def edge(self, id: str, rel: Optional[str], obj: str, style: LineStyle = None):
        if style == LineStyle.DASHED:
            repr = "-.-"
        elif style == LineStyle.DOUBLE:
            repr = "=="
        else:
            repr = "--"
        arrow = f"{repr} {rel} {repr}>" if rel else f"{repr}>"
        self.line(f"{id} {arrow} {obj}")

    def __str__(self):
        return self.s.getvalue()


@dataclass
class MermaidContext(Context):
    mermaid_writer: MermaidWriter = field(default_factory=lambda: MermaidWriter())

    def __repr__(self) -> str:
        return super().__repr__()


@dataclass
class MermaidRenderer(Renderer):
    """
    A renderer that generates mermaid
    """

    element_to_id: Dict[str, str] = field(default_factory=lambda: {})
    last_id: int = field(default_factory=lambda: 0)

    def render(
        self,
        element: Union[YAMLRoot, BaseModel],
        schemaview: SchemaView,
        source_element_name: str = None,
        **kwargs,
    ) -> str:
        """
        Dump a YAMLRoot object to mermaid.

        :param element:
        :param schemaview:
        :param kwargs:
        :return:
        """
        ctxt = MermaidContext(schemaview=schemaview)
        if source_element_name:
            ctxt.set_root(source_element_name)
        self.generate(element, ctxt)
        return str(ctxt.mermaid_writer)

    def generate(self, element: Union[YAMLRoot, BaseModel], context: MermaidContext) -> None:
        """
        Generate mermaid for a YAMLRoot object.

        May be top level, in which case head/body tags are generated.

        :param element:
        :param context:
        :return:
        """
        if context.source_path is None:
            # TODO: refactor
            if isinstance(element, YAMLRoot):
                root = type(element).class_name
            else:
                roots = [c.name for c in context.schemaview.all_classes().values() if c.tree_root]
                if len(roots) != 1:
                    raise ValueError(f"Cannot determine root class for {element}")
                root = roots[0]
            context.set_root(root)
        logger.info(f"Current context: {context}")
        if context.target_depth == 0:
            return self.generate_document(element, context)
        else:
            self.generate_node(element, context)

    def generate_document(
        self, element: Union[YAMLRoot, BaseModel], context: MermaidContext
    ) -> None:
        """
        Generate mermaid top level document for a YAMLRoot object.

        :param element:
        :param context:
        :return:
        """
        # TODO: add any frontmatter here
        a = context.mermaid_writer
        a.header("graph TB")
        self.generate(element, context.extend(None, "body"))

    def _id(self, element: Any, context: MermaidContext) -> str:
        sv = context.schemaview
        et = context.current_element_type.name
        id_slot = sv.get_identifier_slot(et)
        if id_slot and not context.in_collection:
            element_dict = _dict(element)
            id_val = _escape(element_dict.get(id_slot.name)).replace(" ", "_")
            return id_val
        element_str = str(element)
        if element_str not in self.element_to_id:
            self.last_id += 1
            self.element_to_id[element_str] = f"{et}_{self.last_id}"
        return f"ANON__f{self.element_to_id[element_str]}"

    def generate_node(
        self, element: Union[YAMLRoot, dict], context: MermaidContext
    ) -> Optional[str]:
        """
        Generate mermaid for an inner YAMLRoot object.

        Not top level, so no head/body tags are generated.

        :param element:
        :param context:
        :return:
        """
        if not context.in_object:
            return None
        a = context.mermaid_writer
        et = context.current_element_type.name
        id_value = self._id(element, context)
        if context.in_collection:
            a.entity(id_value, " ", Shape.DIAMOND)
            vals = element.values() if isinstance(element, dict) else element
            for val in vals:
                obj_id = self.generate_node(val, context.index_extend("item"))
                if obj_id:
                    a.edge(id_value, None, obj_id, LineStyle.DASHED)
            return id_value
        local_atts = {}
        for slot in self.slots(context):
            element_dict = _dict(element)
            if slot.name not in element_dict:
                continue
            v = element_dict.get(slot.name, None)
            if _empty(v):
                continue
            if slot.readonly:
                continue
            new_context = context.extend(slot)
            obj_id = self.generate_node(v, new_context)
            if obj_id:
                a.edge(id_value, slot.name, obj_id)
            else:
                local_atts[slot.name] = str(v)
            atts_str = "<br>".join([f"<b>{k}</b> {_escape(v)}" for k, v in local_atts.items()])
            a.entity(id_value, f"{et}<br>{atts_str}")
        return id_value
