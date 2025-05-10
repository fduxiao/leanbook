import re
from dataclasses import dataclass, field

from . import token, lexer
from .parser import MonadicParser, Fail, get_ctx, SourcePos


@dataclass()
class Element:
    pos: SourcePos

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
class Open(Element):
    names: list[str]


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
    type: str
    name: str | None = None


@dataclass()
class Group(Element):
    end_pos: SourcePos = field(default_factory=lambda: SourcePos(0, 1, 1))
    name: str | None = None
    elements: list[Element] = field(default_factory=list)
    add_name = True
    type = ""
    toc_hint = None

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
        yield PopScope(self.end_pos, self.type, self.name)

    def add_toc_hint(self, comment_string):
        line_pattern = re.compile(r"^[\s ]*?[-*] +`(.*?)`: (.*?)$", re.MULTILINE)
        result = []
        for x in line_pattern.finditer(comment_string):
            result.append(x.groups())
        self.toc_hint = result


@dataclass()
class Section(Group):
    add_name = False
    type = "section"


@dataclass()
class Namespace(Group):
    type = "namespace"


@dataclass()
class Mutual(Group):
    add_name = False
    type = "mutual"


@dataclass()
class Module(Group):
    type = "module"
    head_comment = None


class UntilNextCommand(MonadicParser):
    def do(self):
        ctx = yield get_ctx
        start = ctx.pos
        while True:
            pos = ctx.pos
            tk = yield lexer.any_token
            if isinstance(
                tk,
                (
                    token.EOF,
                    token.ModuleComment,
                    token.Command,
                    token.TOCHint,
                    token.DocString,
                    token.DeclModifier,
                ),
            ):
                end = tk.pos
                ctx.pos = pos
                break
        content = ctx.text[start.index : end.index].rstrip()
        return content


until_next_command = UntilNextCommand()


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
            raise Fail(ctx, f"Expect command, but got {tk}")
        if not tk.is_declaration():
            raise Fail(ctx, f"Expect a declaration, but got {tk}")
        decl_type = tk.content
        decl_pos = tk.pos
        # read the name
        tk = yield lexer.any_token
        name = None
        if not isinstance(tk, token.Identifier):
            if decl_type != "instance":
                raise Fail("Expect an identifier")
            # set back the pos
            ctx.pos = tk.pos
        else:
            name = tk.content
        # parse body
        body = yield until_next_command
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
            if isinstance(tk, token.TOCHint):
                # We have found a TOC token
                # Read the next token, which should be a ModuleComment containing the TOC.
                toc = yield lexer.module_comment
                # Add it to section.
                section.add_toc_hint(toc.content)
                # Then, append the module comment as usual
                section.append(ModuleComment(pos=toc.pos, content=toc.content))
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
                    pos = tk.pos
                    tk = yield lexer.identifier
                    section.append(Import(pos, tk.content))
                    continue
                if tk.content == "open":
                    pos = tk.pos
                    # read until next command or new line
                    current_pos = ctx.pos
                    content = yield until_next_command
                    index = content.find("\n")
                    if index >= 0:
                        ctx.pos = current_pos
                        ctx.shift(index)
                        content = content[:index]
                    names = content.split()
                    section.append(Open(pos, names))
                    continue
                if tk.content == "end":
                    # We should check the previous section/namespace/mutual command.
                    # Since we only parse correct lean files, we simply break here.
                    ctx.pos = tk.pos
                    break
                if tk.content == "mutual":
                    result = yield mutual_parser
                    result.pos = tk.pos
                    tk = yield lexer.command
                    if tk.content != "end":
                        raise Fail(ctx, f"Expect end, but got {tk}")
                    result.end_pos = ctx.pos
                    section.append(result)
                    continue
                if tk.content == "namespace":
                    ident = yield lexer.identifier
                    result = yield namespace_parser
                    result.pos = tk.pos
                    tk = yield lexer.command
                    if tk.content != "end":
                        raise Fail(ctx, f"Expect end, but got {tk}")
                    tk = yield lexer.identifier
                    if tk.content != ident.content:
                        raise Fail(
                            ctx,
                            f"Expect identifier {ident.content}, but got {tk.content}",
                        )
                    result.name = ident.content
                    result.end_pos = tk.end_pos
                    section.append(result)
                    continue
                if tk.content == "section":
                    name = None
                    ident = yield lexer.identifier.try_fail()
                    if not isinstance(ident, Fail):
                        name = ident.content
                    result = yield section_parser
                    result.pos = tk.pos
                    tk = yield lexer.command
                    if tk.content != "end":
                        raise Fail(ctx, f"Expect end, but got {tk}")
                    result.end_pos = ctx.pos
                    if name is not None:
                        tk = yield lexer.identifier
                        if tk.content != ident.content:
                            raise Fail(
                                ctx,
                                f"Expect identifier {ident.content}, but got {tk.content}",
                            )
                        result.name = ident.content
                        result.end_pos = tk.end_pos
                    section.append(result)
                    continue
                # for other command, just read the code
                code = Code(tk.pos, tk.content)
                code.content += yield until_next_command
                section.append(code)
                continue
            raise Fail(ctx, f"Expect command or module command, got {tk}")
        section.end_pos = ctx.pos
        return section


section_parser = GroupParser(Section)
namespace_parser = GroupParser(Namespace)
mutual_parser = GroupParser(Mutual)


class ModuleParser(GroupParser):
    def __init__(self):
        super().__init__(Module)

    def do(self):
        ctx = yield lexer.get_ctx
        pos = ctx.pos
        tk: token.Comment | Fail = yield lexer.comment.try_fail()
        head_comment = None
        if not isinstance(tk, Fail):
            if tk.content.startswith("/-"):
                if tk.content[2] not in "!-":
                    # head comment
                    head_comment = tk.content
            if head_comment is None:
                ctx.pos = pos
        m = yield from super().do()
        m.head_comment = head_comment
        return m


module_parser = ModuleParser()
