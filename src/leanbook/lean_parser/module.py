from dataclasses import dataclass, field

from . import token, lexer
from .parser import MonadicParser, Fail, get_ctx, Pos


@dataclass()
class Element:
    pos: Pos

    def symbols(self):
        yield from ()

    def element_stream(self):
        yield self


@dataclass()
class Comment(Element):
    content: str


@dataclass()
class ModuleComment(Element):
    content: str


@dataclass()
class Code(Element):
    content: str


@dataclass()
class Import(Element):
    name: str


@dataclass()
class Declaration(Element):
    """Things that can be referred to"""

    type: str
    name: str | None
    body: str
    modifier: str = ""
    doc_string: str = ""

    def symbols(self):
        yield self.pos, self.name


@dataclass()
class PushScope(Element):
    type: str
    name: str | None = None


@dataclass()
class PopScope(Element):
    pass


@dataclass()
class Group(Element):
    end_pos: Pos = field(default_factory=lambda: Pos(0, 1, 1))
    name: str | None = None
    elements: list[Element] = field(default_factory=list)
    add_name = True
    type = ""

    def append(self, element: Element):
        self.elements.append(element)
        return self

    def symbols(self):
        for one in self.elements:
            for pos, sym in one.symbols():
                if self.add_name:
                    if self.name is not None:
                        sym = f"{self.name}.{sym}"
                yield pos, sym

    def element_stream(self):
        name = None
        if self.add_name:
            name = self.name
        yield PushScope(self.pos, self.type, name)
        for one in self.elements:
            yield from one.element_stream()
        yield PopScope(self.end_pos)


@dataclass()
class Section(Group):
    add_name = False
    type = "section"


@dataclass()
class Namespace(Group):
    type = "namespace"


@dataclass()
class Module(Group):
    type = "module"


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


class GroupParser(MonadicParser):
    def __init__(self, group_class=Group):
        self.group_class = group_class

    def do(self):
        ctx = yield get_ctx
        section = self.group_class(ctx.pos)
        while True:
            tk = yield lexer.any_token
            if isinstance(tk, token.EOF):
                break
            if isinstance(tk, token.ModuleComment):
                section.append(ModuleComment(pos=tk.pos, content=tk.content))
                continue
            if isinstance(tk, token.DocString):
                decl = yield decl_parser
                decl.doc_string = tk.content
                section.append(decl)
                continue
            if isinstance(tk, token.Comment):
                section.append(Comment(pos=tk.pos, content=tk.content))
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
        section.end_pos = ctx.pos
        return section


section_parser = GroupParser(Section)
namespace_parser = GroupParser(Namespace)
module_parser = GroupParser(Module)
