from dataclasses import dataclass
from functools import update_wrapper


class SourceContext:
    def __init__(self, text: str, pos=0):
        self.text = text
        self.pos = pos

    def look(self, n=1):
        r = self.text[self.pos : self.pos + n]
        if self.pos + n > len(self.text):
            return None
        return r

    def at(self, n=0):
        n += self.pos
        if n >= len(self.text):
            return None
        return self.text[n]

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

    def find(self, sub, start=0):
        index = self.text.find(sub, self.pos + start)
        if index < 0:
            return None
        return index - self.pos

    def get_line_number(self):
        before = self.text[: self.pos]
        return before.count("\n") + 1

    def __repr__(self):
        return f"SourceContext(line={self.get_line_number()}, pos={self.pos})"


@dataclass(init=False)
class Fail:
    ctx: SourceContext
    args: tuple

    def __init__(self, ctx, *args):
        self.ctx = ctx
        self.args = args


class TryFail:
    pass


class BaseParser:
    def parse(self, ctx: SourceContext):
        return Fail(ctx)

    def parse_str(self, text: str, pos=0):
        return self.parse(SourceContext(text, pos=pos))

    def __or__(self, other: "BaseParser") -> "BaseParser":
        return OrElse(self, other)

    def try_fail(self):
        return TryParser(self)

    def try_look(self):
        return TryLookParser(self)


class TryParser(BaseParser):
    def __init__(self, parser: BaseParser):
        self.parser = parser

    def parse(self, ctx: SourceContext):
        pos = ctx.pos
        r = self.parser.parse(ctx)
        if isinstance(r, Fail):
            ctx.pos = pos
            return TryFail
        return r


class OrElse(BaseParser):
    def __init__(self, p1: BaseParser, p2: BaseParser):
        self.p1 = p1
        self.p2 = p2

    def parse(self, ctx: SourceContext):
        pos = ctx.pos
        r = self.p1.parse(ctx)
        if isinstance(r, Fail):
            ctx.pos = pos
            return self.p2.parse(ctx)
        return r


class TryLookParser(BaseParser):
    def __init__(self, parser: BaseParser):
        self.parser = parser

    def parse(self, ctx: SourceContext):
        pos = ctx.pos
        r = self.parser.parse(ctx)
        if isinstance(r, Fail):
            r = TryFail
        ctx.pos = pos
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
                if isinstance(result, Fail):
                    return result
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


class EOF(BaseParser):
    def parse(self, ctx: SourceContext):
        x = ctx.look(1)
        if x is None:
            return None
        return Fail(f"Expect EOF, but got `{x}`")


eof = EOF()


class String(BaseParser):
    def __init__(self, s: str):
        self.s = s

    def parse(self, ctx: SourceContext):
        read = ctx.take(len(self.s))
        if read is None:
            return Fail(ctx, "Unexpected EOF")
        if self.s == read:
            return self.s
        return Fail(ctx, f"Expect `{self.s}`, but got `{read}`")


class Many(BaseParser):
    def __init__(self, parser: BaseParser):
        self.parser = parser

    def parse(self, ctx: SourceContext):
        result = []
        while True:
            pos = ctx.pos
            one = self.parser.parse(ctx)
            if isinstance(one, Fail):
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
            return Fail(ctx, f"Unable to take {self.n} chars")
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
            if not isinstance(self.until.parse(ctx), Fail):
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
