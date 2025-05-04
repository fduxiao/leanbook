from dataclasses import dataclass

import mistletoe
from mistletoe import block_token
from mistletoe.html_renderer import HtmlRenderer


from ..lean_parser import module
from .context import DocumentContext


class TOC:
    def __init__(self):
        self.list = []

    def add(self, level, title, anchor):
        self.list.append((level, title, anchor))

    def extend(self, another):
        self.list.extend(another.list)


class MyRenderer(HtmlRenderer):
    def __init__(self):
        self.toc = TOC()
        super().__init__()

    def render_heading(self, token: block_token.Heading) -> str:
        content = token.children[0].content
        result = super().render_heading(token)
        anchor = content.replace(" ", "_")
        result = f'<a href="#{anchor}">{result}</a>'
        self.toc.add(token.level, content, anchor)
        return result


@dataclass()
class DocElement:
    toc = None

    def render_md(self) -> str:
        pass

    def render_html(self) -> str:
        md = self.render_md()
        renderer = MyRenderer()
        html = renderer.render(mistletoe.Document(md))
        self.toc = renderer.toc
        return html


@dataclass()
class LeanCode(DocElement):
    content: str

    def render_md(self) -> str:
        code = f"```lean\n{self.content}\n```"
        return code


@dataclass()
class ModuleMarkdown(DocElement):
    content: str

    def render_md(self) -> str:
        return self.content


@dataclass()
class Header(DocElement):
    name: str
    level: int = 1

    def render_html(self) -> str:
        anchor = self.name.replace(" ", "").strip()
        level = self.level
        return f'<a href="#{anchor}"><h{level}>{self.name}</h{level}></a>'


class Document:
    def __init__(self, ctx: DocumentContext):
        self.ctx = ctx
        self.html = ""
        self.toc = TOC()
        self.top_module_toc = TOC()

    def add_elements(self, stream):
        for one in self.iter_elements(stream):
            self.html += one.render_html()
            if one.toc is not None:
                self.toc.extend(one.toc)

    def iter_elements(self, stream):
        element: module.Element
        for element in stream:
            if isinstance(element, module.Comment):
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
                code += f"{element.type} {element.name}{element.body}"
                decl = LeanCode(code)
                yield decl
                continue
            raise ValueError(f"Unknown element: {element}")
