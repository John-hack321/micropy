# ─────────────────────────────────────────────────────────────
#  semantic/analyser.py
#
#  Semantic Analyser for MicroPy — Phase 3
#  (ICG is now Phase 4)
#
#  Responsibilities:
#    1. Build a symbol table of every variable in the program
#    2. Detect use-before-assignment (undeclared variable use)
#    3. Detect unused variables (assigned but never read)
#    4. Detect division by zero (static, where detectable)
#    5. Detect unreachable else blocks (condition is a literal)
#    6. Track scope — variables inside if/while blocks are
#       flagged as "possibly assigned" vs "definitely assigned"
#
#  The analyser walks the AST in the same post-order style
#  as the ICG. It does NOT modify the AST — it only reads it
#  and reports errors/warnings through the shared ErrorHandler.
#
#  Output: a populated SymbolTable that can be printed and
#          passed downstream to the ICG if needed.
# ─────────────────────────────────────────────────────────────

from typing import Any, Dict, List, Optional
from parser.nodes import (
    ProgramNode, AssignmentNode, IfNode, WhileNode,
    PrintNode, BinaryOpNode, LogicalOpNode, BuiltinCallNode,
    NumberNode, StringNode, FStringNode, BooleanNode,
    IdentifierNode
)
from utils.error_handler import ErrorHandler


# ── Symbol Table Entry ────────────────────────────────────────

class SymbolEntry:
    """
    One record in the symbol table — one per unique variable name.

    Fields
    ------
    name          : variable name
    assigned_line : first line where the variable was assigned
    definite      : True  → definitely assigned (top-level or all branches)
                    False → possibly assigned (only inside if/while block)
    read_count    : how many times the variable was read after assignment
    read_lines    : every line where the variable was read
    """
    def __init__(self, name: str, line: int, definite: bool = True):
        self.name          = name
        self.assigned_line = line
        self.definite      = definite
        self.read_count    = 0
        self.read_lines    : List[int] = []

    def mark_read(self, line: int):
        self.read_count += 1
        self.read_lines.append(line)

    def __repr__(self):
        status = "definite" if self.definite else "possible"
        return (
            f"SymbolEntry(name={self.name!r}, "
            f"assigned_line={self.assigned_line}, "
            f"status={status}, "
            f"read_count={self.read_count})"
        )


# ── Symbol Table ──────────────────────────────────────────────

class SymbolTable:
    """
    Flat symbol table mapping variable names to SymbolEntry objects.
    MicroPy has no functions or nested scopes beyond if/while blocks,
    so one flat table with a 'definite' flag is sufficient.
    """
    def __init__(self):
        self._table: Dict[str, SymbolEntry] = {}

    def declare(self, name: str, line: int, definite: bool = True):
        """
        Record that a variable was assigned at a given line.
        If the variable already exists, update its definite status
        (a second assignment at top level makes it definitely assigned).
        """
        if name in self._table:
            # re-assignment — if now at top level, upgrade to definite
            if definite:
                self._table[name].definite = True
        else:
            self._table[name] = SymbolEntry(name, line, definite)

    def lookup(self, name: str) -> Optional[SymbolEntry]:
        """Return the entry for a name, or None if not found."""
        return self._table.get(name)

    def mark_read(self, name: str, line: int):
        """Record a read access to an existing variable."""
        if name in self._table:
            self._table[name].mark_read(line)

    def is_declared(self, name: str) -> bool:
        return name in self._table

    def all_entries(self) -> List[SymbolEntry]:
        return list(self._table.values())

    def unused_variables(self) -> List[SymbolEntry]:
        """Variables that were assigned but never read."""
        return [e for e in self._table.values() if e.read_count == 0]


# ── Semantic Analyser ─────────────────────────────────────────

class SemanticAnalyser:
    """
    Walks the AST and performs all semantic checks.
    Call analyse(ast) once — it returns the populated SymbolTable.
    """

    def __init__(self, error_handler: ErrorHandler):
        self.errors       = error_handler
        self.symbol_table = SymbolTable()
        # tracks whether we are inside a conditional block
        # (if/while body) — assignments here are only "possible"
        self._in_conditional_depth = 0

    @property
    def _in_conditional(self) -> bool:
        return self._in_conditional_depth > 0

    # ── public entry point ────────────────────────────────────

    def analyse(self, ast: ProgramNode) -> SymbolTable:
        """
        Entry point. Walk the full program, run all checks,
        return the completed symbol table.
        """
        self._check_program(ast)
        self._check_unused()
        return self.symbol_table

    # ── program / statement dispatch ─────────────────────────

    def _check_program(self, node: ProgramNode):
        for stmt in node.statements:
            self._check_statement(stmt)

    def _check_statement(self, node: Any):
        if isinstance(node, AssignmentNode):
            self._check_assignment(node)
        elif isinstance(node, IfNode):
            self._check_if(node)
        elif isinstance(node, WhileNode):
            self._check_while(node)
        elif isinstance(node, PrintNode):
            self._check_print(node)
        elif isinstance(node, BuiltinCallNode):
            self._check_builtin(node)
        # unknown node types are silently skipped

    # ── assignment ────────────────────────────────────────────

    def _check_assignment(self, node: AssignmentNode):
        """
        x = <expr>

        1. Check the right-hand side expression first (it is READ)
        2. Then declare the variable on the left (it is WRITTEN)

        The variable is "definitely" assigned only if we are at
        top level (not inside an if/while block).
        """
        # check RHS — variables used here must already be declared
        self._check_expr(node.value)

        # declare LHS — this variable is now known
        definite = not self._in_conditional
        self.symbol_table.declare(node.name, node.line, definite)

    # ── if / else ─────────────────────────────────────────────

    def _check_if(self, node: IfNode):
        """
        Check condition, then both blocks.
        Variables assigned inside either block are "possibly" assigned
        because we don't know at compile time which branch runs.

        Special case: if the condition is a literal boolean we can
        detect unreachable code statically.
        """
        # check for always-true / always-false condition
        self._check_static_condition(node.condition, node.line)

        # check the condition expression itself
        self._check_expr(node.condition)

        # then block — inside a conditional scope
        self._in_conditional_depth += 1
        for stmt in node.then_block:
            self._check_statement(stmt)
        self._in_conditional_depth -= 1

        # else block — also inside a conditional scope
        if node.else_block:
            self._in_conditional_depth += 1
            for stmt in node.else_block:
                self._check_statement(stmt)
            self._in_conditional_depth -= 1

    # ── while ─────────────────────────────────────────────────

    def _check_while(self, node: WhileNode):
        """
        Check condition, then body.
        Variables assigned inside the body are "possibly" assigned
        because the loop may never execute (condition false from start).
        """
        self._check_static_condition(node.condition, node.line)
        self._check_expr(node.condition)

        self._in_conditional_depth += 1
        for stmt in node.body:
            self._check_statement(stmt)
        self._in_conditional_depth -= 1

    # ── print ─────────────────────────────────────────────────

    def _check_print(self, node: PrintNode):
        self._check_expr(node.value)

    # ── expression checker ────────────────────────────────────

    def _check_expr(self, node: Any):
        """
        Recursively walk an expression node.
        The key job here is to catch IdentifierNodes that refer
        to variables that have never been assigned.
        Also catches static division by zero.
        """
        if node is None:
            return

        # ── identifier — this is a READ ───────────────────────
        if isinstance(node, IdentifierNode):
            entry = self.symbol_table.lookup(node.name)
            if entry is None:
                # variable has never been seen at all
                self.errors.report(
                    "Semantic",
                    f"Variable '{node.name}' used before assignment",
                    node.line
                )
            else:
                # variable exists — record this read
                self.symbol_table.mark_read(node.name, node.line)
                # warn if it was only possibly assigned
                if not entry.definite:
                    self.errors.report(
                        "Semantic",
                        f"Variable '{node.name}' may not be assigned "
                        f"(first assigned inside a conditional block at "
                        f"line {entry.assigned_line})",
                        node.line
                    )

        # ── binary op — check both sides ──────────────────────
        elif isinstance(node, BinaryOpNode):
            self._check_expr(node.left)
            self._check_expr(node.right)
            # static division by zero check
            if node.op == "/" and isinstance(node.right, NumberNode):
                if node.right.value == "0":
                    self.errors.report(
                        "Semantic",
                        "Division by zero detected",
                        node.line
                    )

        # ── logical op ────────────────────────────────────────
        elif isinstance(node, LogicalOpNode):
            self._check_expr(node.left)
            self._check_expr(node.right)

        # ── builtin call ──────────────────────────────────────
        elif isinstance(node, BuiltinCallNode):
            self._check_builtin(node)

        # ── literals — nothing to check ───────────────────────
        elif isinstance(node, (NumberNode, StringNode,
                                FStringNode, BooleanNode)):
            # check fstring for variable references inside { }
            if isinstance(node, FStringNode):
                self._check_fstring_vars(node)

    # ── builtin call ──────────────────────────────────────────

    def _check_builtin(self, node: BuiltinCallNode):
        """
        For int(), str(), float() — check the argument expression.
        For input() — argument is a prompt string, always valid.
        """
        if node.func_name == "input":
            # prompt is a string literal — nothing to check
            return
        if node.argument is not None:
            self._check_expr(node.argument)

    # ── fstring variable reference check ──────────────────────

    def _check_fstring_vars(self, node: FStringNode):
        """
        Extract variable names from inside { } in an f-string
        and verify each one has been declared.

        e.g.  f"num1 is {num1} and num2 is {num2}"
              → checks 'num1' and 'num2'
        """
        content = node.value
        i = 0
        while i < len(content):
            if content[i] == '{':
                j = content.find('}', i)
                if j != -1:
                    var_name = content[i+1:j].strip()
                    # only check simple identifiers (no expressions)
                    if var_name.isidentifier():
                        entry = self.symbol_table.lookup(var_name)
                        if entry is None:
                            self.errors.report(
                                "Semantic",
                                f"Variable '{var_name}' used in f-string "
                                f"before assignment",
                                node.line
                            )
                        else:
                            self.symbol_table.mark_read(var_name, node.line)
                    i = j + 1
                    continue
            i += 1

    # ── static condition checks ───────────────────────────────

    def _check_static_condition(self, condition: Any, line: int):
        """
        If a condition is a literal boolean (True/False) we can
        detect at compile time that one branch is unreachable.
        e.g.  if True:   → else block will never run
              while False: → loop body will never run
        """
        if isinstance(condition, BooleanNode):
            if condition.value == "True":
                self.errors.report(
                    "Semantic",
                    "Condition is always True — else block / loop exit "
                    "is unreachable (static warning)",
                    line
                )
            elif condition.value == "False":
                self.errors.report(
                    "Semantic",
                    "Condition is always False — then block / loop body "
                    "is unreachable (static warning)",
                    line
                )

    # ── unused variable check ─────────────────────────────────

    def _check_unused(self):
        """
        After the full tree walk, any variable that was assigned
        but never read is reported as a warning.
        This runs once at the end of analyse().
        """
        for entry in self.symbol_table.unused_variables():
            self.errors.report(
                "Semantic",
                f"Variable '{entry.name}' is assigned at line "
                f"{entry.assigned_line} but never used",
                entry.assigned_line
            )


# ── Symbol Table Pretty Printer ───────────────────────────────

def print_symbol_table(symbol_table: SymbolTable):
    """
    Print the symbol table in a clean report-ready format.
    """
    entries = symbol_table.all_entries()

    col_w = [6, 20, 10, 10, 12, 20]
    header = (
        f"  {'#':<{col_w[0]}}"
        f"{'VARIABLE':<{col_w[1]}}"
        f"{'DECL LINE':<{col_w[2]}}"
        f"{'STATUS':<{col_w[3]}}"
        f"{'READ COUNT':<{col_w[4]}}"
        f"{'READ AT LINES':<{col_w[5]}}"
    )
    divider = "  " + "─" * (sum(col_w) + 2)

    print(header)
    print(divider)
    for i, entry in enumerate(entries):
        status    = "definite" if entry.definite else "possible"
        read_lines = ", ".join(str(l) for l in entry.read_lines) or "—"
        print(
            f"  {i:<{col_w[0]}}"
            f"{entry.name:<{col_w[1]}}"
            f"{entry.assigned_line:<{col_w[2]}}"
            f"{status:<{col_w[3]}}"
            f"{entry.read_count:<{col_w[4]}}"
            f"{read_lines:<{col_w[5]}}"
        )
    print(divider)
    print(f"  Total variables: {len(entries)}")
