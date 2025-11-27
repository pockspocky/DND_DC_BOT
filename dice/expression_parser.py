"""
Expression Parser for Dice Expressions
Implements recursive descent parser with operator precedence
"""
from typing import List, Optional
from dice.tokenizer import Token, TokenType, tokenize, UnsupportedFeatureError
from dice.ast_nodes import (
    ASTNode, ConstantNode, DiceNode, SuccessCountNode,
    BinaryOpNode, UnaryOpNode, ComparisonOp
)
from dice.exceptions import ParseError, ValidationError


# Validation limits
MAX_DICE_COUNT = 10_000
MAX_DIE_SIZE = 1_000_000
MAX_EXPRESSION_DEPTH = 50
MAX_EXPRESSION_LENGTH = 1_000


class DiceParser:
    """
    Recursive descent parser for dice expressions
    
    Grammar (simplified):
    expression := additive
    additive := multiplicative (('+' | '-') multiplicative)*
    multiplicative := unary (('*' | '/' | '//') unary)*
    unary := ('+' | '-') unary | primary
    primary := dice_term | constant | '(' expression ')'
    dice_term := [NUMBER] 'd' NUMBER [operators] [comparison]
    operators := (reroll | clamp | keep_drop | sort)*
    comparison := ('>' | '<' | '>=' | '<=' | '=') NUMBER
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.current_token = tokens[0] if tokens else None
        self.depth = 0  # Track nesting depth
    
    def error(self, message: str) -> ParseError:
        """Create a parse error with position information"""
        if self.current_token:
            return ParseError(
                f"{message} at position {self.current_token.position}, "
                f"got {self.current_token.type.value}"
            )
        return ParseError(f"{message} at end of expression")
    
    def advance(self) -> None:
        """Move to the next token"""
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None
    
    def peek(self, offset: int = 1) -> Optional[Token]:
        """Look ahead at the next token(s) without advancing"""
        peek_pos = self.position + offset
        if peek_pos < len(self.tokens):
            return self.tokens[peek_pos]
        return None
    
    def expect(self, token_type: TokenType) -> Token:
        """Consume a token of the expected type or raise an error"""
        if not self.current_token or self.current_token.type != token_type:
            raise self.error(f"Expected {token_type.value}")
        token = self.current_token
        self.advance()
        return token
    
    def parse(self) -> ASTNode:
        """
        Parse the token stream into an AST
        
        Returns:
            Root AST node
            
        Raises:
            ParseError: If parsing fails
        """
        if not self.tokens or self.tokens[0].type == TokenType.EOF:
            raise ParseError("Empty expression")
        
        # Parse the expression
        ast = self.parse_expression()
        
        # Should be at EOF
        if self.current_token and self.current_token.type != TokenType.EOF:
            raise self.error("Unexpected token after expression")
        
        return ast
    
    def parse_expression(self) -> ASTNode:
        """Parse a complete expression (entry point)"""
        return self.parse_additive()
    
    def parse_additive(self) -> ASTNode:
        """Parse addition and subtraction (lowest precedence)"""
        left = self.parse_multiplicative()
        
        while self.current_token and self.current_token.type in [TokenType.PLUS, TokenType.MINUS]:
            operator = self.current_token.value
            self.advance()
            right = self.parse_multiplicative()
            left = BinaryOpNode(operator=operator, left=left, right=right)
        
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        """Parse multiplication and division"""
        left = self.parse_unary()
        
        while self.current_token and self.current_token.type in [
            TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.FLOOR_DIVIDE
        ]:
            operator = self.current_token.value
            self.advance()
            right = self.parse_unary()
            left = BinaryOpNode(operator=operator, left=left, right=right)
        
        return left
    
    def parse_unary(self) -> ASTNode:
        """Parse unary operators (+ and -)"""
        if self.current_token and self.current_token.type in [TokenType.PLUS, TokenType.MINUS]:
            operator = self.current_token.value
            self.advance()
            operand = self.parse_unary()  # Right-associative
            return UnaryOpNode(operator=operator, operand=operand)
        
        return self.parse_primary()
    
    def parse_primary(self) -> ASTNode:
        """Parse primary expressions (dice, constants, parentheses)"""
        # Parenthesized expression
        if self.current_token and self.current_token.type == TokenType.LPAREN:
            self.depth += 1
            if self.depth > MAX_EXPRESSION_DEPTH:
                raise ValidationError(
                    f"Expression nesting depth exceeds maximum of {MAX_EXPRESSION_DEPTH}"
                )
            self.advance()  # consume '('
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            self.depth -= 1
            return expr
        
        # Dice term (starts with 'd' or number followed by 'd')
        if self.current_token and (
            self.current_token.type == TokenType.DICE or
            (self.current_token.type == TokenType.NUMBER and 
             self.peek() and self.peek().type == TokenType.DICE)
        ):
            return self.parse_dice_term()
        
        # Constant
        if self.current_token and self.current_token.type == TokenType.NUMBER:
            value = self.current_token.value
            self.advance()
            return ConstantNode(value=value)
        
        raise self.error("Expected dice term, number, or '('")
    
    def parse_dice_term(self) -> ASTNode:
        """
        Parse a dice term with optional operators
        
        Format: [count]d<size>[operators][comparison]
        """
        # Parse dice count (optional, defaults to 1)
        if self.current_token.type == TokenType.NUMBER:
            count = self.current_token.value
            self.advance()
        else:
            count = 1
        
        # Expect 'd'
        self.expect(TokenType.DICE)
        
        # Parse die size
        if not self.current_token or self.current_token.type != TokenType.NUMBER:
            raise self.error("Expected die size after 'd'")
        size = self.current_token.value
        self.advance()
        
        # Validate dice count and size
        if count > MAX_DICE_COUNT:
            raise ValidationError(
                f"Dice count {count} exceeds maximum of {MAX_DICE_COUNT}"
            )
        if size > MAX_DIE_SIZE:
            raise ValidationError(
                f"Die size {size} exceeds maximum of {MAX_DIE_SIZE}"
            )
        if count < 1:
            raise ValidationError("Dice count must be at least 1")
        if size < 2:
            raise ValidationError("Die size must be at least 2")
        
        # Create dice node
        dice_node = DiceNode(count=count, size=size)
        
        # Parse optional operators
        self.parse_dice_operators(dice_node)
        
        # Check for success counting comparison
        if self.current_token and self.current_token.type in [
            TokenType.COMPARE_GE, TokenType.COMPARE_LE,
            TokenType.COMPARE_GT, TokenType.COMPARE_LT, TokenType.COMPARE_EQ
        ]:
            return self.parse_success_count(dice_node)
        
        return dice_node
    
    def parse_dice_operators(self, dice_node: DiceNode) -> None:
        """
        Parse dice operators and update the dice node
        
        Operators can appear in any order, but are applied in a specific order:
        1. Reroll (r/ro)
        2. Min/Max clamping
        3. Keep/Drop (kh/kl/dh/dl)
        4. Sort (s/sd)
        """
        while self.current_token and self.current_token.type in [
            TokenType.REROLL, TokenType.REROLL_ONCE,
            TokenType.MIN, TokenType.MAX,
            TokenType.KEEP_HIGH, TokenType.KEEP_LOW,
            TokenType.DROP_HIGH, TokenType.DROP_LOW,
            TokenType.SORT_ASC, TokenType.SORT_DESC
        ]:
            op_type = self.current_token.type
            self.advance()
            
            # Most operators require a number argument
            if op_type in [TokenType.SORT_ASC, TokenType.SORT_DESC]:
                # Sort operators don't take arguments
                if op_type == TokenType.SORT_ASC:
                    dice_node.sort_ascending = True
                else:
                    dice_node.sort_descending = True
            else:
                # All other operators require a number
                if not self.current_token or self.current_token.type != TokenType.NUMBER:
                    raise self.error(f"Expected number after {op_type.value}")
                value = self.current_token.value
                self.advance()
                
                # Apply the operator
                if op_type == TokenType.REROLL:
                    dice_node.reroll = value
                    dice_node.reroll_once = True
                elif op_type == TokenType.REROLL_ONCE:
                    dice_node.reroll = value
                    dice_node.reroll_once = False
                elif op_type == TokenType.MIN:
                    dice_node.min_value = value
                elif op_type == TokenType.MAX:
                    dice_node.max_value = value
                elif op_type == TokenType.KEEP_HIGH:
                    dice_node.keep_highest = value
                elif op_type == TokenType.KEEP_LOW:
                    dice_node.keep_lowest = value
                elif op_type == TokenType.DROP_HIGH:
                    dice_node.drop_highest = value
                elif op_type == TokenType.DROP_LOW:
                    dice_node.drop_lowest = value
    
    def parse_success_count(self, dice_node: DiceNode) -> SuccessCountNode:
        """Parse success counting comparison"""
        # Get comparison operator
        comparison_token = self.current_token
        self.advance()
        
        # Map token type to ComparisonOp
        comparison_map = {
            TokenType.COMPARE_GE: ComparisonOp.GREATER_EQUAL,
            TokenType.COMPARE_LE: ComparisonOp.LESS_EQUAL,
            TokenType.COMPARE_GT: ComparisonOp.GREATER,
            TokenType.COMPARE_LT: ComparisonOp.LESS,
            TokenType.COMPARE_EQ: ComparisonOp.EQUAL,
        }
        comparison = comparison_map[comparison_token.type]
        
        # Get threshold value
        if not self.current_token or self.current_token.type != TokenType.NUMBER:
            raise self.error("Expected number after comparison operator")
        threshold = self.current_token.value
        self.advance()
        
        return SuccessCountNode(dice=dice_node, comparison=comparison, threshold=threshold)


def parse(expression: str) -> ASTNode:
    """
    Parse a dice expression string into an AST
    
    Args:
        expression: Dice expression string
        
    Returns:
        Root AST node
        
    Raises:
        UnsupportedFeatureError: If expression uses unsupported features
        ParseError: If expression has invalid syntax
        ValidationError: If expression exceeds limits
    """
    # Check expression length
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValidationError(
            f"Expression length {len(expression)} exceeds maximum of {MAX_EXPRESSION_LENGTH}"
        )
    
    # Tokenize (this will check for unsupported features)
    tokens = tokenize(expression)
    
    # Parse tokens into AST
    parser = DiceParser(tokens)
    return parser.parse()


def validate(expression: str) -> tuple[bool, str]:
    """
    Validate a dice expression without fully parsing
    
    Args:
        expression: Dice expression string
        
    Returns:
        (is_valid, error_message) tuple
    """
    try:
        parse(expression)
        return (True, "Expression is valid")
    except UnsupportedFeatureError as e:
        return (False, str(e))
    except ParseError as e:
        return (False, str(e))
    except ValidationError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"Unexpected error: {str(e)}")
