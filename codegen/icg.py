# ─────────────────────────────────────────────────────────────
#  codegen/icg.py
#
#  Intermediate Code Generator (ICG) for MicroPy.
#  Representation: QUADRUPLES  →  (op, arg1, arg2, result)
#
#  Walks the AST produced by the parser and emits a flat list
#  of quadruples that a back-end (or virtual machine) can then
#  translate into target code.
#
#  Quadruple format
#  ─────────────────
#  | op          | arg1      | arg2      | result    |
#  |-------------|-----------|-----------|-----------|
#  | +  -  *  /  | operand   | operand   | temp var  |
#  | ==  !=  etc | operand   | operand   | temp var  |
#  | and  or     | operand   | operand   | temp var  |
#  | =           | value     | _         | variable  |
#  | print       | value     | _         | _         |
#  | input       | prompt    | _         | temp var  |
#  | int         | operand   | _         | temp var  |
#  | if_false    | condition | _         | label     |
#  | goto        | _         | _         | label     |
#  | label       | _         | _         | label     |
# ─────────────────────────────────────────────────────────────

from typing import List, Tuple, Any
from parser.nodes import (
    ProgramNode, AssignmentNode, IfNode, WhileNode,
    PrintNode, BinaryOpNode, LogicalOpNode, BuiltinCallNode,
    NumberNode, StringNode, FStringNode, BooleanNode,
    IdentifierNode
)

# A quadruple is just a named 4-tuple for clarity
class Quadruple:
    def __init__(self, op: str, arg1: str, arg2: str, result: str):
        self.op     = op
        self.arg1   = arg1
        self.arg2   = arg2
        self.result = result

    def __repr__(self):
        return f"({self.op:<12} {self.arg1:<16} {self.arg2:<16} {self.result})"


class ICG:
    def __init__(self):
        self.quads        : List[Quadruple] = []
        self._temp_count  : int = 0   # t0, t1, t2 …  temporary variables
        self._label_count : int = 0   # L0, L1, L2 …  jump labels

    # ── helpers ──────────────────────────────────────────────

    def _new_temp(self) -> str:
        """Allocate a fresh temporary variable name."""
        name = f"t{self._temp_count}"
        self._temp_count += 1
        return name

    def _new_label(self) -> str:
        """Allocate a fresh label name."""
        name = f"L{self._label_count}"
        self._label_count += 1
        return name

    def _emit(self, op: str, arg1: str = "_", arg2: str = "_", result: str = "_"):
        """Append one quadruple to the output list."""
        self.quads.append(Quadruple(op, arg1, arg2, result))

    # ── public entry point ────────────────────────────────────

    def generate(self, ast: ProgramNode) -> List[Quadruple]:
        """
        Walk the entire AST and return the complete quadruple list.
        Call this once after parsing.
        """
        self._gen_program(ast)
        return self.quads

    # ── statement dispatch ────────────────────────────────────

    def _gen_program(self, node: ProgramNode):
        for stmt in node.statements:
            self._gen_statement(stmt)

    def _gen_statement(self, node: Any):
        if isinstance(node, AssignmentNode):
            self._gen_assignment(node)
        elif isinstance(node, IfNode):
            self._gen_if(node)
        elif isinstance(node, WhileNode):
            self._gen_while(node)
        elif isinstance(node, PrintNode):
            self._gen_print(node)
        elif isinstance(node, BuiltinCallNode):
            # standalone call used as a statement
            self._gen_builtin(node)
        else:
            pass   # unknown node — skip silently

    # ── assignment  →  (=, value, _, variable) ───────────────

    def _gen_assignment(self, node: AssignmentNode):
        """
        x = <expr>
        Evaluate the right-hand side, then emit an assignment quad.
        """
        rhs = self._gen_expr(node.value)
        self._emit("=", rhs, "_", node.name)

    # ── if / if-else ──────────────────────────────────────────
    #
    #  Pattern (no else):
    #      <evaluate condition → t0>
    #      if_false   t0   _   L_end
    #      <then block>
    #      label      _    _   L_end
    #
    #  Pattern (with else):
    #      <evaluate condition → t0>
    #      if_false   t0   _   L_else
    #      <then block>
    #      goto       _    _   L_end
    #      label      _    _   L_else
    #      <else block>
    #      label      _    _   L_end

    def _gen_if(self, node: IfNode):
        cond_temp = self._gen_expr(node.condition)

        if node.else_block is None:
            # ── if only ──
            l_end = self._new_label()
            self._emit("if_false", cond_temp, "_", l_end)
            for stmt in node.then_block:
                self._gen_statement(stmt)
            self._emit("label", "_", "_", l_end)
        else:
            # ── if / else ──
            l_else = self._new_label()
            l_end  = self._new_label()
            self._emit("if_false", cond_temp, "_", l_else)
            for stmt in node.then_block:
                self._gen_statement(stmt)
            self._emit("goto",  "_",  "_",    l_end)
            self._emit("label", "_",  "_",    l_else)
            for stmt in node.else_block:
                self._gen_statement(stmt)
            self._emit("label", "_",  "_",    l_end)

    # ── while ─────────────────────────────────────────────────
    #
    #  Pattern:
    #      label      _    _   L_start
    #      <evaluate condition → t0>
    #      if_false   t0   _   L_end
    #      <body>
    #      goto       _    _   L_start
    #      label      _    _   L_end

    def _gen_while(self, node: WhileNode):
        l_start = self._new_label()
        l_end   = self._new_label()

        self._emit("label",    "_",       "_", l_start)
        cond_temp = self._gen_expr(node.condition)
        self._emit("if_false", cond_temp, "_", l_end)
        for stmt in node.body:
            self._gen_statement(stmt)
        self._emit("goto",  "_", "_", l_start)
        self._emit("label", "_", "_", l_end)

    # ── print  →  (print, value, _, _) ───────────────────────

    def _gen_print(self, node: PrintNode):
        val = self._gen_expr(node.value)
        self._emit("print", val, "_", "_")

    # ── expression evaluator ──────────────────────────────────

    def _gen_expr(self, node: Any) -> str:
        """
        Recursively generate quads for an expression.
        Returns the name of the variable / temp that holds the result.
        """

        # ── arithmetic / comparison BinaryOpNode ─────────────
        if isinstance(node, BinaryOpNode):
            left  = self._gen_expr(node.left)
            right = self._gen_expr(node.right)
            temp  = self._new_temp()
            self._emit(node.op, left, right, temp)
            return temp

        # ── logical  (and / or) ───────────────────────────────
        if isinstance(node, LogicalOpNode):
            left  = self._gen_expr(node.left)
            right = self._gen_expr(node.right)
            temp  = self._new_temp()
            self._emit(node.op, left, right, temp)
            return temp

        # ── built-in calls ────────────────────────────────────
        if isinstance(node, BuiltinCallNode):
            return self._gen_builtin(node)

        # ── literals ──────────────────────────────────────────
        if isinstance(node, NumberNode):
            return node.value                   # e.g. "42"

        if isinstance(node, StringNode):
            return f'"{node.value}"'            # e.g. '"hello"'

        if isinstance(node, FStringNode):
            return f'f"{node.value}"'           # e.g. 'f"val is {x}"'

        if isinstance(node, BooleanNode):
            return node.value                   # "True" / "False"

        # ── identifier ───────────────────────────────────────
        if isinstance(node, IdentifierNode):
            return node.name                    # e.g. "num1"

        # fallback
        return "_"

    # ── builtin calls ─────────────────────────────────────────

    def _gen_builtin(self, node: BuiltinCallNode) -> str:
        """
        Generates quads for int(), input(), str(), float().
        Returns the temp that holds the result.

        int(input('prompt'))  expands to two quads:
            (input,  "prompt",  _,  t0)
            (int,    t0,        _,  t1)
        """
        if node.func_name == "input":
            arg  = self._gen_expr(node.argument) if node.argument else '""'
            temp = self._new_temp()
            self._emit("input", arg, "_", temp)
            return temp

        elif node.func_name in ("int", "str", "float"):
            arg  = self._gen_expr(node.argument) if node.argument else "_"
            temp = self._new_temp()
            self._emit(node.func_name, arg, "_", temp)
            return temp

        else:
            # unknown builtin — treat as identity
            arg  = self._gen_expr(node.argument) if node.argument else "_"
            temp = self._new_temp()
            self._emit(node.func_name, arg, "_", temp)
            return temp


# ── pretty printer ────────────────────────────────────────────

def print_quads(quads: List[Quadruple]):
    """
    Print the quadruple table in a clean, report-ready format.
    """
    col_w = [6, 14, 18, 18, 18]
    header = (
        f"  {'#':<{col_w[0]}}"
        f"{'OP':<{col_w[1]}}"
        f"{'ARG1':<{col_w[2]}}"
        f"{'ARG2':<{col_w[3]}}"
        f"{'RESULT':<{col_w[4]}}"
    )
    divider = "  " + "─" * (sum(col_w) + 2)

    print(header)
    print(divider)
    for i, q in enumerate(quads):
        print(
            f"  {i:<{col_w[0]}}"
            f"{q.op:<{col_w[1]}}"
            f"{q.arg1:<{col_w[2]}}"
            f"{q.arg2:<{col_w[3]}}"
            f"{q.result:<{col_w[4]}}"
        )
    print(divider)
    print(f"  Total quadruples: {len(quads)}")