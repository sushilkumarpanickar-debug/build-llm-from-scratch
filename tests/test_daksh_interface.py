import unittest
from tempfile import TemporaryDirectory

from daksh.interface import DAKSH, DAKSHConfig


class DAKSHCommandParsingTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.daksh = DAKSH(DAKSHConfig(data_directory=self.directory.name))

    def tearDown(self):
        self.directory.cleanup()

    def test_question_containing_do_is_not_an_execution_command(self):
        command, params = self.daksh._parse_input("What does DAKSH use?")
        self.assertEqual(command, "general_query")
        self.assertEqual(params["query"], "What does DAKSH use?")

    def test_explicit_leading_run_verb_creates_an_objective(self):
        command, params = self.daksh._parse_input("Run a local analysis")
        self.assertEqual(command, "execute_objective")
        self.assertEqual(params["objective"], "a local analysis")


if __name__ == "__main__":
    unittest.main()
