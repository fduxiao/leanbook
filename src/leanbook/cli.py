import argparse
from pathlib import Path

from .source_tree import SourceTree
from .target_tree import TargetTree


def parse_path(args):
    path = Path(args.path)
    output = args.output
    if output is None:
        output = path / ".lake/build/doc"
    else:
        output = Path(output)
    return path, output


def build(args):
    path, output = parse_path(args)
    source_tree = SourceTree(path)
    source_tree.build_tree()
    target_tree = TargetTree(source_tree, output)
    target_tree.render_all()


def serve(args):
    print(args)


def main():
    parser = argparse.ArgumentParser(
        description="build an HTML book from a lean package"
    )
    parser.set_defaults(func=lambda _: parser.print_help() or -1)

    sub_cmds = parser.add_subparsers(description="", title="available commands")
    serve_parser = sub_cmds.add_parser("serve", description="run an HTTP server")
    serve_parser.set_defaults(func=serve)
    serve_parser.add_argument("path", default=".")
    serve_parser.add_argument("--output", "-o", default=None)

    build_parser = sub_cmds.add_parser("build", description="")
    build_parser.set_defaults(func=build)
    build_parser.add_argument("path", default=".", nargs="?")
    build_parser.add_argument("--output", "-o", default=None)

    args = parser.parse_args()
    exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
