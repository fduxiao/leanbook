from dataclasses import dataclass
from ..lean_parser import module
from .context import DocumentContext


@dataclass()
class DocElement:
    def render_md(self) -> str:
        pass


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


class TOC:
    def __init__(self):
        pass


class Document:
    def __init__(self, ctx: DocumentContext):
        self.ctx = ctx
        self.content = ""
        self.toc = TOC()

    def add_elements(self, stream):
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
                # TODO: resolve symbols
                content = element.content
                # remove '/-!' and '-/'
                content = content[3:-2]
                md = ModuleMarkdown(content)
                yield md
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
