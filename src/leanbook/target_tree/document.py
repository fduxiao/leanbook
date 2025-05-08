from dataclasses import dataclass

from ..lean_parser import module
from .context import DocumentContext
from .md_render import MDRender, parse_md


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


@dataclass()
class DocElement:
    content: str

    def render_md(self) -> str:
        pass

    def render_html(self, renderer) -> str:
        md = self.render_md()
        html = renderer.render(parse_md(md))
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
        self.renderer = MDRender(self.ctx, self.toc)
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
                yield LeanCode(element.content)
                continue
            raise ValueError(f"Unknown element: {element}")
