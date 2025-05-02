import unittest
from leanbook.lean_parser.parser import *


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

    def test_parse_block_comment(self):
        parser = BlockComment()

        def assert_parse(x):
            _ctx = SourceContext(x)
            parsed = parser.parse(_ctx)
            self.assertEqual(parsed, x[: len(parsed)])
            return _ctx

        def assert_complete_parse(x):
            _ctx = assert_parse(x)
            self.assertTrue(_ctx.end())

        def assert_fail(x):
            self.assertIs(parser.parse_str(x), Fail)

        assert_complete_parse("/--/")
        assert_fail("/-")
        ctx = assert_parse("/--/-/")
        self.assertEqual(ctx.rest(), "-/")

        assert_complete_parse("/- a b-/")
        assert_complete_parse("/- /-a b-/-/")


if __name__ == "__main__":
    unittest.main()
