from ..source_tree import SourceTree


class DocumentContext:
    def __init__(self, source_tree: SourceTree):
        self.source_tree = source_tree
        self.ctx_stack = []

    def parse_symbol(self, symbol):
        pass

    def push_scope(self, name):
        self.ctx_stack.append([])

    def pop_scope(self):
        self.ctx_stack.pop()

    def resolve(self, symbol):
        symbol_tree = self.source_tree.symbol_tree
        result = symbol_tree.find(symbol)
        if result is None:
            return None
        rel_path = result.rel_path
        module = self.source_tree.file_map[rel_path]
        return f"{module.module_name}.html", result.source_pos
