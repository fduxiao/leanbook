import unittest

from .helper import ParserHelper


from leanbook.lean_parser.parser import SourceContext, Fail, SourcePos
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

        assert_parse(token.ModuleComment, pos=SourcePos(2, 1, 3), content="/-!aaa-/")
        assert_parse(token.Command, pos=SourcePos(11, 1, 12), content="import")
        assert_parse(token.Identifier, pos=SourcePos(18, 1, 19), content="something")
        assert_parse(token.Code, pos=SourcePos(28, 2, 1), content="\\abc")
        assert_parse(token.Command, pos=SourcePos(33, 3, 1), content="import")
        assert_parse(token.Identifier, pos=SourcePos(40, 3, 8), content="a.else")
        assert_parse(
            token.DocString, pos=SourcePos(48, 4, 2), content="/--doc string-/"
        )
        assert_parse(token.Command, pos=SourcePos(63, 4, 17), content="def")
        assert_parse(token.Identifier, pos=SourcePos(67, 4, 21), content="a")
        assert_parse(token.Code, pos=SourcePos(69, 4, 23), content=':= 2 \n"/-" yz')
        assert_parse(token.Comment, pos=SourcePos(83, 5, 9), content="/- comme/--/nt-/")
        assert_parse(token.Identifier, pos=SourcePos(100, 5, 26), content="xz")
        assert_parse(token.Command, pos=SourcePos(104, 5, 30), content="#check")
        assert_parse(token.Identifier, pos=SourcePos(111, 5, 37), content="x")
        assert_parse(token.Code, pos=SourcePos(113, 5, 39), content="= 2")
        assert_parse(token.Command, pos=SourcePos(117, 6, 1), content="section")
        assert_parse(token.Identifier, pos=SourcePos(125, 6, 9), content="abc")
        assert_parse(token.Command, pos=SourcePos(129, 6, 13), content="end")
        assert_parse(token.Identifier, pos=SourcePos(133, 6, 17), content="abc")
        assert_parse(token.DeclModifier, pos=SourcePos(138, 6, 22), content="@[simp]")

        self.assertFalse(ctx.end())
        assert_parse(token.EOF, pos=SourcePos(146, 6, 30))
        self.assertTrue(ctx.end())

        self.assertEqual(ctx.pos.index, 146)
        self.assertEqual(len(ctx.text), 146)

    def test_command(self):
        helper = ParserHelper(self, lexer.command_parser)
        helper.assert_parse("def a := 2", "def")
        helper.assert_fail("defa x y z")
        helper.assert_fail("def.a x y z")
        helper.assert_fail("def_a x y z")

    def test_identifier(self):
        self.assertEqual(lexer.identifier_parser.parse_str("def a := 2"), "def")
        self.assertEqual(lexer.identifier_parser.parse_str("defa x y z"), "defa")
        self.assertEqual(lexer.identifier_parser.parse_str("def.a x y z"), "def.a")
        self.assertEqual(lexer.identifier_parser.parse_str("def_a x y z"), "def_a")
        self.assertEqual(lexer.identifier_parser.parse_str("def_a.{u} x y z"), "def_a")
        # These should raise an error, but them won't happen in our case
        self.assertEqual(lexer.identifier_parser.parse_str("def.a. x y z"), "def.a")
        self.assertEqual(lexer.identifier_parser.parse_str("0defa x y z"), "0defa")


if __name__ == "__main__":
    unittest.main()
