from dataclasses import dataclass

import mistletoe
from mistletoe import block_token, span_token
from mistletoe.html_renderer import HtmlRenderer


from ..lean_parser import module
from .context import DocumentContext


class TOC:
    def __init__(self):
        self.list = []

    def clear(self):
        self.list.clear()

    def add(self, level, title, anchor):
        self.list.append((level, title, anchor))

    def extend(self, another):
        self.list.extend(another.list)

    def iter_html(self, max_level=3):
        stack = [0]
        i = 0
        n = len(self.list)
        while i < n:
            x = self.list[i]
            if x[0] > max_level:
                i += 1
                continue
            if x[0] == stack[-1]:
                yield f'<li><a href="#{x[2]}">{x[1]}</a></li>'
                i += 1
            elif x[0] > stack[-1]:
                yield f'<ul class="toc_{x[0]}">'
                stack.append(x[0])
            else:
                yield "</ul>"
                stack.pop()


class MyRenderer(HtmlRenderer):
    def __init__(self, ctx: DocumentContext, toc: TOC):
        self.toc = toc
        self.ctx = ctx
        super().__init__()

    def clear_toc(self):
        self.toc.clear()

    def render_heading(self, token: block_token.Heading) -> str:
        content = token.children[0].content
        anchor = content.replace(" ", "_")
        level = token.level
        link = f'<a class="anchor" href="#{anchor}">#</a>'
        heading = f'<h{level} id="{anchor}">{content} {link}</h{level}>'
        self.toc.add(token.level, content, anchor)
        return heading

    def render_block_code(self, token: block_token.BlockCode) -> str:
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, guess_lexer
        from pygments.formatters import HtmlFormatter

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


@dataclass()
class DocElement:
    content: str

    def render_md(self) -> str:
        pass

    def render_html(self, renderer) -> str:
        md = self.render_md()
        html = renderer.render(mistletoe.Document(md))
        return html


@dataclass()
class LeanCode(DocElement):
    def render_md(self) -> str:
        code = f"```lean-source\n{self.content}\n```"
        return code


@dataclass()
class ModuleMarkdown(DocElement):
    def render_md(self) -> str:
        return self.content


@dataclass()
class Header(DocElement):
    name: str
    level: int = 1

    def render_html(self, renderer) -> str:
        anchor = self.name.replace(" ", "").strip()
        level = self.level
        return f'<a href="#{anchor}"><h{level}>{self.name}</h{level}></a>'


class Document:
    def __init__(self, ctx: DocumentContext):
        self.ctx = ctx
        self.html = ""
        self.toc = TOC()
        self.renderer = MyRenderer(self.ctx, self.toc)
        self.top_module_toc = TOC()

    def add_elements(self, stream):
        for one in self.merge_elements(self.iter_elements(stream)):
            self.html += one.render_html(self.renderer)

    @staticmethod
    def merge_elements(iterable):
        prev_one = next(iterable)
        one: DocElement
        for one in iterable:
            if isinstance(one, type(prev_one)):
                prev_one.content += "\n" + one.content
            else:
                yield prev_one
                prev_one = one
        yield prev_one

    def iter_elements(self, stream):
        element: module.Element
        for element in stream:
            if isinstance(element, module.Comment):
                yield LeanCode(f"{element.content}")
                continue
            if isinstance(element, module.Import):
                yield LeanCode(f"import {element.name}")
                # TODO: add to context
                continue
            if isinstance(element, module.PushScope):
                self.ctx.push_scope(element.name)
                if element.type != "module":
                    yield LeanCode(f"{element.type} {element.name or ''}")
                continue
            if isinstance(element, module.PopScope):
                self.ctx.pop_scope()
                if element.type != "module":
                    yield LeanCode(f"end {element.name or ''}")
                continue
            if isinstance(element, module.ModuleComment):
                content = element.content
                # remove '/-!' and '-/'
                content = content[3:-2]
                yield ModuleMarkdown(content)
                continue
            if isinstance(element, module.Declaration):
                code = ""
                if element.doc_string != "":
                    code += code + "\n"
                if element.modifier != "":
                    code += element.modifier + "\n"
                code += f"{element.type} {element.name}{element.body}\n"
                decl = LeanCode(code)
                yield decl
                continue
            if isinstance(element, module.Code):
                yield LeanCode("\n" + element.content + "\n")
                continue
            raise ValueError(f"Unknown element: {element}")
