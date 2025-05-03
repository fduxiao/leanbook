from dataclasses import dataclass


@dataclass()
class Token:
    pos: int
    content: str = None


@dataclass()
class End(Token):
    pass


@dataclass()
class Comment(Token):
    pass


@dataclass()
class ModuleComment(Comment):
    pass


@dataclass()
class DocString(ModuleComment):
    pass


@dataclass()
class Identifier(Token):
    pass


@dataclass()
class Command(Token):
    def is_declaration(self):
        return self.content in [
            "def",
            "abbrev",
            "inductive",
            "theorem",
            "instance",
            "class",
        ]


@dataclass()
class DeclModifier(Token):
    pass


@dataclass()
class Code(Token):
    pass
