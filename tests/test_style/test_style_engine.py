"""Demo version test."""
import logging
import unittest

from linkml_runtime.linkml_model import SlotDefinitionName
from linkml_runtime.utils.introspection import package_schemaview

from linkml_renderer.style import style_engine
from linkml_renderer.style.model import RenderElementType
from linkml_renderer.style.style_engine import StyleEngine

logger = logging.getLogger(style_engine.__name__)


class TestStyleEngine(unittest.TestCase):
    """Test style engine."""

    def test_style_engine(self):
        sv = package_schemaview("linkml_runtime.linkml_model.meta")
        se = StyleEngine(sv)
        se.configure_slot(SlotDefinitionName("classes"), RenderElementType.table)
        self.assertEqual(RenderElementType.table, se.slot_render_as(SlotDefinitionName("classes")))
