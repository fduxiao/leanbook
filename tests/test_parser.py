import unittest
from .helper import ParserHelper

from leanbook.lean_parser.parser import *


class TestParser(unittest.TestCase):
    def test_base_parser(self):
        helper = ParserHelper(self, BaseParser())
        helper.assert_fail("aabbccdd")

    def test_or_else(self):
        p1 = String("aa")
        p2 = String("ab")
        p3 = String("bb")
        parser = p1 | p2 | p3
        helper = ParserHelper(self, parser)
        helper.assert_fail("a")
        helper.assert_complete_parse("aa")
        helper.assert_complete_parse("ab")
        helper.assert_complete_parse("bb")

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

    def test_string(self):
        parser = StrLiteral()
        helper = ParserHelper(self, parser)
        helper.assert_complete_parse(r'""')
        helper.assert_complete_parse(r'"a\"\'"')
        ctx = helper.assert_parse(r'"abc"def')
        self.assertEqual(ctx.rest(), "def")


if __name__ == "__main__":
    unittest.main()
