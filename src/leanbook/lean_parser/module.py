from dataclasses import dataclass, field
from typing import Union

from . import token, lexer
from .parser import MonadicParser, Fail, get_ctx

Comment = token.Comment
ModuleComment = token.ModuleComment
Code = token.Code


@dataclass()
class Import:
    pos: int
    name: str


@dataclass()
class Declaration:
    """Things that can be referred to"""

    pos: int
    type: str
    name: str | None
    body: str
    modifier: str = ""
    doc_string: str = ""


Thing = Union[ModuleComment | Code | Import | Declaration | Comment, "Section"]


@dataclass()
class Section:
    pos: int = 0
    name: str | None = None
    things: list[Thing] = field(default_factory=list)
    head_comment: str = None

    def append(self, thing: Thing):
        self.things.append(thing)
        return self


@dataclass()
class Namespace(Section):
    pass


@dataclass()
class Module(Section):
    pass


class DeclParser(MonadicParser):
    def do(self):
        ctx = yield get_ctx
        # read a token
        tk = yield lexer.any_token
        decl_modifier = ""
        if isinstance(tk, token.DeclModifier):
            decl_modifier = tk.content
            tk = yield lexer.any_token
        # it must be a command
        if not isinstance(tk, token.Command):
            return Fail(ctx, f"Expect command, but got {tk}")
        if not tk.is_declaration():
            return Fail(ctx, f"Expect a declaration, but got {tk}")
        decl_type = tk.content
        decl_pos = tk.pos
        # read the name
        tk = yield lexer.any_token
        name = None
        if not isinstance(tk, token.Identifier):
            if decl_type != "instance":
                return Fail("Expect an identifier")
            # set back the pos
            ctx.pos = tk.pos
        else:
            name = tk.content
        # parse body
        body = ""
        ctx = yield get_ctx
        while True:
            pos = ctx.pos
            tk = yield lexer.any_token
            if isinstance(tk, token.EOF):
                break
            if isinstance(tk, token.Code):
                body += tk.content
            else:
                ctx.pos = pos
                break
        return Declaration(decl_pos, decl_type, name, body, decl_modifier)


decl_parser = DeclParser()


class SectionParser(MonadicParser):
    def __init__(self, section_class=Section):
        self.section_class = section_class

    def do(self):
        ctx = yield get_ctx
        section = self.section_class()
        while True:
            tk = yield lexer.any_token
            if isinstance(tk, token.EOF):
                break
            if isinstance(tk, token.ModuleComment):
                section.append(tk)
                continue
            if isinstance(tk, token.DocString):
                decl = yield decl_parser
                decl.doc_string = tk.content
                section.append(decl)
                continue
            if isinstance(tk, token.Comment):
                if section.head_comment is None:
                    section.head_comment = tk.content
                section.append(tk)
                continue
            if isinstance(tk, token.DeclModifier):
                decl = yield decl_parser
                decl.modifier = tk.content
                section.append(decl)
                continue
            if isinstance(tk, token.Command):
                if tk.is_declaration():
                    ctx.pos = tk.pos
                    decl = yield decl_parser
                    section.append(decl)
                    continue
                if tk.content == "import":
                    tk = yield lexer.identifier
                    section.append(Import(tk.pos, tk.content))
                    continue
            return Fail(ctx, f"Unknown Token {tk}")
        return section


section_parser = SectionParser(Section)
namespace_parser = SectionParser(Namespace)
module_parser = SectionParser(Module)
