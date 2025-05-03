import unittest

from .helper import ParserHelper


from leanbook.lean_parser.parser import SourceContext, Fail, Pos
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
                self.assertTrue(text[pos.index :].startswith(content))

        assert_parse(token.ModuleComment, pos=Pos(2, 1, 3), content="/-!aaa-/")
        assert_parse(token.Command, pos=Pos(11, 1, 12), content="import")
        assert_parse(token.Identifier, pos=Pos(18, 1, 19), content="something")
        assert_parse(token.Code, pos=Pos(28, 2, 1), content="\\abc")
        assert_parse(token.Command, pos=Pos(33, 3, 1), content="import")
        assert_parse(token.Identifier, pos=Pos(40, 3, 8), content="a.else")
        assert_parse(token.DocString, pos=Pos(48, 4, 2), content="/--doc string-/")
        assert_parse(token.Command, pos=Pos(63, 4, 17), content="def")
        assert_parse(token.Identifier, pos=Pos(67, 4, 21), content="a")
        assert_parse(token.Code, pos=Pos(69, 4, 23), content=':= 2 \n"/-" yz')
        assert_parse(token.Comment, pos=Pos(83, 5, 9), content="/- comme/--/nt-/")
        assert_parse(token.Identifier, pos=Pos(100, 5, 26), content="xz")
        assert_parse(token.Command, pos=Pos(104, 5, 30), content="#check")
        assert_parse(token.Identifier, pos=Pos(111, 5, 37), content="x")
        assert_parse(token.Code, pos=Pos(113, 5, 39), content="= 2")
        assert_parse(token.Command, pos=Pos(117, 6, 1), content="section")
        assert_parse(token.Identifier, pos=Pos(125, 6, 9), content="abc")
        assert_parse(token.Command, pos=Pos(129, 6, 13), content="end")
        assert_parse(token.Identifier, pos=Pos(133, 6, 17), content="abc")
        assert_parse(token.DeclModifier, pos=Pos(138, 6, 22), content="@[simp]")

        self.assertFalse(ctx.end())
        assert_parse(token.EOF, pos=Pos(146, 6, 30))
        self.assertTrue(ctx.end())

        self.assertEqual(ctx.pos.index, 146)
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
