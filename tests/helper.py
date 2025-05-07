from unittest import TestCase
from leanbook.lean_parser.parser import SourceContext, Fail, BaseParser


class ParserHelper:
    def __init__(self, test_case: TestCase, parser: BaseParser):
        self.test_case = test_case
        self.parser = parser

    def assert_parse(self, text, result=None):
        ctx = SourceContext(text)
        parsed = self.parser.parse(ctx)
        if result is None:
            result = text[: len(parsed)]
        self.test_case.assertEqual(parsed, result)
        return ctx

    def assert_complete_parse(self, text, result=None):
        ctx = self.assert_parse(text, result)
        self.test_case.assertTrue(ctx.end())

    def assert_fail(self, text):
        with self.test_case.assertRaises(Fail):
            self.parser.parse_str(text)
