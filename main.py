import sys
import os # we will need the os module for handling file paths
from lexer.lexer import Lexer
from utils.error_handler import ErrorHandler


def run_file(filepath: str):
    """Read a .mpy file and run the lexer on it."""

    if not os.path.exists(filepath):
        print(f"\n File not found: '{filepath}'")
        print(f"   Make sure the path is correct.\n")
        sys.exit(1)

    with open(filepath, 'r') as f:
        source = f.read()

    print(f"  MicroPy Compiler — Lexical Analysis")
    print(f"  File: {filepath}")

    # this error hanlder interface will be share acroll all compilation phases
    errors = ErrorHandler()

    # run the lexer
    lexer  = Lexer(source, errors)
    tokens = lexer.tokenize()

    # print the token table for the tokens that our lexer has collected
    print(f"\n  {'TOKEN TYPE':<14} | {'VALUE':<35} | LINE")
    for tok in tokens:
        if tok.type.value not in ("EOF", "NEWLINE"):
            print(f"  {tok.type.value:<14} | {repr(tok.value):<35} | {tok.line}")

    """  no need to do summary since we alrady know the code works and what is expected of the code
    # print summary
    print(f"\n{'─' * 60}")
    visible = [t for t in tokens if t.type.value not in ("EOF", "NEWLINE")]
    print(f"  Total tokens: {len(visible)}")
    errors.summary()
    print(f"{'─' * 60}\n")
    """
    errors.summary()



if __name__ == "__main__":
    # guys i made it to accept a file path as parameter bytheway so we can always work with custom files.
    # otherwise fall back to the default sample
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        run_file("samples/calculator.mpy")