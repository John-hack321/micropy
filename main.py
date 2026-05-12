#  main.py — Entry point for the MicroPy compiler
import sys
import os
from lexer.lexer import Lexer
from parser.parser import Parser
from parser.nodes import print_ast
from codegen.icg import ICG, print_quads
from utils.error_handler import ErrorHandler


def run_file(filepath: str):
    if not os.path.exists(filepath):
        print(f"\nFile not found: '{filepath}'\n")
        sys.exit(1)

    with open(filepath, 'r') as f:
        source = f.read()

    errors = ErrorHandler()

    # Phase 1: Lexical Analysis
    print(f"\n{'═' * 62}")
    print(f"  PHASE 1 — Lexical Analysis")
    print(f"{'═' * 62}\n")
    lexer  = Lexer(source, errors)
    tokens = lexer.tokenize()
    print(f"  {'TOKEN TYPE':<14} | {'VALUE':<35} | LINE")
    print(f"  {'─' * 56}")
    for tok in tokens:
        if tok.type.value not in ("EOF", "NEWLINE"):
            print(f"  {tok.type.value:<14} | {repr(tok.value):<35} | {tok.line}")
    visible = [t for t in tokens if t.type.value not in ("EOF", "NEWLINE")]
    print(f"\n  Total tokens: {len(visible)}")

    if errors.has_errors():
        errors.summary()
        return

    # Phase 2: Syntax Analysis
    print(f"\n{'═' * 62}")
    print(f"  PHASE 2 — Syntax Analysis  (Parse Tree / AST)")
    print(f"{'═' * 62}\n")
    parser = Parser(tokens, errors)
    ast    = parser.parse()
    print_ast(ast)

    if errors.has_errors():
        errors.summary()
        return

    # Phase 3: Intermediate Code Generation
    print(f"\n{'═' * 62}")
    print(f"  PHASE 3 — Intermediate Code Generation  (Quadruples)")
    print(f"{'═' * 62}\n")
    icg   = ICG()
    quads = icg.generate(ast)
    print_quads(quads)

    print(f"\n{'═' * 62}")
    errors.summary()


if __name__ == "__main__":
    run_file(sys.argv[1] if len(sys.argv) > 1 else "samples/calculator.mpy")