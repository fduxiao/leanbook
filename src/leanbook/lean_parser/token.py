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
    pass


@dataclass()
class DeclModifier(Token):
    pass


@dataclass()
class Code(Token):
    pass
