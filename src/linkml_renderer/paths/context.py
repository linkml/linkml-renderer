from copy import copy, deepcopy
from dataclasses import dataclass, field
from typing import Any, List, Optional, Union

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import (
    ClassDefinition,
    ElementName,
    EnumDefinition,
    SlotDefinition,
    TypeDefinition,
)


@dataclass
class PathComponent:
    """
    A path element.
    """

    element_type: ElementName
    """The type which the path component instantiates"""

    slot: Optional[SlotDefinition] = None
    """The slot that points to the path component"""

    index: Optional[Union[int, str]] = None
    """For multivalued slots, the index of the value"""

    @property
    def root(self) -> bool:
        """True if this is the root of the path"""
        return self.slot is None

    def __repr__(self) -> str:
        sn = self.slot.name if self.slot else "."
        ix = f"[{self.index}]" if self.index else ""
        et = self.element_type
        if self.slot and not self.slot.inlined:
            et = f"*{et}"
        return f"{sn}{ix}<<{et}>>"


@dataclass
class ObjectPath:
    """
    A path between the tree root of an object and a particular element.
    """

    components: List[PathComponent] = field(default_factory=list)

    def append(self, component: PathComponent):
        """
        Append a path component to the path.

        :param component:
        :return:
        """
        self.components.append(component)


@dataclass
class Context:
    """ "
    A context represents a particular state in traversing a tree of objects.
    """

    schemaview: SchemaView = None
    source_path: ObjectPath = None
    target_path: List = field(default_factory=list)

    def set_root(self, root: Union[str, ElementName]) -> None:
        """
        Set the root of the path.

        :param root:
        :return:
        """
        self.source_path = ObjectPath()
        self.source_path.append(PathComponent(root))

    @property
    def target_depth(self) -> int:
        """
        The depth of the target path.

        :return:
        """
        return len(self.target_path)

    @property
    def current(self) -> Optional[PathComponent]:
        """
        Current position in the path.

        :return:
        """
        if not self.source_path or not self.source_path.components:
            return None
        return self.source_path.components[-1]

    @property
    def in_collection(self) -> bool:
        """
        True if the current element is in a collection.

        :return:
        """
        head = self.current
        if head is None or head.slot is None:
            return False
        return head.slot.multivalued and head.index is None

    def _copy(self) -> "Context":
        # shallow copy, but with a new source_path
        c = copy(self)
        c.source_path = deepcopy(self.source_path)
        c.target_path = deepcopy(self.target_path)
        return c

    def extend(
        self, slot: Optional[SlotDefinition] = None, target_element: Any = None
    ) -> "Context":
        new_context = self._copy()
        if slot:
            component = PathComponent(slot=slot, element_type=slot.range)
            # range_element = slot.range
            # new_context.element_name = range_element
            new_context.source_path.append(component)
        if target_element:
            new_context.target_path.append(target_element)
        return new_context

    def index_extend(self, index: Any, target_element: Any = None) -> "Context":
        new_context = self._copy()
        new_context.current.index = index
        if target_element:
            new_context.target_path.append(target_element)
        return new_context

    @property
    def current_element_type(self) -> Union[ClassDefinition, EnumDefinition, TypeDefinition]:
        elt = self.schemaview.get_element(self.current.element_type)
        if not isinstance(elt, (ClassDefinition, EnumDefinition, TypeDefinition)):
            raise TypeError(f"Unexpected element type: {elt}")
        return elt

    @property
    def in_object(self) -> bool:
        head = self.current
        if head is None:
            return False
        return head.element_type in self.schemaview.all_classes() and (
            head.slot is None or head.slot.inlined
        )

    @property
    def in_object_reference(self) -> bool:
        head = self.current
        if head is None:
            return False
        return (
            head.element_type in self.schemaview.all_classes()
            and head.slot is not None
            and not head.slot.inlined
        )

    @property
    def source_path_str(self) -> str:
        return "/".join([str(x) for x in self.source_path.components])

    @property
    def target_path_str(self) -> str:
        return "/".join([str(x) for x in self.target_path])

    def __repr__(self) -> str:
        return f"{self.source_path_str} -> {self.target_path_str}"
