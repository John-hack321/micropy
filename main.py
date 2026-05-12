#  main.py — Entry point for the MicroPy compiler
#  Usage:
#    python main.py                        ← default sample
#    python main.py samples/calculator.mpy ← specific file

import sys
import os
from lexer.lexer import Lexer
from parser.parser import Parser
from parser.nodes import print_ast
from semantic.analyser import SemanticAnalyser, print_symbol_table
from codegen.icg import ICG, print_quads
from utils.error_handler import ErrorHandler


def run_file(filepath: str):
    if not os.path.exists(filepath):
        print(f"\\File not found: '{filepath}'\n") # if file is not found it will default to the default test one
        sys.exit(1)

    with open(filepath, 'r') as f:
        source = f.read()

    # print(f"\n{'─' * 60}") no need for this upper boundary
    # print("group 18 micropy compiler: lexer and parser demonstaration ")
    # print(f"  MicroPy Compiler")
    # print(f"  File: {filepath}")
    # print(f"{'─' * 60}") 

    errors = ErrorHandler()

    # Phase 1: Lexical Analysis
    print(f"\n  PHASE 1 — Lexical Analysis \n \n")
    # print(f"  {'─' * 50}")
    lexer  = Lexer(source, errors)
    tokens = lexer.tokenize()

    print(f"  {'TOKEN TYPE':<14} | {'VALUE':<35} | LINE")
    # print(f"  {'─' * 56}")
    for tok in tokens:
        if tok.type.value not in ("EOF", "NEWLINE"):
            print(f"  {tok.type.value:<14} | {repr(tok.value):<35} | {tok.line}")

    visible = [t for t in tokens if t.type.value not in ("EOF", "NEWLINE")]
    print(f"\n  Total tokens: {len(visible)}")

    if errors.has_errors():
        errors.summary()
        return

    # Phase 2: Parsing
    print(f"\n \n PHASE 2 : Parser => Parsing (AST)")
    print(f"  {'─' * 50}")
    parser = Parser(tokens, errors)
    ast    = parser.parse()

    print_ast(ast)

    # print(f"\n{'─' * 60}") no need for this bound too 
    if errors.has_errors():
        errors.summary() # since it is nolonger the final phase we need not to print summary here
        return 

    #print(f"{'─' * 60}\n") no need for this lower bound

    # Phase 3: Semantic Analysis
    print(f" \n \n \n PHASE 3 — Semantic Analysis (Symbol Table & Checks)")
    semantic_analyser = SemanticAnalyser(errors)
    symbol_table = semantic_analyser.analyse(ast)
    print_symbol_table(symbol_table)

    if errors.has_errors():
        errors.summary()
        return

    # Phase 4: Intermediate Code Generation
    print(f" \n \n \n PHASE 4 — Intermediate Code Generation  (Quadruples)")
    icg   = ICG()
    quads = icg.generate(ast)
    print_quads(quads)

    print(f"\n{'-' * 62}")
    errors.summary()



if __name__ == "__main__":
    run_file(sys.argv[1] if len(sys.argv) > 1 else "samples/calculator.mpy")