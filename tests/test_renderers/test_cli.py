import os
import unittest

from click.testing import CliRunner

from linkml_renderer.cli import main
from tests.test_renderers import INPUT_DIR, OUTPUT_DIR


class CliTestSuite(unittest.TestCase):
    """
    Tests command line interfaces
    """

    def setUp(self) -> None:
        runner = CliRunner(mix_stderr=False)
        self.runner = runner
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    def test_help(self):
        result = self.runner.invoke(main, ["--help"])
        out = result.stdout
        self.assertEqual(0, result.exit_code)
        self.assertIn("linkml-renderer", out)

    def test_render(self):
        cases = [
            (
                "pp1",
                "phenopackets",
                os.path.join("schema", "phenopackets.yaml"),
                "bethleham-myopathy.json",
                ["-c", INPUT_DIR / "conf-pfx.yaml"],
            ),
            (
                "pp1",
                "phenopackets",
                os.path.join("schema", "phenopackets.yaml"),
                "covid.json",
                ["-c", INPUT_DIR / "conf-pfx.yaml"],
            ),
            ("p1", "personinfo", "personinfo.yaml", "Container-001.yaml", []),
            (
                "p1n",
                "personinfo",
                "personinfo.yaml",
                "Container-001.yaml",
                ["-c", INPUT_DIR / "conf-person-narrow.yaml"],
            ),
            (
                "p1w",
                "personinfo",
                "personinfo.yaml",
                "Container-001.yaml",
                ["-c", INPUT_DIR / "conf-person-wide.yaml"],
            ),
            (
                "p1n",
                "personinfo",
                "personinfo.yaml",
                "Container-001.yaml",
                ["-c", INPUT_DIR / "conf-person-narrow.yaml"],
            ),
        ]
        for fmt in ["html", "markdown", "mermaid"]:
            for id, local_dir, schema, data, opts in cases:
                directory = INPUT_DIR / local_dir
                schema_path = directory / schema
                data_path = directory / data
                print(f"Testing {fmt} {schema_path} {data_path}")
                outpath = OUTPUT_DIR / f"cl-{id}-{data}.{fmt}"
                result = self.runner.invoke(
                    main, ["-t", fmt, "-s", schema_path, str(data_path), "-o", str(outpath)] + opts
                )
                out = result.stdout
                print(f"OUT={out}")
                print(result.stderr)
                self.assertEqual(0, result.exit_code)
