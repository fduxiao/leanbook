from dataclasses import dataclass
from functools import update_wrapper


@dataclass()
class SourcePos:
    index: int
    line: int
    col: int
    file_path: str | None = None

    def copy(self):
        return SourcePos(self.index, self.line, self.col, self.file_path)


class SourceContext:
    def __init__(self, text: str, file_path: str = None):
        self.text = text
        self.index = 0
        self.line = 1
        self.col = 1
        self.file_path = file_path

    def look(self, n=1):
        start = self.index
        r = self.text[start : start + n]
        if start + n > len(self.text):
            return None
        return r

    def at(self, n=0):
        n += self.index
        if n >= len(self.text):
            return None
        return self.text[n]

    def shift(self, n=1):
        if n < 0:
            raise ValueError("Don't shift back")
        start = self.index
        end = start + n
        n_lines = self.text.count("\n", start, end)
        self.line += n_lines
        self.index = end
        # calculate column number
        if n_lines == 0:
            # the same line
            self.col += n
            return
        r_index = self.text.rfind("\n", start, end)
        self.col = end - r_index

    def take(self, n=1):
        text = self.look(n)
        if text is None:
            return None
        self.shift(n)
        return text

    def end(self):
        return self.index >= len(self.text)

    def rest(self):
        return self.text[self.index :]

    def find(self, sub, start=0):
        index = self.text.find(sub, self.index + start)
        if index < 0:
            return None
        return index - self.index

    @property
    def pos(self):
        return SourcePos(self.index, self.line, self.col, self.file_path)

    @pos.setter
    def pos(self, pos: SourcePos):
        self.index = pos.index
        self.line = pos.line
        self.col = pos.col


@dataclass(init=False)
class Fail(Exception):
    ctx: SourceContext
    args: tuple

    def __init__(self, ctx, *args):
        self.ctx = ctx
        self.args = args


class BaseParser:
    def parse(self, ctx: SourceContext):
        raise Fail(ctx)

    def parse_str(self, text: str, file_path: str = None):
        return self.parse(SourceContext(text, file_path=file_path))

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
        try:
            return self.parser.parse(ctx)
        except Fail as err:
            ctx.pos = pos
            return err


class OrElse(BaseParser):
    def __init__(self, p1: BaseParser, p2: BaseParser):
        self.p1 = p1
        self.p2 = p2

    def parse(self, ctx: SourceContext):
        pos = ctx.pos
        try:
            return self.p1.parse(ctx)
        except Fail:
            ctx.pos = pos
            return self.p2.parse(ctx)


class TryLookParser(BaseParser):
    def __init__(self, parser: BaseParser):
        self.parser = parser

    def parse(self, ctx: SourceContext):
        pos = ctx.pos
        try:
            r = self.parser.parse(ctx)
        except Fail as err:
            r = err
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
                value = parser.parse(ctx)
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
        raise Fail(f"Expect EOF, but got `{x}`")


eof = EOF()


class String(BaseParser):
    def __init__(self, s: str):
        self.s = s

    def parse(self, ctx: SourceContext):
        read = ctx.take(len(self.s))
        if read is None:
            raise Fail(ctx, "Unexpected EOF")
        if self.s == read:
            return self.s
        raise Fail(ctx, f"Expect `{self.s}`, but got `{read}`")


class Many(BaseParser):
    def __init__(self, parser: BaseParser):
        self.parser = parser

    def parse(self, ctx: SourceContext):
        result = []
        while True:
            pos = ctx.pos
            try:
                result.append(self.parser.parse(ctx))
            except Fail:
                ctx.pos = pos
                break
        return result


class Any(BaseParser):
    def __init__(self, n=1):
        self.n = n

    def parse(self, ctx: SourceContext):
        ch = ctx.take(self.n)
        if ch is None:
            raise Fail(ctx, f"Unable to take {self.n} chars")
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
            if not isinstance(self.until.try_fail().parse(ctx), Fail):
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
