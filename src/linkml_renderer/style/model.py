from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from linkml_runtime.linkml_model import Decimal
from pydantic import BaseModel as BaseModel
from pydantic import Field

metamodel_version = "None"
version = "None"


class WeakRefShimBaseModel(BaseModel):
    __slots__ = "__weakref__"


class ConfiguredBaseModel(
    WeakRefShimBaseModel,
    validate_assignment=True,
    validate_all=True,
    underscore_attrs_are_private=True,
    extra="forbid",
    arbitrary_types_allowed=True,
):
    pass


class RenderType(str, Enum):

    HTML = "HTML"
    MARKDOWN = "MARKDOWN"
    MERMAID = "MERMAID"


class HTMLFramework(str, Enum):

    Bootstrap = "Bootstrap"
    Tailwind = "Tailwind"


class Shape(str, Enum):

    SQUARE = "SQUARE"
    ROUNDED_SQUARE = "ROUNDED_SQUARE"
    CIRCLE = "CIRCLE"
    DIAMOND = "DIAMOND"


class LineStyle(str, Enum):

    SOLID = "SOLID"
    DASHED = "DASHED"
    DOTTED = "DOTTED"
    DOUBLE = "DOUBLE"


class RenderElementType(str, Enum):

    heading = "heading"
    h1 = "h1"
    h2 = "h2"
    h3 = "h3"
    description_list = "description_list"
    simple_list = "simple_list"
    table = "table"
    TUPLE = "TUPLE"
    NO_ELEMENT = "NO_ELEMENT"


class Configuration(ConfiguredBaseModel):
    """
    A configuration for rendering instances of a LinkML model
    """

    frameworks: Optional[List[HTMLFramework]] = Field(
        default_factory=list,
        description="""The target frameworks. Note that for HTML, currently Bootstrap is assumed.""",
    )
    rules: Optional[List[RenderRule]] = Field(
        default_factory=list, description="""List of rendering rules."""
    )
    include_diagrams: Optional[bool] = Field(
        None,
        description="""If true, include a diagram at the top of the document. Currently only mermaid supported.""",
    )


class RenderRule(ConfiguredBaseModel):
    """
    A rule for rendering a particular element
    """

    name: Optional[str] = Field(None, description="""Optional name of the rule""")
    applies_to_slots: Optional[List[str]] = Field(
        default_factory=list,
        description="""List of slots that this rule applies to. If empty, applies to all slots.""",
    )
    applies_to_curies: Optional[List[str]] = Field(
        default_factory=list,
        description="""List of curies that this rule applies to. If empty, applies to all curies.""",
    )
    applies_to_render_types: Optional[List[RenderType]] = Field(default_factory=list)
    render_as: Optional[RenderElementType] = Field(
        None, description="""The type of element to render this as"""
    )
    fstring: Optional[str] = Field(
        None,
        description="""A python fstring template that is used to render the value of the slot""",
    )
    template: Optional[str] = Field(
        None, description="""A Jinja template string that is used to render the value of the slot"""
    )


# Update forward refs
# see https://pydantic-docs.helpmanual.io/usage/postponed_annotations/
Configuration.update_forward_refs()
RenderRule.update_forward_refs()
