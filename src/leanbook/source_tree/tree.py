"""Source tree"""

from pathlib import Path
import tomllib

from .file import SourceFile


def iter_subtree(path: Path):
    one: Path
    for one in path.iterdir():
        if one.is_dir():
            yield from iter_subtree(one)
        elif one.is_file() and one.with_suffix(".lean"):
            yield one


class SourceTree:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.file_map: dict[Path, SourceFile] = {}
        self.symbol_map = {}

    @property
    def lakefile_toml(self):
        return self.path / "lakefile.toml"

    def scan_files(self):
        self.file_map.clear()
        with open(self.lakefile_toml) as file:
            lakefile = tomllib.loads(file.read())
        dirs = lakefile["lean_lib"]
        for one in dirs:
            dir_path = self.path / one["name"]
            for file_path in iter_subtree(dir_path):
                file = SourceFile(file_path.absolute())
                self.file_map[file_path.relative_to(self.path)] = file

    def read_files(self):
        for file in self.file_map.values():
            file.read()

    def build_symbols(self):
        self.symbol_map.clear()

    def build_tree(self):
        self.scan_files()
        self.read_files()
        self.build_symbols()
