"""Source file"""

import os
from pathlib import Path
from ..lean_parser import Module, module_parser


class SourceFile:
    def __init__(self, path: str | Path, module_name=None):
        self.path = Path(path)
        self.module: Module | None = None
        self.module_name: str | None = module_name

    def update_time(self):
        return os.path.getmtime(self.path)

    def read(self):
        with open(self.path) as file:
            content = file.read()
        self.module = module_parser.parse_str(content, file_path=str(self.path))
        self.module.name = self.module_name
