import re
import mistletoe
from mistletoe import block_token, span_token
from mistletoe.html_renderer import HtmlRenderer
from mistletoe.span_token import SpanToken

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from .context import DocumentContext


class BibRef(SpanToken):
    parse_inner = True
    parse_group = 1
    pattern = re.compile(r"\[(.*?)]\[(.*?)]")

    def __init__(self, match):
        super().__init__(match)
        self.inner = match.group(1)
        self.reference = match.group(2)


class Math(SpanToken):
    parse_inner = False
    parse_group = 0
    pattern = re.compile(r"\$\$?(.+?)\$?\$")

    def __init__(self, match):
        super().__init__(match)
        self.math = match.group(1)


def parse_md(md):
    return mistletoe.Document(md)


class MDRender(HtmlRenderer):
    def __init__(self, ctx: DocumentContext, toc):
        self.toc = toc
        self.ctx = ctx
        super().__init__(BibRef, Math)

    def clear_toc(self):
        self.toc.clear()

    def render_bib_ref(self, token: BibRef) -> str:
        inner = self.render_inner(token)
        href = f"#ref_{token.reference}"
        return f'<a href="../api/references.html{href}">{inner}</a>'

    def render_heading(self, token: block_token.Heading) -> str:
        content = token.children[0].content
        anchor = content.replace(" ", "_")
        level = token.level
        link = f'<a class="anchor" href="#{anchor}">#</a>'
        heading = f'<h{level} id="{anchor}">{content} {link}</h{level}>'
        self.toc.add(token.level, content, anchor)
        return heading

    def render_block_code(self, token: block_token.BlockCode) -> str:
        content = token.content
        language = token.language

        cssclass = "highlight"
        if language == "lean-source":
            # lean code from the file directly
            language = "lean"
            cssclass = "highlight source"

        if language == "":
            lexer = guess_lexer(content)
        else:
            lexer = get_lexer_by_name(language)
        return highlight(content, lexer, HtmlFormatter(cssclass=cssclass))

    def render_inline_code(self, token: span_token.InlineCode) -> str:
        symbol = token.children[0].content
        resolved = self.ctx.resolve(symbol)
        if resolved is None:
            return super().render_inline_code(token)
        url, pos = resolved
        anchor = ""
        if pos is not None:
            anchor = f"#{symbol}"
        return f'<a href="{url}{anchor}">{symbol}</a>'

    def render_math(self, token: Math) -> str:
        if token.content.startswith("$$"):
            return self.render_raw_text(token)
        return f"\\({token.math}\\)"
