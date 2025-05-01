"""Source file"""

import os
from pathlib import Path


class SourceFile:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def update_time(self):
        return os.path.getmtime(self.path)
