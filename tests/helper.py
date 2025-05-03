from unittest import TestCase
from leanbook.lean_parser.parser import SourceContext, Fail, BaseParser


class ParserHelper:
    def __init__(self, test_case: TestCase, parser: BaseParser):
        self.test_case = test_case
        self.parser = parser

    def assert_parse(self, x):
        ctx = SourceContext(x)
        parsed = self.parser.parse(ctx)
        self.test_case.assertEqual(parsed, x[: len(parsed)])
        return ctx

    def assert_complete_parse(self, x):
        ctx = self.assert_parse(x)
        self.test_case.assertTrue(ctx.end())

    def assert_fail(self, x):
        self.test_case.assertIsInstance(self.parser.parse_str(x), Fail)
