# ─────────────────────────────────────────────────────────────
#  main.py — Entry point for the MicroPy compiler
#  Usage:
#    python main.py                        ← default sample
#    python main.py samples/calculator.mpy ← specific file
# ─────────────────────────────────────────────────────────────

import sys
import os
from lexer.lexer import Lexer
from parser.parser import Parser
from parser.nodes import print_ast
from utils.error_handler import ErrorHandler


def run_file(filepath: str):
    if not os.path.exists(filepath):
        print(f"\n❌ File not found: '{filepath}'\n")
        sys.exit(1)

    with open(filepath, 'r') as f:
        source = f.read()

    print(f"\n{'─' * 60}")
    print(f"  MicroPy Compiler")
    print(f"  File: {filepath}")
    print(f"{'─' * 60}")

    errors = ErrorHandler()

    # ── Phase 1: Lexical Analysis ──
    print(f"\n  PHASE 1 — Lexical Analysis")
    print(f"  {'─' * 50}")
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

    # ── Phase 2: Parsing ──
    print(f"\n  PHASE 2 — Parsing (AST)")
    print(f"  {'─' * 50}")
    parser = Parser(tokens, errors)
    ast    = parser.parse()

    print_ast(ast)

    print(f"\n{'─' * 60}")
    errors.summary()
    print(f"{'─' * 60}\n")


if __name__ == "__main__":
    run_file(sys.argv[1] if len(sys.argv) > 1 else "samples/calculator.mpy")