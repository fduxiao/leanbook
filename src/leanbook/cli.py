import argparse


def build(args):
    print(args)


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

    build_parser = sub_cmds.add_parser("build", description="")
    build_parser.set_defaults(func=build)
    build_parser.add_argument("path", default=".", nargs="?")
    build_parser.add_argument("--output", "-o", default=None)

    args = parser.parse_args()
    exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
