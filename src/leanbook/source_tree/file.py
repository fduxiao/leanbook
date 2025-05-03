"""Source file"""

import os
from pathlib import Path
from ..lean_parser import Module, module_parser, Fail


class SourceFile:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.module: Module | None = None

    def update_time(self):
        return os.path.getmtime(self.path)

    def read(self):
        with open(self.path) as file:
            content = file.read()
        self.module = module_parser.parse_str(content)
        if isinstance(self.module, Fail):
            raise SyntaxError(self.path, Fail)
