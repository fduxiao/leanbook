from dataclasses import dataclass, field


class AST:
    pass


@dataclass()
class Comment(AST):
    content: str


@dataclass()
class Code(AST):
    content: str
    doc_string: str = ""


@dataclass()
class LeanFile:
    things: list[AST] = field(default_factory=list)

    def append(self, ast: AST):
        self.things.append(ast)

    def add_comment(self, comment):
        self.append(Comment(comment))

    def add_code(self, code):
        self.append(Code(code))

    def build_doc_string(self):
        pass
