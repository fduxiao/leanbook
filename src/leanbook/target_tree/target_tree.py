"""Target tree"""

from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape


from ..source_tree import SourceTree, SourceFile
from .context import DocumentContext
from .document import Document


class TemplateRenderer:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("leanbook.target_tree"), autoescape=select_autoescape()
        )

    def render(self, path, **kwargs) -> str:
        template = self.env.get_template(f"{path}")
        return template.render(**kwargs)

    def render_index(self, top_modules: dict[Path, str]) -> str:
        data = []
        for rel_path, name in top_modules.items():
            data.append({"href": f"./lean_modules/{name}.html", "name": rel_path.name})
        return self.render("index.html.jinja2", top_modules=data)

    def render_module(self, title, toc, toc_hint, body):
        def opt_href(x, default=None):
            if x is None:
                if default is None:
                    return ' class="disabled" '
                return f'href="{default}"'
            return f'href="{x}.html"'

        up_href = opt_href(toc_hint.up, "../index.html")
        prev_href = opt_href(toc_hint.prev)
        next_href = opt_href(toc_hint.next)

        return self.render(
            "module.html.jinja2",
            title=title,
            toc=toc.iter_html(max_level=3),
            body=body,
            up=up_href,
            prev=prev_href,
            next=next_href,
        )


class TargetTree:
    def __init__(self, source_tree: SourceTree, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.source_tree = source_tree
        self.ctx = DocumentContext(source_tree)
        self.renderer = TemplateRenderer()

    def get_path(self, rel_path):
        return self.output_dir / rel_path

    def render_module(self, rel_path: Path):
        print("rendering", rel_path)
        source_file: SourceFile = self.source_tree.file_map[rel_path]
        toc_hint = self.source_tree.get_toc_hint(source_file.module_name)
        document = Document(self.ctx)
        document.add_elements(source_file.module.element_stream())
        module_name = source_file.module_name
        body = document.html
        toc = document.toc
        html = self.renderer.render_module(module_name, toc, toc_hint, body)
        with open(
            self.output_dir / "lean_modules" / f"{module_name}.html", "w"
        ) as file:
            file.write(html)

    def render_all(self):
        self.render_index()
        for rel_path in self.source_tree.file_map:
            self.render_module(rel_path)

    def render_and_write(self, path, **kwargs):
        with open(self.output_dir / path, "w") as file:
            file.write(self.renderer.render(path, **kwargs))

    def render_index(self):
        """render index.html and file system structures"""
        (self.output_dir / "lean_modules").mkdir(exist_ok=True, parents=True)
        (self.output_dir / "styles").mkdir(exist_ok=True, parents=True)
        # copy style and js files
        self.render_and_write("styles/style.css")
        # index
        with open(self.output_dir / "index.html", "w") as file:
            file.write(self.renderer.render_index(self.source_tree.top_modules))
