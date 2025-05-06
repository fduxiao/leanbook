"""Source tree"""

from dataclasses import dataclass
from pathlib import Path
import tomllib

from .file import SourceFile
from .symbol_tree import SymbolTree


def iter_subtree(path: Path):
    one: Path
    for one in path.iterdir():
        if one.is_dir():
            yield from iter_subtree(one)
        elif one.is_file() and one.with_suffix(".lean"):
            yield one


def parse_module_name(rel_path: Path):
    module_name = ".".join(rel_path.parts)
    if module_name.endswith(".lean"):
        module_name = module_name[:-5]
    return module_name


@dataclass()
class TOCHint:
    up: str | None = None
    prev: str | None = None
    next: str | None = None


class SourceTree:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.top_modules: dict[Path, str] = {}
        self.toc_hits: dict[str, TOCHint] = {}
        self.file_map: dict[Path, SourceFile] = {}
        self.symbol_tree = SymbolTree()

    @property
    def lakefile_toml(self):
        return self.path / "lakefile.toml"

    def iter_files(self):
        with open(self.lakefile_toml) as file:
            lakefile = tomllib.loads(file.read())
        dirs = lakefile["lean_lib"]
        for one in dirs:
            top_module = self.path / f"{one['name']}.lean"
            if top_module.exists():
                rel_path = top_module.relative_to(self.path)
                module_name = parse_module_name(rel_path)
                self.top_modules[rel_path] = module_name
                yield (
                    rel_path,
                    SourceFile(top_module.absolute(), module_name=module_name),
                )
            dir_path = self.path / one["name"]
            for file_path in iter_subtree(dir_path):
                rel_path = file_path.relative_to(self.path)
                yield (
                    rel_path,
                    SourceFile(
                        file_path.absolute(), module_name=parse_module_name(rel_path)
                    ),
                )

    def scan_files(self):
        self.file_map.clear()
        file: SourceFile
        for rel_path, file in self.iter_files():
            self.file_map[rel_path] = file

    def read_files(self):
        for file in self.file_map.values():
            file.read()

    def build_symbols(self):
        self.symbol_tree.clear()
        for rel_path, file in self.file_map.items():
            module = file.module
            self.symbol_tree.add_symbol(rel_path, module.name, None)
            for pos, symbol in file.module.symbols():
                self.symbol_tree.add_symbol(rel_path, symbol, pos)

    def build_toc_hint(self):
        self.toc_hits.clear()
        children_lists = {}
        # make empty hints
        for file in self.file_map.values():
            self.toc_hits.setdefault(file.module_name, TOCHint())
        # we first find parents and children
        for file in self.file_map.values():
            toc = file.module.toc_hint
            if toc is None:
                continue
            children_lists[file.module_name] = [x[0] for x in toc]
            for child, _ in toc:
                self.toc_hits[child].up = file.module_name
        # the prev and next
        for file in self.file_map.values():
            hint = self.toc_hits[file.module_name]
            parent = hint.up
            siblings = children_lists.get(parent, None)
            if siblings is None:
                continue
            # must be true
            index = siblings.index(file.module_name)
            if index > 0:
                hint.prev = siblings[index - 1]
            if index < len(siblings) - 1:
                hint.next = siblings[index + 1]

    def get_toc_hint(self, module_name):
        return self.toc_hits[module_name]

    def build_tree(self):
        self.scan_files()
        self.read_files()
        self.build_symbols()
        self.build_toc_hint()
