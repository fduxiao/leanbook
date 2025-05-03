import re

from .parser import MonadicParser, Fail, TryFail, get_ctx
from . import parser, token


class BlockComment(MonadicParser):
    def __init__(self):
        self.start = parser.String("/-")
        self.end = parser.String("-/")
        self.until_mark = parser.AnyUntil(self.start | self.end)

    def do(self):
        ctx = yield parser.get_ctx
        yield self.start
        result = ""
        while True:
            x = ctx.look(2)
            if x is None:
                break
            if x == "-/":
                break
            if x == "/-":
                x = yield self
                result += x
            else:
                x = yield self.until_mark
                result += x
        yield self.end
        return "/-" + result + "-/"


block_comment = BlockComment()


class LineComment(MonadicParser):
    def __init__(self):
        self.start = parser.String("--")
        self.end = parser.String("\n") | parser.eof
        self.until = parser.AnyUntil(self.end)

    def do(self):
        yield self.start
        x = yield self.until
        yield self.end
        return "--" + x


line_comment = LineComment()


class Identifier(MonadicParser):
    def __init__(self):
        self.pattern = re.compile(r"\w+(\.(\w+))*")

    def do(self):
        ctx = yield parser.get_ctx
        pos = ctx.pos
        match = self.pattern.match(ctx.text, pos.index)
        if match is None:
            return Fail(ctx, "Expect identifier")
        (start, end) = match.span(0)
        if start != pos.index:
            return Fail(ctx, f"Expect identifier, but got `{ctx.at()}`")
        if start == end:
            return Fail(ctx, "Empty identifier")
        ctx.shift(end - pos.index)
        result: str = ctx.text[start:end]
        return result


identifier_parser = Identifier()


class Command(MonadicParser):
    commands = [
        # declarations
        "def",
        "abbrev",
        "inductive",
        "theorem",
        "instance",
        "class",
        # sections
        "namespace",
        "section",
        "end",
        "import",
        # directives
        "#check",
        "#eval",
    ]

    def do(self):
        ctx = yield parser.get_ctx
        for w in self.commands:
            n = len(w)
            if ctx.look(n) != w:
                continue
            x = ctx.at(n)
            if x is not None:
                if x == "." or x == "_":
                    continue
                if x.isalnum():
                    continue
            ctx.shift(n)
            return w
        return Fail(ctx, "Expect a command")


command_parser = Command()


class CodeParser(MonadicParser):
    def do(self):
        ctx = yield parser.get_ctx
        result = ""
        while True:
            if ctx.end():
                break
            if ctx.look(1) == '"':
                result += yield parser.str_literal
                continue
            if ctx.look(2) == "/-":
                break
            if ctx.look(2) == "--":
                break
            if ctx.look(2) == "@[":
                break
            # stop at keywords
            cmd = yield command_parser.try_look()
            if cmd is not TryFail:
                break
            result += ctx.take(1)
        return result


code_parser = CodeParser()


class Lexer(MonadicParser):
    """
    Tokenizer / Lexer
    """

    def do(self):
        ctx = yield parser.get_ctx
        yield parser.spaces
        pos = ctx.pos
        if ctx.end():
            return token.EOF(pos)

        if ctx.look(2) == "/-":
            x = yield block_comment
            x = x.strip()
            if x.startswith("/--"):
                return token.DocString(pos, x)
            if x.startswith("/-!"):
                return token.ModuleComment(pos, x)
            return token.Comment(pos, x)
        if ctx.look(2) == "--":
            x = yield line_comment
            x = x.strip() + "\n"
            return token.Comment(pos, x)
        if ctx.look(2) == "@[":
            index = ctx.find("]")
            if index < 0:
                return Fail(ctx, "Expect ']'")
            x = ctx.take(index + 1)
            return token.DeclModifier(pos, x)

        cmd = yield command_parser.try_fail()
        if cmd is not TryFail:
            return token.Command(pos, cmd)

        w = yield identifier_parser.try_fail()
        if w is not TryFail:
            return token.Identifier(pos, w)

        # read code
        x = yield code_parser
        x = x.strip()
        return token.Code(pos, x)


any_token = Lexer()


class ExpectToken(MonadicParser):
    def __init__(self, token_class):
        self.token_class = token_class

    def do(self):
        ctx = yield get_ctx
        tk = yield any_token
        if not isinstance(tk, self.token_class):
            return Fail(ctx, f"Expect `{self.token_class}`, but got `{tk}`")
        return tk


eof = ExpectToken(token.EOF)
comment = ExpectToken(token.Comment)
module_comment = ExpectToken(token.ModuleComment)
doc_string = ExpectToken(token.DocString)
identifier = ExpectToken(token.Identifier)
command = ExpectToken(token.Command)
decl_modifier = ExpectToken(token.DeclModifier)
code = ExpectToken(token.Code)


class AllToken(MonadicParser):
    def __init__(self):
        self.comment = BlockComment()
        self.code = CodeParser()

    def do(self):
        result = []
        while True:
            tk = yield any_token
            result.append(tk)
            if isinstance(tk, token.EOF):
                break
        return result
