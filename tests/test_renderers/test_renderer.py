"""Demo version test."""
import logging
import unittest

from linkml_runtime import SchemaView

from linkml_renderer.paths.context import Context
from linkml_renderer.renderers import renderer
from linkml_renderer.renderers.html_renderer import HTMLRenderer
from tests.test_renderers import OUTPUT_DIR, PERSONINFO_DIR

logger = logging.getLogger(renderer.__name__)


class TestRenderer(unittest.TestCase):
    """Test HTMLRender object on metamodel and other example data."""

    def setUp(self) -> None:
        """Setup."""
        self.renderer = HTMLRenderer()
        logger.setLevel(logging.INFO)
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    def test_attribute_blocks(self):
        sv = SchemaView(str(PERSONINFO_DIR / "personinfo.yaml"))
        renderer = self.renderer
        context = Context(schemaview=sv)
        context.set_root("Person")
        blocks = renderer.attribute_blocks(context)
        for block in blocks:
            print(block)
        self.assertEqual(["id", "name"], [s.name for s in blocks[0].attributes])
        context.set_root("FamilialRelationship")
        slots = renderer.ordered_slots(context)
        slot_names = [s.name for s in slots]
        self.assertEqual(["type", "related_to", "started_at_time", "ended_at_time"], slot_names)
