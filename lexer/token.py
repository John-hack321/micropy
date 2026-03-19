from dataclasses import dataclass
from enum import Enum

# here we define all the token types in teh Token data structure for all the valid token types


# All valid token types in MicroPy
class TokenType(Enum):
    # Literals
    NUMBER      = "NUMBER"
    STRING      = "STRING"
    FSTRING     = "FSTRING"
    BOOLEAN     = "BOOLEAN"

    # Names
    KEYWORD     = "KEYWORD"
    IDENTIFIER  = "IDENTIFIER"

    # Operators
    OPERATOR    = "OPERATOR"        # + - * /
    COMPARE_OP  = "COMPARE_OP"      # == != < > <= >=
    LOGICAL_OP  = "LOGICAL_OP"      # and or
    ASSIGNMENT  = "ASSIGNMENT"      # =

    # Structure
    DELIMITER   = "DELIMITER"       # ( ) : ,
    NEWLINE     = "NEWLINE"
    INDENT      = "INDENT"
    DEDENT      = "DEDENT"
    EOF         = "EOF"

# we used data class so as to have automatic generation of __init__ and __repr__ for us instead of manual doing
@dataclass
class Token:
    type:  TokenType   
    value: str         # this give us the actual text from the sourcode
    line:  int         # this one tells which line it was on so that we can do error handling perfectly

    def __repr__(self):
        return f"Token({self.type.value:<12} | {repr(self.value):<30} | line {self.line})"


# micropy Reserved words for easier access form all parts of the program including the futer parser files and more

KEYWORDS    = {"if", "else", "while", "print", "input", "int", "str", "float"}
BOOLEANS    = {"True", "False"}
LOGICAL_OPS = {"and", "or"}