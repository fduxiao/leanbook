from dataclasses import dataclass, field
from typing import Any

from ..lean_parser import SourcePos


@dataclass()
class SymbolPos:
    rel_path: Any
    source_pos: SourcePos = None


class TreePath:
    def __init__(self, path: str | list):
        if isinstance(path, str):
            path = path.split(".")
        self.path: list = path
        self.index = 0

    def take(self):
        if self.index >= len(self.path):
            return None
        head = self.path[self.index]
        self.index += 1
        return head

    def __repr__(self):
        return f"TreePath({self.path[self.index :]})"


@dataclass()
class SymbolTree:
    pos: SymbolPos = None
    map: dict[str, "SymbolTree"] = field(default_factory=dict)

    def clear(self):
        self.map.clear()

    def insert_path(self, tree_path: TreePath, rel_path, pos: SourcePos | None):
        target = self
        while True:
            head = tree_path.take()
            if head is None:
                # insert at target
                target.pos = SymbolPos(rel_path, pos)
                break
            target = target.map.setdefault(head, SymbolTree())

    def add(self, rel_path, symbol: str, pos: SourcePos | None):
        tree_path = TreePath(symbol)
        self.insert_path(tree_path, rel_path, pos)

    def to_dict(self):
        result = {}
        for key, value in self.map.items():
            result[key] = value.to_dict()
        return result

    def find(self, tree_path: str | TreePath) -> SymbolPos | None:
        if not isinstance(tree_path, TreePath):
            tree_path = TreePath(tree_path)
        target = self
        while True:
            head = tree_path.take()
            if head is None:
                # return target
                return target.pos
            target = target.map.get(head, None)
            if target is None:
                return None
