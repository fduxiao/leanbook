import re

from .parser import MonadicParser, get_ctx, Fail, TryFail
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
        self.end = parser.String("\n")
        self.until = parser.AnyUntil(self.end)

    def do(self):
        yield self.start
        x = yield self.end
        yield self.end
        return x


line_comment = LineComment()


class Word(MonadicParser):
    def __init__(self):
        self.pattern = re.compile(r"[\w.]*")

    def do(self):
        ctx = yield get_ctx
        match = self.pattern.match(ctx.text, ctx.pos)
        if match is None:
            return Fail
        (start, end) = match.span(0)
        if start == end:
            return Fail
        ctx.pos = end
        return ctx.text[start:end]


word = Word()


class Keyword(MonadicParser):
    keywords = ["def", "inductive", "instance", "namespace", "section", "end", "import"]

    def do(self):
        w = yield word
        if w in self.keywords:
            return w
        return Fail


keyword = Keyword()


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
            # stop at keywords
            kw = yield keyword.try_look()
            if kw is not TryFail:
                break
            result += ctx.take(1)
        return result


code = CodeParser()


class Lexer(MonadicParser):
    """
    Tokenizer / Lexer
    """

    def do(self):
        ctx = yield parser.get_ctx
        yield parser.spaces
        pos = ctx.pos
        if ctx.end():
            return token.End(pos)

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

        kw = yield keyword.try_fail()
        if kw is not TryFail:
            return token.Keyword(pos, kw)

        w = yield word.try_fail()
        if w is not TryFail:
            return token.Word(pos, w)

        # read code
        x = yield code
        x = x.strip()
        return token.Code(pos, x)


lexer = Lexer()


class AllToken(MonadicParser):
    def __init__(self):
        self.comment = BlockComment()
        self.code = CodeParser()

    def do(self):
        result = []
        while True:
            tk = yield lexer
            result.append(tk)
            if isinstance(tk, token.End):
                break
        return result
