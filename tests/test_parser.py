import unittest
from leanbook.lean_parser.parser import *
from leanbook.lean_parser import token, lexer


class TestParser(unittest.TestCase):
    def test_base_parser(self):
        parser = BaseParser()
        r = parser.parse_str("aabbccdd")
        self.assertIs(r, Fail)

    def test_or_else(self):
        p1 = String("aa")
        p2 = String("ab")
        p3 = String("bb")
        parser = p1 | p2 | p3
        self.assertIs(Fail, parser.parse_str("a"))
        self.assertEqual("aa", parser.parse_str("aa"))
        self.assertEqual("ab", parser.parse_str("ab"))
        self.assertEqual("bb", parser.parse_str("bb"))

        cs = SourceContext("aabbab")
        self.assertEqual("aa", parser.parse(cs))
        self.assertEqual(cs.look(2), "bb")
        self.assertEqual("bb", parser.parse(cs))
        self.assertEqual(cs.look(2), "ab")
        self.assertEqual("ab", parser.parse(cs))
        self.assertIs(cs.look(2), None)
        self.assertTrue(cs.end())

    def test_many_parser(self):
        p1 = String("aa")
        p2 = String("ab")
        p3 = String("bb")

        parser = Many(p1 | p2 | p3)
        cs = SourceContext("aabbccdd")
        self.assertListEqual(["aa", "bb"], parser.parse(cs))
        self.assertEqual("ccdd", cs.rest())

    def assert_parse(self, parser, x):
        ctx = SourceContext(x)
        parsed = parser.parse(ctx)
        self.assertEqual(parsed, x[: len(parsed)])
        return ctx

    def assert_complete_parse(self, parser, x):
        ctx = self.assert_parse(parser, x)
        self.assertTrue(ctx.end())

    def assert_fail(self, parser, x):
        self.assertIs(parser.parse_str(x), Fail)

    def test_parse_block_comment(self):
        parser = lexer.BlockComment()

        self.assert_complete_parse(parser, "/--/")
        self.assert_fail(parser, "/-")
        ctx = self.assert_parse(parser, "/--/-/")
        self.assertEqual(ctx.rest(), "-/")

        self.assert_complete_parse(parser, "/- a b-/")
        self.assert_complete_parse(parser, "/- /-a b-/-/")

    def test_string(self):
        parser = StrLiteral()
        self.assert_complete_parse(parser, r'""')
        self.assert_complete_parse(parser, r'"a\"\'"')
        ctx = self.assert_parse(parser, r'"abc"def')
        self.assertEqual(ctx.rest(), "def")

    def test_code(self):
        parser = lexer.CodeParser()
        self.assert_complete_parse(parser, r"abcd")
        ctx = self.assert_parse(parser, r'abcd "\"/-" /-')
        self.assertEqual(ctx.rest(), "/-")

    def test_lexer(self):
        parser = lexer.BlockParser()
        ctx = SourceContext(r'/-!aaa-/ /--doc string-/def "/-" yz /- comment-/ xz  ')
        result: list = parser.parse(ctx)
        self.assertTrue(ctx.end())
        self.assertListEqual(
            result,
            [
                token.ModuleComment(content="/-!aaa-/"),
                token.DocString(content="/--doc string-/"),
                token.Code(content='def "/-" yz', doc_string=""),
                token.Comment(content="/- comment-/"),
                token.Code(content="xz", doc_string=""),
            ],
        )


if __name__ == "__main__":
    unittest.main()
