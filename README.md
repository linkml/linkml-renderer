# linkml-renderer

Generating HTML, Markdown, Mermaid, and other rendering artefacts from LinkML data.

This applies a configurable *generic* mapping between instance data and the target output file.
This is an example of a "no code" approach to generating visual representations of data.

In general, writing custom code (e.g. in Jinja) that is specific to your schema may produce
more user-friendly results. LinkML-renderer should only be used in cases where it is harder to
commit developer resources to writing custom code.

Status: experimental

## Command Line Usage

Minimally, you must pass in a schema (LinkML YAML) and a file of instance data conforming to the schema:

`linkml-render -s my-schema.yaml my-data.yaml`

or with a specific output file:

`linkml-render -s my-schema.yaml my-data.yaml -o output.html`

The default output type is HTML.

To produce other formats:

`linkml-render -s my-schema.yaml -f markdown my-data.yaml -o output.md`

You can pass in a configuration file using `--config` (`-c).

`linkml-render -s my-schema.yaml  my-data.yaml -c my-config.yaml`

The YAML file should conform to the style datamodel Configuration object.
(note: autodocumentation for this model will be produced later, for now
consult the LinkML file).

## Python Usage

When this library matures, the python documentation will be linked from the main LinkML docs.

For now, see the docstrings directly in the source, and the test folder for examples.

See minimal sphinx docs: https://linkml.github.io/linkml-renderer

## Output types

- HTML
- Markdown
- Mermaid

Note that the mermaid can be optionally embedded inside the HTML or Markdown.

## How it works

The input object is treated as a tree, and nodes in the tree are recursively visited, producing
output in the desired format.

For HTML and markdown generation, the following default rules are applied:

- singular outer objects are translated to Description Lists
- lists of objects are translated to tables 

These rules are contextual:

- Tables are not nested inside tables

The rules are also configurable. See the style schema and test cases for details.

For example, in the person infoschema, a Container contains a list of persons and a list of organizations.
The default rendering will create two tables, with each row representing an individual or organization.

This can lead to wide tables if there are a large number of slots.

If the `persons` or `organizations` slot is mapped to `RenderType.description_list`, then instead, each item
gets its own description list, resulting in a longer narrower page.

## Limitations and Future plans

Currently there are limits to customizability, both in terms of stylesheets and in terms of how schema
elements map to output elements.

The HTML generation is currently hardwired to use Bootstrap.

It is likely that the functionality here may be subsumed into a future linkml.js library. At this time
the framework may be extended to include interactive form-based data entry.

The library has not yet been tested on a wide range of data.

