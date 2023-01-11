"""Demo version test."""
import logging
import unittest

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SlotDefinitionName
from linkml_runtime.utils.introspection import package_schemaview

from linkml_renderer.renderers import html_renderer
from linkml_renderer.renderers.html_renderer import HTMLRenderer
from linkml_renderer.style.model import RenderElementType
from linkml_renderer.style.style_engine import StyleEngine
from tests.test_renderers import OUTPUT_DIR, PERSONINFO_DIR

logger = logging.getLogger(html_renderer.__name__)


class TestHTMLRenderer(unittest.TestCase):
    """Test HTMLRender object on metamodel and other example data."""

    def setUp(self) -> None:
        """Setup."""
        self.dumper = HTMLRenderer()
        # logger.setLevel(logging.INFO)
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    def test_style_engine(self):
        sv = package_schemaview("linkml_runtime.linkml_model.meta")
        se = StyleEngine(sv)
        se.configure_slot(SlotDefinitionName("classes"), RenderElementType.table)
        self.assertEqual(RenderElementType.table, se.slot_render_as(SlotDefinitionName("classes")))

    def test_render_metamodel(self):
        sv = package_schemaview("linkml_runtime.linkml_model.meta")
        se = StyleEngine(sv)
        se.configure_slots(
            ["classes", "slot_definitions", "enums", "types", "subsets"],
            RenderElementType.description_list,
        )
        self.dumper.style_engine = se
        schema = sv.schema
        html = self.dumper.render(schema, sv)
        with open(OUTPUT_DIR / "metamodel.html", "w") as f:
            f.write(html)

    def test_render_personinfo(self):
        sv = SchemaView(str(PERSONINFO_DIR / "personinfo.yaml"))
        se = StyleEngine(sv)
        se.configure_slots(
            [
                "has_employment_history",
                "has_familial_relationships",
                "has_medical_history",
                "diagnosis",
                "procedure",
            ],
            RenderElementType.TUPLE,
        )
        self.dumper.style_engine = se
        with open(str(PERSONINFO_DIR / "Container-001.yaml"), "r", encoding="UTF-8") as f:
            obj = yaml.safe_load(f)
            html = self.dumper.render(obj, sv)
            with open(OUTPUT_DIR / "person.html", "w") as f:
                f.write(html)

    def test_render_personinfo_narrow(self):
        sv = SchemaView(str(PERSONINFO_DIR / "personinfo.yaml"))
        se = StyleEngine(sv)
        self.dumper.style_engine = se
        with open(str(PERSONINFO_DIR / "Container-001.yaml"), "r", encoding="UTF-8") as f:
            obj = yaml.safe_load(f)
            html = self.dumper.render(obj, sv)
            with open(OUTPUT_DIR / "person.narrow.html", "w") as f:
                f.write(html)
