from functools import update_wrapper


class SourceContext:
    def __init__(self, text: str, pos=0):
        self.text = text
        self.pos = pos

    def look(self, n=1):
        r = self.text[self.pos : self.pos + n]
        if r == "":
            return None
        return r

    def shift(self, n=1):
        self.pos += n

    def take(self, n=1):
        text = self.look(n)
        if text is None:
            return None
        self.shift(n)
        return text

    def end(self):
        return self.pos >= len(self.text)

    def rest(self):
        return self.text[self.pos :]


class Fail:
    pass


class BaseParser:
    def parse(self, ctx: SourceContext):
        return Fail

    def parse_str(self, text: str, pos=0):
        return self.parse(SourceContext(text, pos=pos))

    def __or__(self, other: "BaseParser") -> "BaseParser":
        return OrElse(self, other)


class OrElse(BaseParser):
    def __init__(self, p1: BaseParser, p2: BaseParser):
        self.p1 = p1
        self.p2 = p2

    def parse(self, ctx: SourceContext):
        pos = ctx.pos
        r = self.p1.parse(ctx)
        if r is Fail:
            ctx.pos = pos
            return self.p2.parse(ctx)
        return r


class GetCtx(BaseParser):
    def parse(self, ctx: SourceContext):
        return ctx


get_ctx = GetCtx()


class MonadicParser(BaseParser):
    def do(self):
        yield BaseParser()

    def run_monad(self, ctx: SourceContext):
        generator = self.do()
        value = None
        while True:
            try:
                parser = generator.send(value)
                result = parser.parse(ctx)
                if result is Fail:
                    return Fail
                value = result
            except StopIteration as err:
                return err.value

    def parse(self, ctx: SourceContext):
        return self.run_monad(ctx)


def parser_do(func) -> MonadicParser:
    parser = MonadicParser()
    parser.do = func
    update_wrapper(parser, func)
    return parser


class String(BaseParser):
    def __init__(self, s: str):
        self.s = s

    def parse(self, ctx: SourceContext):
        read = ctx.take(len(self.s))
        if read is None:
            return Fail
        if self.s == read:
            return self.s
        return Fail


class Many(BaseParser):
    def __init__(self, parser: BaseParser):
        self.parser = parser

    def parse(self, ctx: SourceContext):
        result = []
        while True:
            pos = ctx.pos
            one = self.parser.parse(ctx)
            if one is Fail:
                ctx.pos = pos
                break
            result.append(one)
        return result


class Any(BaseParser):
    def __init__(self, n=1):
        self.n = n

    def parse(self, ctx: SourceContext):
        ch = ctx.take(self.n)
        if ch is None:
            return Fail
        return ch


class Spaces(BaseParser):
    def parse(self, ctx: SourceContext):
        result = ""
        while True:
            x = ctx.look(1)
            if x in [" ", "\n", "\t", "\r"]:
                result += ctx.take(1)
            else:
                break
        return result


spaces = Spaces()


class AnyUntil(BaseParser):
    def __init__(self, until: BaseParser):
        self.until = until

    def parse(self, ctx: SourceContext):
        result = ""
        while True:
            # try parse until
            pos = ctx.pos
            if self.until.parse(ctx) is not Fail:
                # restore the state
                ctx.pos = pos
                break
            ctx.pos = pos
            if ctx.end():
                break
            result += ctx.take(1)
        return result


class StrLiteral(MonadicParser):
    delim = '"'

    def __init__(self, delim=None):
        self.ctx = GetCtx()
        if delim is not None:
            self.delim = delim  # delimiter
        self.start = String(self.delim)
        self.end = String(self.delim)

    def do(self):
        yield self.start
        ctx = yield self.ctx
        result = ""
        while True:
            x = ctx.look(1)
            if x is None:
                break
            if x == self.delim:
                break
            if x == "\\":
                result += ctx.take(2)
            else:
                result += ctx.take(1)
        yield self.end
        result = self.delim + result + self.delim
        return result


str_literal = StrLiteral()


class CharLiteral(StrLiteral):
    delim = "'"


char_literal = CharLiteral()
