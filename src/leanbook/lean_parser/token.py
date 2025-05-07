from dataclasses import dataclass
from .parser import SourcePos


@dataclass()
class Token:
    pos: SourcePos
    content: str = None


@dataclass()
class EOF(Token):
    pass


@dataclass()
class Comment(Token):
    pass


@dataclass()
class ModuleComment(Token):
    pass


@dataclass()
class DocString(Token):
    pass


@dataclass()
class TOCHint(Token):
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
