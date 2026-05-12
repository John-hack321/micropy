"""
Semantic Analysis Module for MicroPy Compiler

This module provides semantic analysis capabilities including:
- Symbol table construction
- Use-before-assignment detection
- Unused variable detection
- Static semantic checks
"""

from .analyser import SemanticAnalyser, SymbolTable, SymbolEntry, print_symbol_table

__all__ = ['SemanticAnalyser', 'SymbolTable', 'SymbolEntry', 'print_symbol_table']
