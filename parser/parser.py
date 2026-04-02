# ─────────────────────────────────────────────────────────────
#  parser/parser.py
#
#  Recursive Descent Parser for MicroPy.
#  Takes a list of tokens from the lexer.
#  Produces an AST (Abstract Syntax Tree) as output.
#
#  Every grammar rule in the BNF spec maps to one method here.
# ─────────────────────────────────────────────────────────────

from typing import List, Optional, Any
from lexer.token import Token, TokenType
from parser.nodes import (
    ProgramNode, AssignmentNode, IfNode, WhileNode,
    PrintNode, BinaryOpNode, LogicalOpNode, BuiltinCallNode,
    NumberNode, StringNode, FStringNode, BooleanNode,
    IdentifierNode
)
from utils.error_handler import ErrorHandler


class Parser:
    def __init__(self, tokens: List[Token], error_handler: ErrorHandler):
        self.tokens  = tokens
        self.pos     = 0
        self.errors  = error_handler

    # ─────────────────────────────────────────────────────────
    #  HELPERS — same idea as the lexer helpers but for tokens
    # ─────────────────────────────────────────────────────────

    def current(self) -> Token:
        """What token are we looking at right now?"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # return EOF token

    def peek(self, offset: int = 1) -> Token:
        """Look ahead without consuming."""
        p = self.pos + offset
        if p < len(self.tokens):
            return self.tokens[p]
        return self.tokens[-1]

    def advance(self) -> Token:
        """Consume current token and move forward."""
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, type: TokenType, value: str = None) -> Token:
        """
        Consume a token and verify it matches what we expect.
        If it does not match — report an error.
        This is how the parser enforces grammar rules.
        """
        token = self.current()
        if token.type != type:
            self.errors.report(
                "Parser",
                f"Expected {type.value} but got {token.type.value} '{token.value}'",
                token.line
            )
            return token
        if value and token.value != value:
            self.errors.report(
                "Parser",
                f"Expected '{value}' but got '{token.value}'",
                token.line
            )
            return token
        return self.advance()

    def skip_newlines(self):
        """Skip over any NEWLINE tokens."""
        while self.current().type == TokenType.NEWLINE:
            self.advance()

    def is_at_end(self) -> bool:
        """Have we reached the end of the token stream?"""
        return self.current().type == TokenType.EOF

    # ─────────────────────────────────────────────────────────
    #  ENTRY POINT
    #  <program> ::= <statement>+
    # ─────────────────────────────────────────────────────────

    def parse(self) -> ProgramNode:
        """
        Entry point — parse the entire program.
        Keeps parsing statements until end of file.
        Returns a ProgramNode containing all statements.
        """
        statements = []
        self.skip_newlines()

        while not self.is_at_end():
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        return ProgramNode(statements=statements)

    # ─────────────────────────────────────────────────────────
    #  STATEMENT
    #  <statement> ::= <assignment>
    #                | <if_stmt>
    #                | <while_stmt>
    #                | <print_stmt>
    #                | <builtin_call>
    # ─────────────────────────────────────────────────────────

    def parse_statement(self) -> Optional[Any]:
        """
        Look at the current token and decide which kind
        of statement we are dealing with.
        This is the main decision point of the parser.
        """
        self.skip_newlines()
        token = self.current()

        # ── if statement ──
        if token.type == TokenType.KEYWORD and token.value == "if":
            return self.parse_if_statement()

        # ── while statement ──
        if token.type == TokenType.KEYWORD and token.value == "while":
            return self.parse_while_statement()

        # ── print statement ──
        if token.type == TokenType.KEYWORD and token.value == "print":
            return self.parse_print_statement()

        # ── assignment: IDENTIFIER = <expression> or <condition> ──
        # We check: current is IDENTIFIER and next is ASSIGNMENT
        if (token.type == TokenType.IDENTIFIER and
                self.peek().type == TokenType.ASSIGNMENT):
            return self.parse_assignment()

        # ── standalone builtin call e.g int(input(...)) ──
        if token.type == TokenType.KEYWORD and token.value in ("int", "input", "str", "float"):
            return self.parse_builtin_call()

        # ── unknown statement ──
        self.errors.report(
            "Parser",
            f"Unexpected token '{token.value}'",
            token.line
        )
        self.advance()  # skip it and keep going
        return None

    # ─────────────────────────────────────────────────────────
    #  ASSIGNMENT
    #  <assignment> ::= IDENTIFIER "=" <expression>
    # ─────────────────────────────────────────────────────────

    def parse_assignment(self) -> AssignmentNode:
        """
        Parses: x = 10
                result = num1 + num2
                num1 = int(input('enter number'))
        """
        name_token = self.expect(TokenType.IDENTIFIER)  # consume the variable name
        self.expect(TokenType.ASSIGNMENT)               # consume the =
        value = self.parse_condition()                  # parse the right side (handles == too)

        return AssignmentNode(
            name  = name_token.value,
            value = value,
            line  = name_token.line
        )

    # ─────────────────────────────────────────────────────────
    #  IF STATEMENT
    #  <if_stmt> ::= "if" <condition> ":" <block>
    #              | "if" <condition> ":" <block> "else" ":" <block>
    # ─────────────────────────────────────────────────────────

    def parse_if_statement(self) -> IfNode:
        """
        Parses:
            if operator == 1:
                result = num1 * num2

            if boolean_value == True:
                print("hurray")
            else:
                print("nope")
        """
        line = self.current().line
        self.expect(TokenType.KEYWORD, "if")   # consume "if"
        condition = self.parse_condition()      # parse the condition
        self.expect(TokenType.DELIMITER, ":")   # consume ":"
        self.skip_newlines()
        then_block = self.parse_block()         # parse the indented block

        # check for optional else
        else_block = None
        self.skip_newlines()
        if (self.current().type == TokenType.KEYWORD and
                self.current().value == "else"):
            self.advance()                      # consume "else"
            self.expect(TokenType.DELIMITER, ":") # consume ":"
            self.skip_newlines()
            else_block = self.parse_block()     # parse the else block

        return IfNode(
            condition  = condition,
            then_block = then_block,
            else_block = else_block,
            line       = line
        )

    # ─────────────────────────────────────────────────────────
    #  WHILE STATEMENT
    #  <while_stmt> ::= "while" <condition> ":" <block>
    # ─────────────────────────────────────────────────────────

    def parse_while_statement(self) -> WhileNode:
        """
        Parses:
            while result < 5:
                print(message)
        """
        line = self.current().line
        self.expect(TokenType.KEYWORD, "while")  # consume "while"
        condition = self.parse_condition()        # parse the condition
        self.expect(TokenType.DELIMITER, ":")     # consume ":"
        self.skip_newlines()
        body = self.parse_block()                 # parse the loop body

        return WhileNode(
            condition = condition,
            body      = body,
            line      = line
        )

    # ─────────────────────────────────────────────────────────
    #  PRINT STATEMENT
    #  <print_stmt> ::= "print" "(" <expression> ")"
    # ─────────────────────────────────────────────────────────

    def parse_print_statement(self) -> PrintNode:
        """
        Parses:
            print("chose an operator")
            print(result)
            print(f"the boolean value was {boolean_value}")
        """
        line = self.current().line
        self.expect(TokenType.KEYWORD, "print")  # consume "print"
        self.expect(TokenType.DELIMITER, "(")    # consume "("
        value = self.parse_expression()          # parse what to print
        self.expect(TokenType.DELIMITER, ")")    # consume ")"

        return PrintNode(value=value, line=line)

    # ─────────────────────────────────────────────────────────
    #  BLOCK
    #  <block> ::= INDENT <statement>+ DEDENT
    # ─────────────────────────────────────────────────────────

    def parse_block(self) -> List[Any]:
        """
        Parses an indented block of statements.
        Expects INDENT at the start and DEDENT at the end.
        Returns a list of statement nodes.
        """
        statements = []
        self.expect(TokenType.INDENT)   # must see INDENT — block starts here
        self.skip_newlines()

        # keep parsing statements until we hit DEDENT or EOF
        while (not self.is_at_end() and
               self.current().type != TokenType.DEDENT):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        self.expect(TokenType.DEDENT)   # must see DEDENT — block ends here
        return statements

    # ─────────────────────────────────────────────────────────
    #  CONDITION
    #  <condition> ::= <expression> <compare_op> <expression>
    #               | <condition> "and" <condition>
    #               | <condition> "or"  <condition>
    # ─────────────────────────────────────────────────────────

    def parse_condition(self) -> Any:
        """
        Parses conditions like:
            operator == 1
            result < 5
            boolean_value == True
            boolean_value and num1 < 3
        """
        # parse the left side
        left = self.parse_expression()

        # check for comparison operator
        if self.current().type == TokenType.COMPARE_OP:
            op    = self.advance().value             # consume the operator
            right = self.parse_expression()          # parse right side
            left  = BinaryOpNode(left=left, op=op, right=right)

        # check for logical operator (and / or)
        if self.current().type == TokenType.LOGICAL_OP:
            op    = self.advance().value             # consume and/or
            right = self.parse_condition()           # parse right condition
            left  = LogicalOpNode(left=left, op=op, right=right)

        return left

    # ─────────────────────────────────────────────────────────
    #  EXPRESSION
    #  <expression> ::= <term>
    #                 | <expression> "+" <term>
    #                 | <expression> "-" <term>
    # ─────────────────────────────────────────────────────────

    def parse_expression(self) -> Any:
        """
        Handles + and - (lowest priority operators).
        Example: num1 + num2 - 1
        """
        left = self.parse_term()

        while (self.current().type == TokenType.OPERATOR and
               self.current().value in ('+', '-')):
            op    = self.advance().value    # consume + or -
            right = self.parse_term()
            left  = BinaryOpNode(left=left, op=op, right=right)

        return left

    # ─────────────────────────────────────────────────────────
    #  TERM
    #  <term> ::= <factor>
    #           | <term> "*" <factor>
    #           | <term> "/" <factor>
    # ─────────────────────────────────────────────────────────

    def parse_term(self) -> Any:
        """
        Handles * and / (higher priority than + and -).
        Example: num1 * num2
        This is why * and / happen before + and - — operator precedence.
        """
        left = self.parse_factor()

        while (self.current().type == TokenType.OPERATOR and
               self.current().value in ('*', '/')):
            op    = self.advance().value    # consume * or /
            right = self.parse_factor()
            left  = BinaryOpNode(left=left, op=op, right=right)

        return left

    # ─────────────────────────────────────────────────────────
    #  FACTOR
    #  <factor> ::= NUMBER | STRING | FSTRING | BOOLEAN
    #             | IDENTIFIER | "(" <expression> ")"
    #             | <builtin_call>
    # ─────────────────────────────────────────────────────────

    def parse_factor(self) -> Any:
        """
        The deepest level — handles raw values.
        This is where we produce the leaf nodes of the AST.
        """
        token = self.current()

        # ── integer number ──
        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(value=token.value, line=token.line)

        # ── string ──
        if token.type == TokenType.STRING:
            self.advance()
            return StringNode(value=token.value, line=token.line)

        # ── f-string ──
        if token.type == TokenType.FSTRING:
            self.advance()
            return FStringNode(value=token.value, line=token.line)

        # ── boolean ──
        if token.type == TokenType.BOOLEAN:
            self.advance()
            return BooleanNode(value=token.value, line=token.line)

        # ── identifier (variable name) ──
        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return IdentifierNode(name=token.value, line=token.line)

        # ── grouped expression: ( expression ) ──
        if token.type == TokenType.DELIMITER and token.value == "(":
            self.advance()                   # consume (
            expr = self.parse_expression()   # parse inside
            self.expect(TokenType.DELIMITER, ")")  # consume )
            return expr

        # ── builtin function call: int(...) input(...) ──
        if token.type == TokenType.KEYWORD and token.value in ("int", "input", "str", "float"):
            return self.parse_builtin_call()

        # ── unexpected token ──
        self.errors.report(
            "Parser",
            f"Unexpected token '{token.value}' in expression",
            token.line
        )
        self.advance()
        return NumberNode(value="0", line=token.line)  # return dummy node to keep going

    # ─────────────────────────────────────────────────────────
    #  BUILTIN CALL
    #  <builtin_call> ::= "int"   "(" <expression> ")"
    #                   | "input" "(" <expression> ")"
    #                   | "str"   "(" <expression> ")"
    #                   | "float" "(" <expression> ")"
    # ─────────────────────────────────────────────────────────

    def parse_builtin_call(self) -> BuiltinCallNode:
        """
        Parses calls like:
            int(input('enter number'))
            input('enter operator')
            str(result)
        """
        line      = self.current().line
        func_name = self.advance().value             # consume function name
        self.expect(TokenType.DELIMITER, "(")        # consume (
        argument  = self.parse_expression()          # parse the argument
        self.expect(TokenType.DELIMITER, ")")        # consume )

        return BuiltinCallNode(
            func_name = func_name,
            argument  = argument,
            line      = line
        )


# patch: make expect tolerant of EOF for DEDENT
_original_expect = Parser.expect
def _tolerant_expect(self, type, value=None):
    if type == TokenType.DEDENT and self.current().type == TokenType.EOF:
        return self.current()
    return _original_expect(self, type, value)
Parser.expect = _tolerant_expect