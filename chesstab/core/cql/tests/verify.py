# verify.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Verify 'cql -parse' output against chesstab preparation for evaluation.

Subclasses will call the verify(...) method to get 'cql -parse' output.
"""

import unittest
import shlex
import subprocess
import os

# An input file must be specified, but need not exist, with '-parse' option.
_CQL_PREFIX = "cql -input null.pgn -parse -cql "

# Assume any cql output is to the default output file.
_CQL_DEFAULT_OUTPUT = "cqldefault-out.pgn"

_CHESSQL_PREFIX = "cql() "


def is_cql_on_path():
    """Return True if the cql executable can be run."""
    try:
        process = subprocess.run(
            ["cql"],
            stdout=subprocess.DEVNULL,
        )
        return True
    except FileNotFoundError:
        print(
            "".join(
                (
                    "'FileNotFoundError' exception trying to run 'cql':",
                    " is it on PATH?",
                )
            )
        )
        return False


class Verify(unittest.TestCase):
    """Implement verify_*() methods for many unittests."""

    def verify_capture_cql_output(self, string):
        """Verify CQL returncode and return job output."""
        process = subprocess.run(
            shlex.split(_CQL_PREFIX) + [string],
            stdout=subprocess.PIPE,
            encoding="utf8",
        )
        self.assertEqual(process.returncode, 0)
        return process.stdout


if __name__ == "__main__":

    class CQLAssumptions(unittest.TestCase):
        """Confirm operation of cql command with '-cql' option.

        Tests test_03_anynode(), test_04_count_anynode(), and test_05_kall(),
        indicate the 'AnyNode' inserted from 'cqldefault.cql' can be taken
        to have no effect on the validity of the statement in the '-cql'
        argument.
        """

        LEX_PREFIX = "".join(
            (
                "\nParser: lexing file: cqldefault.cql",
                "\ngenCqlNodes::Got return of ntokens: 4",
                "\nPrinting the token stream for file: ",
                "cqldefault.cql",
                "\nTokens: Bottom: 0 size: 4",
                "\nToken 0 of 4<KeywordToken: ",
                '{Line 1, Column 2} "cql">',
                "\nToken 1 of 4<SpecialToken: ",
                '{Line 1, Column 4} "(">',
                "\nToken 2 of 4<SpecialToken: ",
                '{Line 1, Column 5} ")">',
                "\nToken 3 of 4<SpecialToken: ",
                '{Line 1, Column 6} ".">',
            )
        )

        def run_cql(self, string):
            """Return the subprocess run to parse cql statement in string."""
            return subprocess.run(
                shlex.split(_CQL_PREFIX) + [string],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

        def good_request_stdout(self, process):
            """Verify lexer output for 'cql' jobs which succeed."""
            self.assertEqual(
                "".join(
                    (
                        self.LEX_PREFIX,
                        "\n\n<CqlNode  inputfile: null.pgn ",
                        "outputfile: cqldefault-out.pgn ",
                        "searchVariations: 0",
                        "\n CqlNode body: ",
                        "\n <CompoundNode at ",
                    )
                )
                in process.stdout,
                True,
            )

        def test_01_null_string(self):
            """Verify output for '-cql ""' option."""
            process = self.run_cql("")
            self.assertEqual(process.returncode, 1)
            self.assertEqual(
                process.stdout.endswith(
                    "\n\nempty filter following '--cql'\n"
                ),
                True,
            )

        def test_02_bare_count(self):
            """Verify output for '-cql "#"' option."""
            process = self.run_cql("#")
            self.assertEqual(process.returncode, 1)
            self.assertEqual(
                process.stdout.endswith(
                    "".join(
                        (
                            self.LEX_PREFIX,
                            "\n\n\n\nCQL syntax error: ",
                            "Expected either a string filter or a set ",
                            "filter following '#' but the filter parsed ",
                            "was of neither type",
                            "\nUnable to parse the following token: ",
                            "<SpecialToken: ",
                            '{Line 2, Column 1} "}">',
                            "\n\n",
                        )
                    )
                ),
                True,
            )

        def test_03_anynode(self):
            """Verify output for '-cql "."' option."""
            process = self.run_cql(".")
            self.assertEqual(process.returncode, 0)
            self.good_request_stdout(process)
            # Ignore the '0x..' assumed to be an address within process.
            self.assertEqual(
                process.stdout.endswith(
                    "".join(
                        (
                            ": 2 specs:",
                            "\n  <0 of 2: <AnyNode>",
                            "\n  <1 of 2: <AnyNode> CompoundNode>  CqlNode>",
                            "\n",
                        )
                    )
                ),
                True,
            )

        def test_04_count_anynode(self):
            """Verify output for '-cql "#."' option."""
            process = self.run_cql("#.")
            self.assertEqual(process.returncode, 0)
            self.good_request_stdout(process)
            # Ignore the '0x..' assumed to be an address within process.
            self.assertEqual(
                process.stdout.endswith(
                    "".join(
                        (
                            ": 2 specs:",
                            "\n  <0 of 2: <CountSquaresNode <AnyNode>>",
                            "\n  <1 of 2: <AnyNode> CompoundNode>  CqlNode>",
                            "\n",
                        )
                    )
                ),
                True,
            )

        def test_05_kall(self):
            """Verify output for '-cql "k"' option."""
            process = self.run_cql("k")
            self.assertEqual(process.returncode, 0)
            self.good_request_stdout(process)
            # Ignore the '0x..' assumed to be an address within process.
            self.assertEqual(
                process.stdout.endswith(
                    "".join(
                        (
                            ": 2 specs:",
                            "\n  <0 of 2: k<all>",
                            "\n  <1 of 2: <AnyNode> CompoundNode>  CqlNode>",
                            "\n",
                        )
                    )
                ),
                True,
            )

    class VerifyTest(Verify):
        """Unittests for Verify class."""

        def test_verify_capture_cql_output(self):
            """Unittest for returncode 0 from cql job."""
            value = self.verify_capture_cql_output("b")
            self.assertEqual(isinstance(value, str), True)

    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(CQLAssumptions))
    runner().run(loader(VerifyTest))
