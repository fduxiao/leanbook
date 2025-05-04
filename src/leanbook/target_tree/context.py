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
