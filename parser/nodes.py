from dataclasses import dataclass, field
from typing import List, Optional, Any

"""
here every node defined is a represention of a representation of a production rule in our grammar.
"""

@dataclass
class Node:
    line: int = 0

# LITERAL NODES 

@dataclass
class NumberNode(Node):
    value: str = ""

@dataclass
class StringNode(Node):
    value: str = ""

@dataclass
class FStringNode(Node):
    value: str = ""

@dataclass
class BooleanNode(Node):
    value: str = ""

@dataclass
class IdentifierNode(Node):
    name: str = ""

# ── EXPRESSION NODES ──

@dataclass
class BinaryOpNode(Node):
    left:  Any = None
    op:    str = ""
    right: Any = None

@dataclass
class BuiltinCallNode(Node):
    func_name: str = ""
    argument:  Any = None

# ── STATEMENT NODES ──

@dataclass
class AssignmentNode(Node):
    name:  str = ""
    value: Any = None

@dataclass
class PrintNode(Node):
    value: Any = None

@dataclass
class InputNode(Node):
    prompt: Any = None

@dataclass
class IfNode(Node):
    condition:  Any             = None
    then_block: List[Any]       = field(default_factory=list)
    else_block: Optional[List[Any]] = None

@dataclass
class WhileNode(Node):
    condition: Any       = None
    body:      List[Any] = field(default_factory=list)

# ROOT NODE : everything is help here.

@dataclass
class ProgramNode(Node):
    statements: List[Any] = field(default_factory=list)


@dataclass
class LogicalOpNode(Node):
    left:  Any = None
    op:    str = ""
    right: Any = None


# ─────────────────────────────────────────────────────────────
#  AST Pretty Printer — names match BNF grammar rules
#
#  BNF rule          →   printed label
#  ─────────────────────────────────────────────────────────────
#  <program>         →   <program>
#  <statement_list>  →   (implicit — each child of <program>)
#  <statement>       →   <statement>  (wraps the actual node)
#  <assignment>      →   <assignment>
#  <if_stmt>         →   <if_stmt>
#  <while_stmt>      →   <while_stmt>
#  <print_stmt>      →   <print_stmt>
#  <input_stmt>      →   <input_stmt>
#  <block>           →   <block>
#  <condition>       →   <condition>
#  <expression>      →   <expression>
#  <term>            →   <term>
#  <factor>          →   <factor>  (leaf — shows actual value)
#  <builtin_call>    →   <builtin_call>
#  <compare_op>      →   <compare_op>
# ─────────────────────────────────────────────────────────────

def print_ast(node: Any, indent: str = "", is_last: bool = True) -> None:

    branch = "└── " if is_last else "├── "
    pipe   = "    " if is_last else "│   "

    # ── <program> ──────────────────────────────────────────
    if isinstance(node, ProgramNode):
        print(f"<program>  ({len(node.statements)} statements)")
        for i, stmt in enumerate(node.statements):
            is_last_stmt = i == len(node.statements) - 1
            _print_statement(stmt, indent, is_last_stmt)

    else:
        # fallback for a direct call with a non-program root
        _print_statement(node, indent, is_last)


def _print_statement(node: Any, indent: str, is_last: bool) -> None:
    """
    Wrap every top-level child in a <statement> label,
    then delegate to the appropriate handler.
    Matches: <statement_list> ::= <statement> | <statement> <statement_list>
    """
    branch = "└── " if is_last else "├── "
    pipe   = "    " if is_last else "│   "

    print(f"{indent}{branch}<statement>")
    child_indent = indent + pipe
    _print_node(node, child_indent, True)


def _print_node(node: Any, indent: str, is_last: bool) -> None:
    """
    Recursively print a node using the BNF rule name as the label.
    """
    branch = "└── " if is_last else "├── "
    pipe   = "    " if is_last else "│   "

    # ── <assignment> ───────────────────────────────────────
    if isinstance(node, AssignmentNode):
        print(f"{indent}{branch}<assignment>  identifier: '{node.name}'")
        _print_expression_or_condition(node.value, indent + pipe, True)

    # ── <if_stmt> ──────────────────────────────────────────
    elif isinstance(node, IfNode):
        print(f"{indent}{branch}<if_stmt>")
        next_indent = indent + pipe

        # condition
        has_else   = node.else_block is not None
        has_then   = len(node.then_block) > 0
        cond_last  = not has_then and not has_else

        print(f"{next_indent}{'└── ' if cond_last else '├── '}<condition>")
        _print_expression_or_condition(
            node.condition,
            next_indent + ("    " if cond_last else "│   "),
            True
        )

        # then block
        then_last = not has_else
        print(f"{next_indent}{'└── ' if then_last else '├── '}<block>  [then]")
        block_indent = next_indent + ("    " if then_last else "│   ")
        for i, stmt in enumerate(node.then_block):
            _print_statement(stmt, block_indent, i == len(node.then_block) - 1)

        # else block (optional)
        if has_else:
            print(f"{next_indent}└── <block>  [else]")
            else_indent = next_indent + "    "
            for i, stmt in enumerate(node.else_block):
                _print_statement(stmt, else_indent, i == len(node.else_block) - 1)

    # ── <while_stmt> ───────────────────────────────────────
    elif isinstance(node, WhileNode):
        print(f"{indent}{branch}<while_stmt>")
        next_indent = indent + pipe

        print(f"{next_indent}├── <condition>")
        _print_expression_or_condition(node.condition, next_indent + "│   ", True)

        print(f"{next_indent}└── <block>")
        body_indent = next_indent + "    "
        for i, stmt in enumerate(node.body):
            _print_statement(stmt, body_indent, i == len(node.body) - 1)

    # ── <print_stmt> ───────────────────────────────────────
    elif isinstance(node, PrintNode):
        print(f"{indent}{branch}<print_stmt>")
        _print_expression_or_condition(node.value, indent + pipe, True)

    # ── <input_stmt> / <builtin_call> ──────────────────────
    elif isinstance(node, BuiltinCallNode):
        # input() at the top level is <input_stmt>; elsewhere it is <builtin_call>
        label = "<input_stmt>" if node.func_name == "input" else "<builtin_call>"
        print(f"{indent}{branch}{label}  func: '{node.func_name}'")
        if node.argument is not None:
            _print_expression_or_condition(node.argument, indent + pipe, True)

    # ── anything else (expressions used as statements) ─────
    else:
        _print_expression_or_condition(node, indent, is_last)


def _print_expression_or_condition(node: Any, indent: str, is_last: bool) -> None:
    """
    Decides whether to label a node as <condition>, <expression>,
    <term>, <factor>, or <builtin_call> based on what it is,
    mirroring the BNF hierarchy.
    """
    branch = "└── " if is_last else "├── "
    pipe   = "    " if is_last else "│   "

    # ── <condition> — comparison or logical ────────────────
    if isinstance(node, BinaryOpNode) and node.op in ('==', '!=', '<', '>', '<=', '>='):
        print(f"{indent}{branch}<condition>")
        cond_indent = indent + pipe
        # left side is an <expression>
        _print_as_expression(node.left, cond_indent, False)
        # the operator is a <compare_op>
        print(f"{cond_indent}├── <compare_op>  '{node.op}'")
        # right side is an <expression>
        _print_as_expression(node.right, cond_indent, True)

    elif isinstance(node, LogicalOpNode):
        print(f"{indent}{branch}<condition>")
        cond_indent = indent + pipe
        _print_expression_or_condition(node.left,  cond_indent, False)
        print(f"{cond_indent}├── logical_op  '{node.op}'")
        _print_expression_or_condition(node.right, cond_indent, True)

    # ── <expression> / <term> / <factor> — arithmetic ──────
    else:
        _print_as_expression(node, indent, is_last)


def _print_as_expression(node: Any, indent: str, is_last: bool) -> None:
    """
    Labels arithmetic BinaryOpNodes as <expression> (+ -)
    or <term> (* /), and everything else as <factor>.
    """
    branch = "└── " if is_last else "├── "
    pipe   = "    " if is_last else "│   "

    if isinstance(node, BinaryOpNode) and node.op in ('+', '-'):
        print(f"{indent}{branch}<expression>  op: '{node.op}'")
        expr_indent = indent + pipe
        _print_as_expression(node.left,  expr_indent, False)
        _print_as_expression(node.right, expr_indent, True)

    elif isinstance(node, BinaryOpNode) and node.op in ('*', '/'):
        print(f"{indent}{branch}<term>  op: '{node.op}'")
        term_indent = indent + pipe
        _print_as_expression(node.left,  term_indent, False)
        _print_as_expression(node.right, term_indent, True)

    elif isinstance(node, BuiltinCallNode):
        label = "<input_stmt>" if node.func_name == "input" else "<builtin_call>"
        print(f"{indent}{branch}{label}  func: '{node.func_name}'")
        if node.argument is not None:
            _print_as_expression(node.argument, indent + pipe, True)

    # ── <factor> — leaf nodes ───────────────────────────────
    elif isinstance(node, NumberNode):
        print(f"{indent}{branch}<factor>  NUMBER '{node.value}'")

    elif isinstance(node, StringNode):
        print(f"{indent}{branch}<factor>  STRING '{node.value}'")

    elif isinstance(node, FStringNode):
        print(f"{indent}{branch}<factor>  FSTRING f'{node.value}'")

    elif isinstance(node, BooleanNode):
        print(f"{indent}{branch}<factor>  BOOLEAN '{node.value}'")

    elif isinstance(node, IdentifierNode):
        print(f"{indent}{branch}<factor>  IDENTIFIER '{node.name}'")

    else:
        print(f"{indent}{branch}{type(node).__name__}")