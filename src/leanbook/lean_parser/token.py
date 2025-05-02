from dataclasses import dataclass


@dataclass()
class Token:
    pos: int


@dataclass()
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
class Word(Token):
    word: str


@dataclass()
class Keyword(Word):
    pass


@dataclass()
class Code(Token):
    content: str
