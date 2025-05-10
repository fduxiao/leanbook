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
    # I would like to add this. Now, let's keep it simple
    # end_pos: SourcePos | None = None


@dataclass()
class Command(Token):
    names = [
        # declarations
        "def",
        "abbrev",
        "inductive",
        "theorem",
        "instance",
        "class",
        "axiom",
        # sections
        "namespace",
        "section",
        "mutual",
        "end",
        "import",
        "open",
        # directives
        "#check",
        "#eval",
        "set_option",
        # syntax
        "syntax",
        "macro",
        "notation",
        "declare_syntax_cat",
        "macro_rules"
    ]

    def is_declaration(self):
        return self.content in [
            "def",
            "abbrev",
            "inductive",
            "theorem",
            "instance",
            "class",
            "axiom"
        ]


@dataclass()
class DeclModifier(Token):
    pass


@dataclass()
class Code(Token):
    pass
