"""Rendering of LinkML instances as HTML."""
import logging
from typing import Any, List, Tuple, Union

from airium import Airium
from linkml_runtime import SchemaView
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_renderer.paths.html_context import HTMLContext
from linkml_renderer.renderers.mermaid_renderer import MermaidRenderer
from linkml_renderer.renderers.renderer import Renderer, _dict, _empty
from linkml_renderer.style.model import RenderElementType
from linkml_renderer.style.style_engine import StyleEngine

BOOTSTRAP_VERSION = "5.3.0-alpha1"

PRIMITIVE = Union[str, int, float, bool]

logger = logging.getLogger(__name__)


class HTMLRenderer(Renderer):
    """
    A renderer that generates HTML
    """

    style_engine: StyleEngine = None

    def render(
        self,
        element: Union[YAMLRoot, BaseModel],
        schemaview: SchemaView,
        source_element_name: str = None,
        **kwargs,
    ) -> str:
        """
        Dump a YAMLRoot object to HTML.

        :param element:
        :param schemaview:
        :param kwargs:
        :return:
        """
        a = Airium()
        ctxt = HTMLContext(airium=a, schemaview=schemaview)
        if source_element_name:
            ctxt.set_root(source_element_name)
        self.generate(element, ctxt)
        return str(a)

    def generate(self, element: Union[YAMLRoot, BaseModel], context: HTMLContext) -> None:
        """
        Generate HTML for a YAMLRoot object.

        May be top level, in which case head/body tags are generated.

        :param element:
        :param context:
        :return:
        """
        if context.source_path is None:
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
                    context.airium("TRUNCATED")
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

    def generate_document(self, element: Union[YAMLRoot, BaseModel], context: HTMLContext) -> None:
        """
        Generate HTML top level document for a YAMLRoot object.

        :param element:
        :param context:
        :return:
        """
        a = context.airium
        title = "DEFAULT"
        if self.style_engine:
            title_slot = self.style_engine.title_slot(context.current_element_type.name)
            if title_slot:
                title = _dict(element).get(title_slot, "NO TITLE")
        a("<!DOCTYPE html>")
        with a.html(lang="en"):
            with a.head():
                a.meta(charset="utf-8")
                a.meta(name="viewport", content="width=device-width, initial-scale=1")
                a.link(
                    rel="stylesheet",
                    href=f"https://cdn.jsdelivr.net/npm/bootstrap@{BOOTSTRAP_VERSION}/dist/css/bootstrap.min.css",
                )
                a.title(_t=title)
            with a.body():
                a.script(
                    src=f"https://cdn.jsdelivr.net/npm/bootstrap@{BOOTSTRAP_VERSION}/dist/js/bootstrap.bundle.min.js"
                )
                if self.style_engine.configuration.include_diagrams:
                    with a.div():
                        a.h3("Diagram")
                        mermaid_renderer = MermaidRenderer()
                        with a.div(class_="mermaid"):
                            a(
                                mermaid_renderer.render(
                                    element,
                                    context.schemaview,
                                    source_element_name=context.current_element_type.name,
                                )
                            )
                        with a.script(src="https://unpkg.com/mermaid@8.8.0/dist/mermaid.min.js"):
                            a("mermaid.initialize({});")
                self.generate(element, context.extend(None, "body"))

    def generate_object(self, element: Union[YAMLRoot, dict], context: HTMLContext) -> None:
        """
        Generate HTML for an inner YAMLRoot object.

        Not top level, so no head/body tags are generated.

        :param element:
        :param context:
        :return:
        """
        a = context.airium
        sv = context.schemaview
        element_dict = _dict(element)
        with a.div():
            title_slot = self.style_engine.title_slot(context.current_element_type.name)
            if title_slot:
                title = _dict(element).get(title_slot, None)
                if title:
                    with a.h2():
                        a(title)
            description_slot = self.style_engine.description_slot(context.current_element_type.name)
            if description_slot:
                description = _dict(element).get(description_slot, None)
                if description:
                    with a.div():
                        a(description)
            with a.dl(class_="row"):
                for block in self.attribute_blocks(context):
                    for slot in block.attributes:
                        if slot.name not in element_dict:
                            continue
                        v = element_dict[slot.name]
                        if v is None:
                            continue
                        if slot.readonly:
                            continue
                        with a.dt(class_="col-sm-3"):
                            with a.span():
                                a(slot.name)
                                url = sv.get_uri(slot, expand=True)
                                desc = slot.description
                                args = {
                                    "data-bs-toggle": "tooltip",
                                    "title": desc,
                                }
                                with a.a(href=url, **args):
                                    with a.sup():
                                        a("?")
                        with a.dd(class_="col-sm-9"):
                            logger.debug(f" - Object[{slot.name}] type {type(v)}")
                            self.generate(v, context.extend(slot))

    def elements_to_unordered_list(
        self, indexed_elements: List[Tuple[Any, Any]], context: HTMLContext
    ) -> None:
        """
        Generate HTML for a list of objects.

        :param indexed_elements:
        :param context:
        :return:
        """
        logger.debug(f"Generating list of {len(indexed_elements)} elements")
        a = context.airium
        with a.div():
            if not context.in_object_reference and context.current_element_type.name == "string":
                for _, element in indexed_elements:
                    with a.span(class_="badge rounded-pill bg-light text-dark"):
                        a(element)
            else:
                with a.ul(class_="list-group"):
                    for ix, element in indexed_elements:
                        element_context = context.index_extend(ix)
                        with a.li(class_="list-group-item"):
                            self.generate(element, element_context)

    def elements_to_table(
        self, indexed_elements: List[Tuple[Any, YAMLRoot]], context: HTMLContext
    ) -> None:
        """
        Generate HTML table for a list of objects.

        :param elements:
        :param context:
        :return:
        """
        if len(indexed_elements) == 0:
            return
        logger.debug(f"Generating table for {indexed_elements}")
        a = context.airium
        populated_slots = set()
        all_slots = list(self.slots(context))
        slots_to_check = list(all_slots)
        for _, element in indexed_elements:
            for slot in slots_to_check:
                if not _empty(_dict(element).get(slot.name, None)):
                    populated_slots.add(slot.name)
            slots_to_check = [slot for slot in slots_to_check if slot.name not in populated_slots]
        slots = []
        for block in self.attribute_blocks(context):
            for slot in block.attributes:
                if slot.name in populated_slots:
                    slots.append(slot)
        with a.div():
            with a.table(class_="table table-striped"):
                with a.tr():
                    for slot in slots:
                        with a.th():
                            a(slot.alias)
                for _, element in indexed_elements:
                    element_dict = _dict(element)
                    with a.tr():
                        for slot in slots:
                            v = element_dict.get(slot.name, None)
                            with a.td():
                                self.generate(v, context.extend(slot, "table"))

    def elements_to_description_lists(
        self, indexed_elements: List[Tuple[Any, YAMLRoot]], context: HTMLContext
    ) -> None:
        """
        Generate description lists for a list of objects.

        :param elements:
        :param context:
        :return:
        """
        if len(indexed_elements) == 0:
            return
        logger.debug(f"Generating DLs for {indexed_elements}")
        a = context.airium
        slots = list(self.slots(context))
        with a.div():
            with a.div():
                anchor_id = self.anchor_id(context, "TOC")
                a.a(id=anchor_id)
                for ix, _ in indexed_elements:
                    with a.a(
                        class_="btn btn-outline-primary", href=f"#{self.anchor_id(context, ix)}"
                    ):
                        a(ix)
                    a(" ")
            for ix, element in indexed_elements:
                anchor_id = self.anchor_id(context, ix)
                a.a(id=anchor_id)
                element_dict = _dict(element)
                with a.h3():
                    a(ix)
                with a.dl(class_="row"):
                    for slot in slots:
                        v = element_dict.get(slot.name, None)
                        if not _empty(v):
                            with a.dt(class_="col-sm-3"):
                                a(slot.alias)
                            with a.dd(class_="col-sm-9"):
                                self.generate(v, context.extend(slot, "dl"))

    def elements_to_tuples(
        self, indexed_elements: List[Tuple[Any, YAMLRoot]], context: HTMLContext
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
        a = context.airium
        with a.div():
            for _, element in indexed_elements:
                self.generate_tuple(element, context)

    def generate_tuple(self, element: Any, context: HTMLContext) -> None:
        element_dict = _dict(element)
        a = context.airium
        slots = list(self.ordered_slots(context))
        with a.span():
            for slot in slots:
                v = element_dict.get(slot.name, None)
                if not _empty(v):
                    self.generate(v, context.extend(slot, "span"))

    def generate_atom(self, element: PRIMITIVE, context: HTMLContext) -> None:
        """
        Generate HTML for an atom.

        :param element:
        :param context:
        :return:
        """
        a = context.airium
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
                with a.a(href=url):
                    a(element)
            else:
                a(str(element))
        elif et in sv.all_enums():
            a(str(element))
        else:
            raise ValueError(f"ELEMENT {element}")

    def generate_reference(self, element: str, context: HTMLContext) -> None:
        """
        Generate HTML for a reference.

        :param element:
        :param context:
        :return:
        """
        a = context.airium
        with a.a(href=element):
            a(element)

    def anchor_id(self, context: HTMLContext, index: str) -> str:
        return f"{context.current_element_type.name}__{index}"
