#  lexer/lexer.py
#
#  The Lexer (Scanner) for MicroPy.
#  Takes raw source code as input.
#  Produces a list of Tokens as output.

from typing import List, Optional
from lexer.token import Token, TokenType, KEYWORDS, BOOLEANS, LOGICAL_OPS
from utils.error_handler import ErrorHandler


class Lexer:
    def __init__(self, source: str, error_handler: ErrorHandler):
        self.source        = source
        self.errors        = error_handler
        self.pos           = 0      # current character position
        self.line          = 1      # current line number
        self.tokens        : List[Token] = []
        self.indent_stack  : List[int]   = [0]  # tracks indentation levels

    def current(self) -> Optional[str]:
        """
        show us What character we are looking at right now
        """
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def peek(self, offset: int = 1) -> Optional[str]:
        """
        Look ahead without moving. 
        we will mostly use this for == <= >= etc.
        """
        p = self.pos + offset
        if p < len(self.source):
            return self.source[p]
        return None

    def advance(self) -> str:
        """
        Consume current character and move forward
        moves our pointer forward
        returns the current character 
        """
        ch = self.source[self.pos]
        self.pos += 1
        return ch

    def add_token(self, type: TokenType, value: str):
        """
        appends a completed token to our list
        """
        self.tokens.append(Token(type=type, value=value, line=self.line))

    def tokenize(self) -> List[Token]:
        """
        Walk through the entire source code character by character.
        For each position, scan one token and add it to the list.
        keep going untill the whole file has been covered
        """
        while self.pos < len(self.source):
            self.scan_token()

        self.add_token(TokenType.EOF, "")
        return self.tokens

    def scan_token(self):
        """
        Look at the current character and decide what token it starts.
        This is the heart of the lexer — one big decision tree.
        """
        ch = self.current()

        # the lexer will skip spaces and tabs
        # NOTE: we are not skipping new line character since they trigger indentation and those are treated differently
        if ch in (' ', '\t'):
            self.advance()
            return

        # we skip comments too  upto the end of the line
        if ch == '#':
            while self.current() and self.current() != '\n':
                self.advance()
            return

        # newline marks the end of a statement 
        # this triggers the indent check in our lexer
        if ch == '\n':
            self.add_token(TokenType.NEWLINE, "\\n")
            self.advance()
            self.line += 1
            self.handle_indent()
            return

        # this is not part of our language specification but  thought it is important we add it since it will help us alot in string formating
        if ch == 'f' and self.peek() in ('"', "'"):
            self.read_fstring()
            return

        # strings 
        # stringsa re denoted by single or double quotes
        if ch in ('"', "'"):
            self.read_string(ch)
            return

        # number : NOTE => We need to updat this to only work with integers so that our keyword will be INTEGER instead of NUMBBER
        if ch.isdigit():
            self.read_number()
            return

        # Word: could be keyword, boolean, logical op, or identifier NOTE : look more into this.
        if ch.isalpha() or ch == '_':
            self.read_word()
            return

        # COMPARE_OP => two character operators
        # we need to do the check before we do single character checks for operators
        two_char = self.source[self.pos: self.pos + 2]
        if two_char in ('==', '!=', '<=', '>='):
            self.add_token(TokenType.COMPARE_OP, two_char)
            self.pos += 2
            return

        # Single character compare ops 
        # remember we made these to run after the two_character checks
        if ch in ('<', '>'):
            self.add_token(TokenType.COMPARE_OP, ch)
            self.advance()
            return

        # Assignment 
        # This must come after two-character checks so that we dont catch == here
        if ch == '=':
            self.add_token(TokenType.ASSIGNMENT, ch)
            self.advance()
            return

        # Arithmetic operators
        if ch in ('+', '-', '*', '/'):
            self.add_token(TokenType.OPERATOR, ch)
            self.advance()
            return

        # Delimiters 
        if ch in ('(', ')', ':', ',', '[', ']'):
            self.add_token(TokenType.DELIMITER, ch)
            self.advance()
            return

        # Unknown character : for characters that are not defined in our minilanguage specification 
        # if we find such we raise / report an error to our error handler
        self.errors.report("Lexer", f"Unknown character '{ch}'", self.line)
        self.advance()

    #  READ METHODS
    #  Each one collects all characters
    #  that belong to one token

    def read_string(self, quote_char: str): # takes in the quote character ( either " or ')
        """
        Collects everything between matching quote characters ( strings are always between matching quote characters )
        NOTE : we take in the quote character as a parameter since python supports both single and double quotes 
        so at the end of string we need to confirm if the quote marches the opening quote in order to label the string
        a valid string  
        """
        self.advance()  # consume opening quote since it is not part os the string word itself
        result = ""
        while self.current() and self.current() != quote_char:
            if self.current() == '\n':
                self.errors.report("Lexer", "Unterminated string", self.line) # if string does not have the closing quote characters
                break
            result += self.advance()
        if self.current() == quote_char:
            self.advance()  # consume closing quote
        self.add_token(TokenType.STRING, result)

    def read_fstring(self):
        """
        Collect an f-string: f"some text {variable} more text"
        We store the entire content as one FSTRING token.
        The {variable} parts inside will be handled by the parser.
        """
        self.advance()  # consume 'f'
        quote_char = self.advance()  # consume opening quote and assign it to quote char so that we know when our string is valid
        result = ""
        while self.current() and self.current() != quote_char:
            if self.current() == '\n':
                self.errors.report("Lexer", "Unterminated f-string", self.line) # for strings with now closing quotes
                break
            result += self.advance()
        if self.current() == quote_char:
            self.advance()  # consume closing quote
        self.add_token(TokenType.FSTRING, result)

    def read_number(self):
        """
        Collect digits
        Also handles decimals like 3.14 NOTE : We need to make this only to support integers"""        
        num = ""
        while self.current() and self.current().isdigit():
            num += self.advance()
        # check for decimal point NOTE : We will remove this decimal suport as its not supposed to be ther since our language scope is not in supoort
        if self.current() == '.' and self.peek() and self.peek().isdigit():
            num += self.advance()  # consume '.'
            while self.current() and self.current().isdigit():
                num += self.advance()
        self.add_token(TokenType.NUMBER, num)

    def read_word(self):
        """
        Collect a full word (letters, digits, underscores).
        Then decide: is it a keyword, boolean, logical op, or identifier?
        """
        word = ""
        while self.current() and (self.current().isalnum() or self.current() == '_'):
            word += self.advance()

        if word in KEYWORDS:
            self.add_token(TokenType.KEYWORD, word)
        elif word in BOOLEANS:
            self.add_token(TokenType.BOOLEAN, word)
        elif word in LOGICAL_OPS:
            self.add_token(TokenType.LOGICAL_OP, word)
        else:
            self.add_token(TokenType.IDENTIFIER, word)

    def handle_indent(self):
        """
        Called after every newline.
        Counts spaces at the start of the new line.
        Compares to the previous indentation level.
        Emits INDENT if we went deeper, DEDENT if we came back out.
        """
        spaces = 0
        while self.current() in (' ', '\t'):
            spaces += 4 if self.current() == '\t' else 1 # if tab we add 4 spaces else we add 1 space only.
            self.advance()

        # our lexer will ignore all blank lines
        if self.current() == '\n' or self.current() is None:
            return

        current_level = self.indent_stack[-1] # tracks the current indentation level

        if spaces > current_level:
            # if spaces is greater than current level then it means that the indentatin went deaper
            self.indent_stack.append(spaces)
            self.add_token(TokenType.INDENT, f"INDENT({spaces})")

        elif spaces < current_level:
            # if spaces is less than the currnet indentation level then it means  that the indentation reduced
            while self.indent_stack[-1] > spaces:
                self.indent_stack.pop()
                self.add_token(TokenType.DEDENT, "DEDENT")

            # check the indentation is consistent
            if self.indent_stack[-1] != spaces:
                self.errors.report(
                    "Lexer",
                    f"Inconsistent indentation (got {spaces} spaces)",
                    self.line
                )