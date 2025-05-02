from dataclasses import dataclass, field


class Token:
    pass


class End(Token):
    pass


@dataclass()
class Comment(Token):
    content: str


@dataclass()
class ModuleComment(Comment):
    pass


@dataclass()
class DocString(ModuleComment):
    pass


@dataclass()
class Word:
    word: str


@dataclass()
class Keyword(Word):
    pass


@dataclass()
class Code(Token):
    content: str
    doc_string: str = ""


@dataclass()
class LeanFile:
    things: list[Token] = field(default_factory=list)

    def append(self, ast: Token):
        self.things.append(ast)

    def add_comment(self, comment):
        self.append(Comment(comment))

    def add_code(self, code):
        self.append(Code(code))

    def build_doc_string(self):
        pass
