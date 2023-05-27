"""Command line interface for linkml-html."""
import json
import logging
import os
import sys

import click
import yaml
from linkml_runtime import SchemaView

from linkml_renderer import __version__
from linkml_renderer.renderers.markdown_renderer import MarkdownRenderer

__all__ = [
    "main",
]

from linkml_renderer.renderers.html_renderer import HTMLRenderer
from linkml_renderer.renderers.mermaid_renderer import MermaidRenderer
from linkml_renderer.style.model import Configuration
from linkml_renderer.style.style_engine import StyleEngine

logger = logging.getLogger(__name__)

FORMAT_TO_RENDERER = {
    "html": HTMLRenderer,
    "markdown": MarkdownRenderer,
    "mermaid": MermaidRenderer,
}

aliases = {
    "rdf": "ttl",
    "jsonld": "json-ld",
}


def _get_format(path: str, specified_format: str = None, default=None):
    if specified_format is None:
        if path is None:
            if default is None:
                raise Exception("Must pass format option OR pass a filename with known file suffix")
            else:
                specified_format = default
        else:
            _, ext = os.path.splitext(path)
            if ext is not None:
                specified_format = ext.replace(".", "")
            else:
                raise Exception(f"Must pass format option OR use known file suffix: {path}")
    specified_format = specified_format.lower()
    if specified_format in aliases:
        specified_format = aliases[specified_format]
    return specified_format


@click.command()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
@click.option("-s", "--schema", help="LinkML Schema file")
@click.option("-c", "--config", help="Configuration file")
@click.option("-o", "--output", type=click.File("w"), default=sys.stdin, help="Output file")
@click.option(
    "-r", "--root", help="LinkML class that represents the instance at the root of the tree"
)
@click.option(
    "-f",
    "--input-format",
    type=click.Choice(["yaml", "json"]),
    help="Input format",
    default="yaml",
)
@click.option(
    "-t",
    "--output-format",
    type=click.Choice(list(FORMAT_TO_RENDERER.keys())),
    help="Output type",
    default="html",
)
@click.version_option(__version__)
@click.argument("input_data")
def main(
    verbose: int, quiet: bool, schema, root, config, output_format, input_format, input_data, output
):
    """CLI for linkml-renderer."""
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)
    input_format = _get_format(input_data, input_format)
    renderer = FORMAT_TO_RENDERER[output_format]()
    sv = SchemaView(schema)
    se = StyleEngine(sv)
    if config:
        se.configuration = Configuration(**yaml.safe_load(open(config)))
    renderer.style_engine = se
    with open(input_data, "r", encoding="utf-8") as f:
        if input_format == "yaml":
            obj = yaml.safe_load(f)
        else:
            obj = json.load(f)
        out = renderer.render(obj, sv, source_element_name=root)
        output.write(out)


if __name__ == "__main__":
    main()
