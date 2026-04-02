from dataclasses import dataclass, field
from typing import List, Optional, Any


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

# ── ROOT NODE ──

@dataclass
class ProgramNode(Node):
    statements: List[Any] = field(default_factory=list)


@dataclass
class LogicalOpNode(Node):
    left:  Any = None
    op:    str = ""
    right: Any = None