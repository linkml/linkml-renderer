"""Demo version test."""
import logging
import unittest

from linkml_runtime.utils.introspection import package_schemaview

from linkml_renderer.paths import context
from linkml_renderer.paths.context import Context

logger = logging.getLogger(context.__name__)


class TestContext(unittest.TestCase):
    """Test context objects."""

    def test_immutability(self):
        sv = package_schemaview("linkml_runtime.linkml_model.meta")
        context = Context(schemaview=sv)
        context.set_root("SchemaDefinition")
        self.assertEqual(".<<SchemaDefinition>>", str(context.source_path_str))
        new_context = context.extend(sv.get_slot("enums"))
        self.assertEqual(
            ".<<SchemaDefinition>>/enums<<enum_definition>>", str(new_context.source_path_str)
        )
        self.assertEqual(".<<SchemaDefinition>>", str(context.source_path_str))
        context = Context(schemaview=sv)
        self.assertEqual([], context.target_path)
        new_context = context.extend(None, "foo")
        self.assertEqual([], context.target_path)
        self.assertEqual(["foo"], new_context.target_path)
