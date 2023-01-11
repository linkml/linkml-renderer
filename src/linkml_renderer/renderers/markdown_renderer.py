import logging
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, List, Tuple, Union

from linkml_runtime import SchemaView
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_renderer.paths.context import Context
from linkml_renderer.renderers.renderer import Renderer, _dict, _empty
from linkml_renderer.style.model import RenderElementType

logger = logging.getLogger(__name__)


@dataclass
class MarkdownWriter:
    s: StringIO = field(default_factory=lambda: StringIO())

    def h(self, level: int, text: str):
        self.block(f"{'#' * level} {text}")

    def h1(self, text: str):
        self.block(f"# {text}")

    def h2(self, text: str):
        self.block(f"## {text}")

    def h3(self, text: str):
        self.block(f"### {text}")

    def w(self, text: str):
        self.s.write(text)

    def line(self, text: str):
        self.s.write(f"{text}\n")

    def block(self, text: str):
        self.s.write(f"\n{text}\n\n")

    def link(self, url: str, text: str = None):
        self.s.write(f"[{text or url}]({url})")

    def table_header(self, cols):
        self.s.write("\n")
        self.table_row(cols)
        self.table_row(["---"] * len(cols))

    def table_row(self, vals):
        self.line("|".join([""] + vals + [""]))

    def __repr__(self) -> str:
        return self.s.getvalue()


@dataclass
class MarkdownContext(Context):
    markdown_writer: MarkdownWriter = field(default_factory=lambda: MarkdownWriter())

    def __repr__(self) -> str:
        return super().__repr__()


@dataclass
class MarkdownRenderer(Renderer):
    """
    A renderer that generates Markdown
    """

    def render(
        self,
        element: Union[YAMLRoot, BaseModel],
        schemaview: SchemaView,
        source_element_name: str = None,
        **kwargs,
    ) -> str:
        """
        Dump a YAMLRoot object to markdown.

        :param element:
        :param schemaview:
        :param kwargs:
        :return:
        """
        ctxt = MarkdownContext(schemaview=schemaview)
        if source_element_name:
            ctxt.set_root(source_element_name)
        self.generate(element, ctxt)
        return str(ctxt.markdown_writer)

    def generate(self, element: Union[YAMLRoot, BaseModel], context: MarkdownContext) -> None:
        """
        Generate markdown for a YAMLRoot object.

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
        if context.current.slot:
            render_as = self.style_engine.slot_render_as(context.current.slot.name)
        else:
            render_as = None
        if context.target_depth == 0:
            return self.generate_document(element, context)
        elif element is None:
            return
        elif context.in_collection:
            if isinstance(element, list):
                elements = list(enumerate(element))
            elif isinstance(element, dict):
                elements = list(element.items())
            else:
                raise TypeError(f"Unexpected type for collection: {type(element)}")
            logger.debug(f"Collection {context.current.slot.name} render_as={render_as}")
            if render_as is None:
                if context.in_object:
                    render_as = RenderElementType.table
                else:
                    render_as = RenderElementType.simple_list
            if render_as == RenderElementType.table:
                if "table" in context.target_path:
                    logger.debug(f"Will not nest table in table for {context}")
                    return
                return self.elements_to_table(elements, context)
            elif render_as == RenderElementType.simple_list:
                return self.elements_to_unordered_list(elements, context)
            elif render_as == RenderElementType.description_list:
                return self.elements_to_description_lists(elements, context)
            elif render_as == RenderElementType.TUPLE:
                return self.elements_to_tuples(elements, context)
            else:
                raise ValueError(f"Unknown render_as {render_as}")
        elif context.in_object:
            if not isinstance(element, (dict, YAMLRoot, BaseModel)):
                raise TypeError(f"Unexpected type for class: {type(element)}")
            if render_as == RenderElementType.TUPLE:
                return self.generate_tuple(element, context)
            else:
                return self.generate_object(element, context)
        elif context.in_object_reference:
            return self.generate_reference(element, context)
        else:
            # TODO: enums
            return self.generate_atom(element, context)

    def generate_document(
        self, element: Union[YAMLRoot, BaseModel], context: MarkdownContext
    ) -> None:
        """
        Generate markdown top level document for a YAMLRoot object.

        :param element:
        :param context:
        :return:
        """
        # TODO: add any frontmatter here
        title = "DEFAULT"
        if self.style_engine:
            title_slot = self.style_engine.title_slot(context.current_element_type.name)
            if title_slot:
                title = _dict(element).get(title_slot, None)
                if title:
                    context.markdown_writer.h1(title)
        self.generate(element, context.extend(None, "body"))

    def generate_object(self, element: Union[YAMLRoot, dict], context: MarkdownContext) -> None:
        """
        Generate markdown for an inner YAMLRoot object.

        Not top level, so no head/body tags are generated.

        :param element:
        :param context:
        :return:
        """
        a = context.markdown_writer
        sv = context.schemaview
        element_dict = _dict(element)
        in_table = False

        for slot in self.slots(context):
            if slot.name not in element_dict:
                continue
            v = element_dict.get(slot.name, None)
            if _empty(v):
                continue
            if slot.readonly:
                continue
            # print(f"Slot {slot.name} v={v}")

            url = sv.get_uri(slot, expand=True)
            if slot.range in sv.all_classes() and slot.inlined:
                in_table = False
                a.h(context.target_depth + 1, slot.name)
                self.generate(v, context.extend(slot, "dl"))
            else:
                if not in_table:
                    a.table_header(["Slot", "Value"])
                    in_table = True
                new_context = context.extend(slot, "table")
                if new_context.in_collection:
                    if isinstance(v, list):
                        vs = list(enumerate(v))
                    elif isinstance(v, dict):
                        vs = list(v.items())
                    else:
                        raise TypeError(f"Unexpected type for collection: {type(v)}")
                    for ix, v in vs:
                        a.w("|")
                        a.w(f"{slot.name}[?]({url})")
                        a.w("|")
                        self.generate(v, new_context.index_extend(ix, v))
                        a.w("|\n")
                else:
                    a.w("|")
                    a.w(f"{slot.name}[?]({url})")
                    a.w("|")
                    self.generate(v, new_context)
                    a.w("|\n")

    def elements_to_unordered_list(
        self, indexed_elements: List[Tuple[Any, Any]], context: MarkdownContext
    ) -> None:
        """
        Generate Markdown for a list of objects.

        :param indexed_elements:
        :param context:
        :return:
        """
        logger.debug(f"Generating list of {len(indexed_elements)} elements")
        a = context.markdown_writer
        if context.target_depth < 1:
            for ix, element in indexed_elements:
                element_context = context.index_extend(ix, "li")
                a.w("\n * ")
                self.generate(element, element_context)
                a.w("\n")
        else:
            for ix, element in indexed_elements:
                element_context = context.index_extend(ix)
                a.w(" ")
                self.generate(element, element_context)

    def elements_to_description_lists(
        self, indexed_elements: List[Tuple[Any, YAMLRoot]], context: MarkdownContext
    ) -> None:
        a = context.markdown_writer
        if len(indexed_elements) == 0:
            return
        for ix, element in indexed_elements:
            a.h3(ix)
            self.generate_object(element, context.index_extend(ix, "h"))

    def elements_to_table(
        self, indexed_elements: List[Tuple[Any, YAMLRoot]], context: MarkdownContext
    ) -> None:
        """
        Generate markdown table for a list of objects.

        :param elements:
        :param context:
        :return:
        """
        if len(indexed_elements) == 0:
            return
        logger.debug(f"Generating table for {indexed_elements}")
        a = context.markdown_writer
        populated_slots = set()
        all_slots = list(self.slots(context))
        slots_to_check = list(all_slots)
        for _, element in indexed_elements:
            for slot in slots_to_check:
                if not _empty(_dict(element).get(slot.name, None)):
                    populated_slots.add(slot.name)
            slots_to_check = [slot for slot in slots_to_check if slot.name not in populated_slots]
        slots = [slot for slot in all_slots if slot.name in populated_slots]
        a.table_header([slot.name for slot in slots])
        for _, element in indexed_elements:
            element_dict = _dict(element)
            a.w("|")
            for slot in slots:
                self.generate(element_dict.get(slot.name, None), context.extend(slot, "table"))
                a.w("|")
            a.w("\n")

    def elements_to_tuples(
        self, indexed_elements: List[Tuple[Any, YAMLRoot]], context: MarkdownContext
    ) -> None:
        """
        Generate simple tuples for a list of objects.

        When writing tuples, the attributes/keys are omitted, as the position of the value is
        intended to be sufficient to identify it.

        :param elements:
        :param context:
        :return:
        """
        if len(indexed_elements) == 0:
            return
        logger.debug(f"Generating tuples for {indexed_elements}")
        a = context.markdown_writer
        n = 0
        for _, element in indexed_elements:
            if n:
                a.w(", ")
            n += 1
            self.generate_tuple(element, context)

    def generate_tuple(self, element: Any, context: MarkdownContext) -> None:
        element_dict = _dict(element)
        a = context.markdown_writer
        slots = list(self.slots(context))
        for slot in slots:
            v = element_dict.get(slot.name, None)
            if not _empty(v):
                self.generate(v, context.extend(slot, "span"))
                a.w(" ")

    def generate_reference(self, element: str, context: MarkdownContext) -> None:
        """
        Generate Markdown for a reference.

        :param element:
        :param context:
        :return:
        """
        a = context.markdown_writer
        a.link(element, element)

    def generate_atom(self, element: Any, context: MarkdownContext) -> None:
        """
        Generate HTML for an atom.

        :param element:
        :param context:
        :return:
        """
        a = context.markdown_writer
        sv = context.schemaview
        url = None
        et = context.current.element_type
        if et in sv.all_types():
            all_elt_types = sv.type_ancestors(et)
            if "uri" in all_elt_types:
                url = element
            if "uriorcurie" in all_elt_types:
                url = context.schemaview.expand_curie(element)
            if url:
                a.link(url, element)
            else:
                a.w(str(element))
        elif et in sv.all_enums():
            a.w(str(element))
        else:
            raise ValueError(f"ELEMENT {element}")
