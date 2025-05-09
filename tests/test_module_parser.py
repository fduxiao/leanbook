import unittest
from .helper import ParserHelper
from leanbook.lean_parser.module import (
    decl_parser,
    Declaration,
    SourcePos,
    module_parser,
    Module,
    Namespace,
    Section,
)


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

    def test_module(self):
        text = """
        def x := 2
        namespace abc
            section
                def y := 3
            end
            section xyz
                def z := "end"
            end xyz
        end abc
        """
        result: Module = module_parser.parse_str(text)
        self.assertEqual(
            result,
            Module(
                pos=SourcePos(index=0, line=1, col=1),
                end_pos=SourcePos(index=204, line=11, col=9),
                name=None,
                elements=[
                    Declaration(
                        pos=SourcePos(index=9, line=2, col=9),
                        type="def",
                        name="x",
                        body=" := 2",
                        modifier="",
                        doc_string="",
                    ),
                    Namespace(
                        pos=SourcePos(index=28, line=3, col=9),
                        end_pos=SourcePos(index=195, line=10, col=16),
                        name="abc",
                        elements=[
                            Section(
                                pos=SourcePos(index=54, line=4, col=13),
                                end_pos=SourcePos(index=104, line=6, col=16),
                                name=None,
                                elements=[
                                    Declaration(
                                        pos=SourcePos(index=78, line=5, col=17),
                                        type="def",
                                        name="y",
                                        body=" := 3",
                                        modifier="",
                                        doc_string="",
                                    )
                                ],
                            ),
                            Section(
                                pos=SourcePos(index=117, line=7, col=13),
                                end_pos=SourcePos(index=179, line=9, col=20),
                                name="xyz",
                                elements=[
                                    Declaration(
                                        pos=SourcePos(index=145, line=8, col=17),
                                        type="def",
                                        name="z",
                                        body=' := "end"',
                                        modifier="",
                                        doc_string="",
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )


if __name__ == "__main__":
    unittest.main()
