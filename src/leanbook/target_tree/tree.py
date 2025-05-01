"""Target tree"""

from pathlib import Path

from ..source_tree import SourceTree


class TargetTree:
    def __init__(self, source_tree: SourceTree, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.source_tree = source_tree

    def get_path(self, rel_path):
        return self.output_dir / rel_path

    def render_file(self, rel_path: Path):
        pass

    def render_all(self):
        print(self.source_tree)
