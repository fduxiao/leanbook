"""Target tree"""

from pathlib import Path

from ..source_tree import SourceTree, SourceFile


class TargetTree:
    def __init__(self, source_tree: SourceTree, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.source_tree = source_tree

    def get_path(self, rel_path):
        return self.output_dir / rel_path

    def render_file(self, rel_path: Path):
        file: SourceFile = self.source_tree.file_map[rel_path]
        print(str(rel_path), file.content[:10])

    def render_all(self):
        for rel_path in self.source_tree.file_map:
            self.render_file(rel_path)
