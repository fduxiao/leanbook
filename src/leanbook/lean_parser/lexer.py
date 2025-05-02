from .parser import MonadicParser
from . import parser, token
from .token import Comment


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
        if ctx.end():
            return token.End

        if ctx.look(2) == "/-":
            x: str = yield block_comment
            x = x.strip()
            if x.startswith("/--"):
                return token.DocString(x)
            if x.startswith("/-!"):
                return token.ModuleComment(x)
            return Comment(x)

        # read code
        x = yield code
        x = x.strip()
        return token.Code(x)


lexer = Lexer()


class BlockParser(MonadicParser):
    def __init__(self):
        self.comment = BlockComment()
        self.code = CodeParser()

    def do(self):
        result = []
        while True:
            tk = yield lexer
            if tk is token.End:
                break
            result.append(tk)
        return result
