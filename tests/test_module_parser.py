import unittest
from leanbook.lean_parser.module import decl_parser, Declaration, Fail, Pos


class TestModuleParser(unittest.TestCase):
    def test_declarations(self):
        self.assertEqual(
            decl_parser.parse_str("""def x := 2"""),
            Declaration(
                pos=Pos(0, 1, 1),
                type="def",
                name="x",
                body=":= 2",
                modifier="",
                doc_string="",
            ),
        )

        self.assertEqual(
            decl_parser.parse_str("""instance: Coe Nat String where coe := sorry"""),
            Declaration(
                pos=Pos(0, 1, 1),
                type="instance",
                name=None,
                body=": Coe Nat String where coe := sorry",
                modifier="",
                doc_string="",
            ),
        )
        self.assertEqual(
            decl_parser.parse_str("""@[simp]def id x := x"""),
            Declaration(
                pos=Pos(7, 1, 8),
                type="def",
                name="id",
                body="",
                modifier="@[simp]",
                doc_string="",
            ),
        )

        self.assertIsInstance(decl_parser.parse_str("""def := x"""), Fail)


if __name__ == "__main__":
    unittest.main()
