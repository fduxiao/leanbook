"""Source file"""

import os
from pathlib import Path


class SourceFile:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.content = None
        self.ast = None

    def update_time(self):
        return os.path.getmtime(self.path)

    def read(self):
        with open(self.path) as file:
            self.content = file.read()
        self.parse()

    def parse(self):
        pass
