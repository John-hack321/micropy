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



# I tried to do add these lines to give our AST printed on the terminal a better visualization tweak as you want at will.

def print_ast(node: Any, indent: str = "", is_last: bool = True) -> None:
    
    # these will be our tree drawing characters
    branch = "└── " if is_last else "├── "
    pipe   = "    " if is_last else "│   "

    if isinstance(node, ProgramNode):
        print(f"ProgramNode ({len(node.statements)} statements)")
        for i, stmt in enumerate(node.statements):
            is_last_stmt = i == len(node.statements) - 1
            print_ast(stmt, indent, is_last_stmt)

    elif isinstance(node, AssignmentNode):
        print(f"{indent}{branch}AssignmentNode → {node.name}")
        print_ast(node.value, indent + pipe, True)

    elif isinstance(node, IfNode):
        print(f"{indent}{branch}IfNode")
        print(f"{indent}{pipe}├── condition:")
        print_ast(node.condition, indent + pipe + "│   ", True)
        print(f"{indent}{pipe}├── then:")
        for i, stmt in enumerate(node.then_block):
            is_last_stmt = i == len(node.then_block) - 1 and not node.else_block
            print_ast(stmt, indent + pipe + "│   ", is_last_stmt)
        if node.else_block:
            print(f"{indent}{pipe}└── else:")
            for i, stmt in enumerate(node.else_block):
                print_ast(stmt, indent + pipe + "    ", i == len(node.else_block) - 1)

    elif isinstance(node, WhileNode):
        print(f"{indent}{branch}WhileNode")
        print(f"{indent}{pipe}├── condition:")
        print_ast(node.condition, indent + pipe + "│   ", True)
        print(f"{indent}{pipe}└── body:")
        for i, stmt in enumerate(node.body):
            print_ast(stmt, indent + pipe + "    ", i == len(node.body) - 1)

    elif isinstance(node, PrintNode):
        print(f"{indent}{branch}PrintNode")
        print_ast(node.value, indent + pipe, True)

    elif isinstance(node, BinaryOpNode):
        print(f"{indent}{branch}BinaryOpNode ({node.op})")
        print_ast(node.left,  indent + pipe, False)
        print_ast(node.right, indent + pipe, True)

    elif isinstance(node, LogicalOpNode):
        print(f"{indent}{branch}LogicalOpNode ({node.op})")
        print_ast(node.left,  indent + pipe, False)
        print_ast(node.right, indent + pipe, True)

    elif isinstance(node, BuiltinCallNode):
        print(f"{indent}{branch}BuiltinCallNode → {node.func_name}()")
        if node.argument is not None:
            print_ast(node.argument, indent + pipe, True)

    elif isinstance(node, IdentifierNode):
        print(f"{indent}{branch}IdentifierNode → {node.name}")

    elif isinstance(node, NumberNode):
        print(f"{indent}{branch}NumberNode → {node.value}")

    elif isinstance(node, StringNode):
        print(f"{indent}{branch}StringNode → '{node.value}'")

    elif isinstance(node, FStringNode):
        print(f"{indent}{branch}FStringNode → f'{node.value}'")

    elif isinstance(node, BooleanNode):
        print(f"{indent}{branch}BooleanNode → {node.value}")

    else:
        print(f"{indent}{branch}{type(node).__name__}")