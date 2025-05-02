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

    def test_lexer(self):
        parser = lexer.lexer
        text = (
            "  /-!aaa-/ import something\n"
            "\\abc\n"
            "import a.else\n"
            " /--doc string-/def a := 2 \n"
            '"/-" yz /- comme/--/nt-/ xz  '
            "section abc end abc  "
        )
        ctx = SourceContext(text)
        tk = parser.parse(ctx)
        self.assertEqual(tk, token.ModuleComment(pos=2, content="/-!aaa-/"))
        self.assertTrue(text[tk.pos :].startswith("/-!aaa-/"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Keyword(pos=11, word="import"))
        self.assertTrue(text[tk.pos :].startswith("import"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Word(pos=18, word="something"))
        self.assertTrue(text[tk.pos :].startswith("something"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Code(pos=28, content="\\abc"))
        self.assertTrue(text[tk.pos :].startswith("\\abc"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Keyword(pos=33, word="import"))
        self.assertTrue(text[tk.pos :].startswith("import"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Word(pos=40, word="a.else"))
        self.assertTrue(text[tk.pos :].startswith("a.else"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.DocString(pos=48, content="/--doc string-/"))
        self.assertTrue(text[tk.pos :].startswith("/--doc string-/"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Keyword(pos=63, word="def"))
        self.assertTrue(text[tk.pos :].startswith("def"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Word(pos=67, word="a"))
        self.assertTrue(text[tk.pos :].startswith("a"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Code(pos=69, content=':= 2 \n"/-" yz'))
        self.assertTrue(text[tk.pos :].startswith(':= 2 \n"/-" yz'))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Comment(pos=83, content="/- comme/--/nt-/"))
        self.assertTrue(text[tk.pos :].startswith("/- comme/--/nt-/"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Word(pos=100, word="xz"))
        self.assertTrue(text[tk.pos :].startswith("xz"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Keyword(pos=104, word="section"))
        self.assertTrue(text[tk.pos :].startswith("section"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Word(pos=112, word="abc"))
        self.assertTrue(text[tk.pos :].startswith("abc"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Keyword(pos=116, word="end"))
        self.assertTrue(text[tk.pos :].startswith("end"))

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.Word(pos=120, word="abc"))
        self.assertTrue(text[tk.pos :].startswith("abc"))

        # spaces at the end
        self.assertFalse(ctx.end())

        tk = parser.parse(ctx)
        self.assertEqual(tk, token.End(pos=125))
        self.assertTrue(ctx.end())

    def test_word(self):
        self.assertEqual(lexer.word.parse_str("def a := 2"), "def")
        self.assertEqual(lexer.keyword.parse_str("def a := 2"), "def")

        self.assertEqual(lexer.word.parse_str("defa x y z"), "defa")
        self.assertIs(lexer.keyword.parse_str("defa x y z"), Fail)

        self.assertEqual(lexer.word.parse_str("def.a x y z"), "def.a")
        self.assertIs(lexer.keyword.parse_str("def.a x y z"), Fail)

        # This may be fixed later
        self.assertEqual(lexer.word.parse_str("0defa x y z"), "0defa")


if __name__ == "__main__":
    unittest.main()
