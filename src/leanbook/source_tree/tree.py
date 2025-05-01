"""Source tree"""

from pathlib import Path


class SourceTree:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.file_map = {}
        self.symbol_map = {}

    @property
    def lakefile_toml(self):
        return self.path / "lakefile.toml"

    def scan_files(self):
        pass

    def read_files(self):
        pass

    def build_symbols(self):
        pass

    def build_tree(self):
        self.scan_files()
        self.read_files()
        self.build_symbols()
