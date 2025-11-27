"""
Tokenizer for Dice Expressions
Converts dice expression strings into tokens for parsing
"""
import re
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class TokenType(Enum):
    """Types of tokens in dice expressions"""
    NUMBER = "number"
    DICE = "dice"  # 'd' character
    PLUS = "plus"
    MINUS = "minus"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    FLOOR_DIVIDE = "floor_divide"
    LPAREN = "lparen"
    RPAREN = "rparen"
    KEEP_HIGH = "kh"
    KEEP_LOW = "kl"
    DROP_HIGH = "dh"
    DROP_LOW = "dl"
    REROLL = "r"
    REROLL_ONCE = "ro"
    MIN = "min"
    MAX = "max"
    SORT_ASC = "s"
    SORT_DESC = "sd"
    COMPARE_GE = ">="
    COMPARE_LE = "<="
    COMPARE_GT = ">"
    COMPARE_LT = "<"
    COMPARE_EQ = "="
    EOF = "eof"


@dataclass
class Token:
    """A single token from the input"""
    type: TokenType
    value: any
    position: int
    
    def __repr__(self) -> str:
        return f"Token({self.type.value}, {self.value}, pos={self.position})"


class UnsupportedFeatureError(Exception):
    """Raised when expression uses unsupported features"""
    pass


class Tokenizer:
    """Tokenizes dice expression strings"""
    
    # Patterns for unsupported features
    EXPLODING_PATTERN = re.compile(r'!+p?')
    TABLE_PATTERN = re.compile(r'\b(table|rolltable)\b', re.IGNORECASE)
    
    def __init__(self, expression: str):
        self.expression = expression.strip()
        self.position = 0
        self.current_char: Optional[str] = self.expression[0] if self.expression else None
    
    def error(self, message: str) -> Exception:
        """Create an error with position information"""
        return ValueError(f"{message} at position {self.position}")
    
    def advance(self) -> None:
        """Move to the next character"""
        self.position += 1
        if self.position < len(self.expression):
            self.current_char = self.expression[self.position]
        else:
            self.current_char = None
    
    def peek(self, offset: int = 1) -> Optional[str]:
        """Look ahead at the next character(s) without advancing"""
        peek_pos = self.position + offset
        if peek_pos < len(self.expression):
            return self.expression[peek_pos]
        return None
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters"""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()
    
    def read_number(self) -> int:
        """Read a multi-digit number"""
        start_pos = self.position
        num_str = ''
        while self.current_char is not None and self.current_char.isdigit():
            num_str += self.current_char
            self.advance()
        
        if not num_str:
            raise self.error("Expected number")
        
        return int(num_str)
    
    def read_operator(self) -> Optional[Token]:
        """Read multi-character operators (kh, kl, dh, dl, ro, min, max, sd, >=, <=)"""
        start_pos = self.position
        
        # Check for two-character comparison operators
        if self.current_char in ['>', '<', '=']:
            if self.current_char == '>' and self.peek() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.COMPARE_GE, ">=", start_pos)
            elif self.current_char == '<' and self.peek() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.COMPARE_LE, "<=", start_pos)
            elif self.current_char == '>':
                self.advance()
                return Token(TokenType.COMPARE_GT, ">", start_pos)
            elif self.current_char == '<':
                self.advance()
                return Token(TokenType.COMPARE_LT, "<", start_pos)
            elif self.current_char == '=':
                self.advance()
                return Token(TokenType.COMPARE_EQ, "=", start_pos)
        
        # Check for letter-based operators
        if self.current_char and self.current_char.isalpha():
            op_str = ''
            while self.current_char and self.current_char.isalpha():
                op_str += self.current_char.lower()
                self.advance()
            
            # Check for multi-character operators
            if op_str == 'kh':
                return Token(TokenType.KEEP_HIGH, "kh", start_pos)
            elif op_str == 'kl':
                return Token(TokenType.KEEP_LOW, "kl", start_pos)
            elif op_str == 'dh':
                return Token(TokenType.DROP_HIGH, "dh", start_pos)
            elif op_str == 'dl':
                return Token(TokenType.DROP_LOW, "dl", start_pos)
            elif op_str == 'ro':
                return Token(TokenType.REROLL_ONCE, "ro", start_pos)
            elif op_str == 'min':
                return Token(TokenType.MIN, "min", start_pos)
            elif op_str == 'max':
                return Token(TokenType.MAX, "max", start_pos)
            elif op_str == 'sd':
                return Token(TokenType.SORT_DESC, "sd", start_pos)
            elif op_str == 's':
                return Token(TokenType.SORT_ASC, "s", start_pos)
            elif op_str == 'r':
                return Token(TokenType.REROLL, "r", start_pos)
            elif op_str == 'd':
                return Token(TokenType.DICE, "d", start_pos)
            else:
                # Reset position and return None for unknown operators
                self.position = start_pos
                self.current_char = self.expression[self.position] if self.position < len(self.expression) else None
                return None
        
        return None
    
    def check_unsupported_features(self) -> None:
        """Check for unsupported features and raise errors"""
        # Check for exploding dice
        if self.EXPLODING_PATTERN.search(self.expression):
            raise UnsupportedFeatureError(
                "Exploding dice are not supported in this bot. "
                "Please remove !, !!, or !p from your expression."
            )
        
        # Check for table rolls
        if self.TABLE_PATTERN.search(self.expression):
            raise UnsupportedFeatureError(
                "Table rolls are not supported in this bot. "
                "Please remove 'table' or 'rolltable' from your expression."
            )
    
    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire expression
        
        Returns:
            List of tokens
            
        Raises:
            UnsupportedFeatureError: If expression uses unsupported features
            ValueError: If expression has invalid syntax
        """
        # First check for unsupported features
        self.check_unsupported_features()
        
        tokens: List[Token] = []
        
        while self.current_char is not None:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # Numbers
            if self.current_char.isdigit():
                start_pos = self.position
                number = self.read_number()
                tokens.append(Token(TokenType.NUMBER, number, start_pos))
                continue
            
            # Try to read multi-character operators
            operator_token = self.read_operator()
            if operator_token:
                tokens.append(operator_token)
                continue
            
            # Single character tokens
            start_pos = self.position
            
            if self.current_char == '+':
                tokens.append(Token(TokenType.PLUS, "+", start_pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TokenType.MINUS, "-", start_pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TokenType.MULTIPLY, "*", start_pos))
                self.advance()
            elif self.current_char == '/':
                # Check for floor division //
                if self.peek() == '/':
                    tokens.append(Token(TokenType.FLOOR_DIVIDE, "//", start_pos))
                    self.advance()
                    self.advance()
                else:
                    tokens.append(Token(TokenType.DIVIDE, "/", start_pos))
                    self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TokenType.LPAREN, "(", start_pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TokenType.RPAREN, ")", start_pos))
                self.advance()
            else:
                raise self.error(f"Unexpected character: '{self.current_char}'")
        
        # Add EOF token
        tokens.append(Token(TokenType.EOF, None, self.position))
        
        return tokens


def tokenize(expression: str) -> List[Token]:
    """
    Convenience function to tokenize an expression
    
    Args:
        expression: Dice expression string
        
    Returns:
        List of tokens
        
    Raises:
        UnsupportedFeatureError: If expression uses unsupported features
        ValueError: If expression has invalid syntax
    """
    tokenizer = Tokenizer(expression)
    return tokenizer.tokenize()
