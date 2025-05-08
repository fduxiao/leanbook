import unittest
from .helper import ParserHelper
from leanbook.lean_parser.module import decl_parser, Declaration, Fail, SourcePos


class TestModuleParser(unittest.TestCase):
    def test_declarations(self):
        helper = ParserHelper(self, decl_parser)
        helper.assert_parse(
            """def x := 2""",
            Declaration(
                pos=SourcePos(0, 1, 1),
                type="def",
                name="x",
                body=" := 2",
                modifier="",
                doc_string="",
            ),
        )

        helper.assert_parse(
            """instance: Coe Nat String where coe := sorry""",
            Declaration(
                pos=SourcePos(0, 1, 1),
                type="instance",
                name=None,
                body=": Coe Nat String where coe := sorry",
                modifier="",
                doc_string="",
            ),
        )
        helper.assert_parse(
            """@[simp]def id x := x""",
            Declaration(
                pos=SourcePos(7, 1, 8),
                type="def",
                name="id",
                body=" x := x",
                modifier="@[simp]",
                doc_string="",
            ),
        )

        helper.assert_fail("""def := x""")


if __name__ == "__main__":
    unittest.main()
