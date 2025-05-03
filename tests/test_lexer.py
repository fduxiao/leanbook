import unittest

from .helper import ParserHelper


from leanbook.lean_parser.parser import SourceContext, Fail
from leanbook.lean_parser import token, lexer


class TestLexer(unittest.TestCase):
    def test_code(self):
        parser = lexer.CodeParser()
        helper = ParserHelper(self, parser)
        helper.assert_complete_parse(r"abcd")
        ctx = helper.assert_parse(r'abcd "\"/-" /-')
        self.assertEqual(ctx.rest(), "/-")

    def test_parse_block_comment(self):
        parser = lexer.BlockComment()
        helper = ParserHelper(self, parser)

        helper.assert_complete_parse("/--/")
        helper.assert_fail("/-")
        ctx = helper.assert_parse("/--/-/")
        self.assertEqual(ctx.rest(), "-/")

        helper.assert_complete_parse("/- a b-/")
        helper.assert_complete_parse("/- /-a b-/-/")

    def test_parser_line_comment(self):
        parser = lexer.LineComment()
        helper = ParserHelper(self, parser)

        helper.assert_complete_parse("-- abcd\n")
        helper.assert_complete_parse("--")
        helper.assert_complete_parse("--\n")

    def test_lexer(self):
        parser = lexer.any_token
        text = (
            "  /-!aaa-/ import something\n"
            "\\abc\n"
            "import a.else\n"
            " /--doc string-/def a := 2 \n"
            '"/-" yz /- comme/--/nt-/ xz  '
            "#check x = 2\n"
            "section abc end abc  "
            "@[simp] "
        )
        ctx = SourceContext(text)

        def assert_parse(token_type, pos, content=None):
            tk = parser.parse(ctx)
            self.assertEqual(tk, token_type(pos=pos, content=content))
            if content is None:
                self.assertIsNone(tk.content)
            else:
                self.assertTrue(text[pos:].startswith(content))

        assert_parse(token.ModuleComment, pos=2, content="/-!aaa-/")
        assert_parse(token.Command, pos=11, content="import")
        assert_parse(token.Identifier, pos=18, content="something")
        assert_parse(token.Code, pos=28, content="\\abc")
        assert_parse(token.Command, pos=33, content="import")
        assert_parse(token.Identifier, pos=40, content="a.else")
        assert_parse(token.DocString, pos=48, content="/--doc string-/")
        assert_parse(token.Command, pos=63, content="def")
        assert_parse(token.Identifier, pos=67, content="a")
        assert_parse(token.Code, pos=69, content=':= 2 \n"/-" yz')
        assert_parse(token.Comment, pos=83, content="/- comme/--/nt-/")
        assert_parse(token.Identifier, pos=100, content="xz")
        assert_parse(token.Command, pos=104, content="#check")
        assert_parse(token.Identifier, pos=111, content="x")
        assert_parse(token.Code, pos=113, content="= 2")
        assert_parse(token.Command, pos=117, content="section")
        assert_parse(token.Identifier, pos=125, content="abc")
        assert_parse(token.Command, pos=129, content="end")
        assert_parse(token.Identifier, pos=133, content="abc")
        assert_parse(token.DeclModifier, pos=138, content="@[simp]")

        self.assertFalse(ctx.end())
        assert_parse(token.EOF, pos=146)
        self.assertTrue(ctx.end())

        self.assertEqual(ctx.pos, 146)
        self.assertEqual(len(ctx.text), 146)

    def test_command(self):
        self.assertEqual(lexer.identifier_parser.parse_str("def a := 2"), "def")
        self.assertEqual(lexer.command_parser.parse_str("def a := 2"), "def")

        self.assertEqual(lexer.identifier_parser.parse_str("defa x y z"), "defa")
        self.assertIsInstance(lexer.command_parser.parse_str("defa x y z"), Fail)

        self.assertEqual(lexer.identifier_parser.parse_str("def.a x y z"), "def.a")
        self.assertIsInstance(lexer.command_parser.parse_str("def.a x y z"), Fail)

        self.assertEqual(lexer.identifier_parser.parse_str("def_a x y z"), "def_a")
        self.assertIsInstance(lexer.command_parser.parse_str("def_a x y z"), Fail)

        # This may be fixed later
        self.assertEqual(lexer.identifier_parser.parse_str("0defa x y z"), "0defa")


if __name__ == "__main__":
    unittest.main()
