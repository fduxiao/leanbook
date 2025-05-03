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
class Word(Token):
    pass


@dataclass()
class Keyword(Word):
    pass


@dataclass()
class Code(Token):
    pass
