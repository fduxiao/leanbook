"""Source tree"""

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


class SourceTree:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.top_modules: dict[Path, str] = {}
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

    def build_tree(self):
        self.scan_files()
        self.read_files()
        self.build_symbols()
