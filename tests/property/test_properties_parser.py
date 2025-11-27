"""
Property-Based Tests for Expression Parser
Tests correctness properties related to parsing
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
from dice.expression_parser import parse, validate, ParseError
from dice.ast_nodes import (
    ASTNode, ConstantNode, DiceNode, BinaryOpNode, UnaryOpNode,
    NodeType, SuccessCountNode
)


# Property 2: Omitted dice count defaults to one
# Validates: Requirements 1.2

@settings(max_examples=100)
@given(
    die_size=st.integers(min_value=2, max_value=100)
)
def test_property_2_omitted_dice_count_defaults_to_one(die_size):
    """
    Feature: advanced-dice-roller, Property 2: Omitted dice count defaults to one
    
    For any die size Y, parsing the expression "dY" should be equivalent
    to parsing "1dY" (both should produce a DiceNode with count=1).
    """
    expr1 = f"d{die_size}"
    expr2 = f"1d{die_size}"
    
    ast1 = parse(expr1)
    ast2 = parse(expr2)
    
    # Both should be DiceNode
    assert isinstance(ast1, DiceNode)
    assert isinstance(ast2, DiceNode)
    
    # Both should have count=1 and same size
    assert ast1.count == 1
    assert ast2.count == 1
    assert ast1.size == die_size
    assert ast2.size == die_size


# Property 3: Arithmetic operator precedence is respected
# Validates: Requirements 1.3, 8.3

@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=20),
    b=st.integers(min_value=1, max_value=20),
    c=st.integers(min_value=1, max_value=20)
)
def test_property_3_arithmetic_precedence_multiplication_before_addition(a, b, c):
    """
    Feature: advanced-dice-roller, Property 3: Arithmetic operator precedence is respected
    
    For any expression with mixed operators, multiplication should be evaluated
    before addition: "a + b * c" should parse as "a + (b * c)", not "(a + b) * c"
    """
    expression = f"{a} + {b} * {c}"
    ast = parse(expression)
    
    # Should be: BinaryOp(+, Constant(a), BinaryOp(*, Constant(b), Constant(c)))
    assert isinstance(ast, BinaryOpNode)
    assert ast.operator == "+"
    assert isinstance(ast.left, ConstantNode)
    assert ast.left.value == a
    assert isinstance(ast.right, BinaryOpNode)
    assert ast.right.operator == "*"
    assert isinstance(ast.right.left, ConstantNode)
    assert ast.right.left.value == b
    assert isinstance(ast.right.right, ConstantNode)
    assert ast.right.right.value == c


@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=20),
    b=st.integers(min_value=1, max_value=20),
    c=st.integers(min_value=1, max_value=20)
)
def test_property_3_arithmetic_precedence_division_before_subtraction(a, b, c):
    """
    Test that division is evaluated before subtraction
    """
    assume(c != 0)  # Avoid division by zero
    expression = f"{a} - {b} / {c}"
    ast = parse(expression)
    
    # Should be: BinaryOp(-, Constant(a), BinaryOp(/, Constant(b), Constant(c)))
    assert isinstance(ast, BinaryOpNode)
    assert ast.operator == "-"
    assert isinstance(ast.left, ConstantNode)
    assert isinstance(ast.right, BinaryOpNode)
    assert ast.right.operator == "/"


# Property 4: Parentheses override operator precedence
# Validates: Requirements 1.4

@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=20),
    b=st.integers(min_value=1, max_value=20),
    c=st.integers(min_value=1, max_value=20)
)
def test_property_4_parentheses_override_precedence(a, b, c):
    """
    Feature: advanced-dice-roller, Property 4: Parentheses override operator precedence
    
    For any expression with parentheses, operations inside parentheses should
    be evaluated first: "(a + b) * c" should parse differently from "a + b * c"
    """
    expr_with_parens = f"({a} + {b}) * {c}"
    expr_without_parens = f"{a} + {b} * {c}"
    
    ast_with = parse(expr_with_parens)
    ast_without = parse(expr_without_parens)
    
    # With parentheses: BinaryOp(*, BinaryOp(+, a, b), c)
    assert isinstance(ast_with, BinaryOpNode)
    assert ast_with.operator == "*"
    assert isinstance(ast_with.left, BinaryOpNode)
    assert ast_with.left.operator == "+"
    
    # Without parentheses: BinaryOp(+, a, BinaryOp(*, b, c))
    assert isinstance(ast_without, BinaryOpNode)
    assert ast_without.operator == "+"
    assert isinstance(ast_without.right, BinaryOpNode)
    assert ast_without.right.operator == "*"
    
    # They should have different structures
    assert type(ast_with.left) != type(ast_without.left)


# Property 28: Parser produces AST for valid expressions
# Validates: Requirements 8.1

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=100),
    die_size=st.integers(min_value=2, max_value=100),
    modifier=st.integers(min_value=-20, max_value=20)
)
def test_property_28_parser_produces_ast(dice_count, die_size, modifier):
    """
    Feature: advanced-dice-roller, Property 28: Parser produces AST for valid expressions
    
    For any valid dice expression, the parser should successfully produce
    an Abstract Syntax Tree representation without errors.
    """
    expression = f"{dice_count}d{die_size}"
    if modifier != 0:
        expression += f"{modifier:+d}"
    
    # Should parse without error
    ast = parse(expression)
    
    # Should return an ASTNode
    assert isinstance(ast, ASTNode)
    
    # Should have a node_type
    assert hasattr(ast, 'node_type')
    assert ast.node_type in [NodeType.DICE, NodeType.BINARY_OP, NodeType.CONSTANT]


# Property 29: Nested parentheses parse correctly
# Validates: Requirements 8.2

@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=10),
    b=st.integers(min_value=1, max_value=10),
    c=st.integers(min_value=1, max_value=10),
    d=st.integers(min_value=1, max_value=10)
)
def test_property_29_nested_parentheses(a, b, c, d):
    """
    Feature: advanced-dice-roller, Property 29: Nested parentheses parse correctly
    
    For any expression with multiple levels of nested parentheses,
    the parser should correctly build an AST that respects the nesting structure.
    """
    expression = f"(({a} + {b}) * ({c} + {d}))"
    
    # Should parse without error
    ast = parse(expression)
    
    # Should be: BinaryOp(*, BinaryOp(+, a, b), BinaryOp(+, c, d))
    assert isinstance(ast, BinaryOpNode)
    assert ast.operator == "*"
    assert isinstance(ast.left, BinaryOpNode)
    assert ast.left.operator == "+"
    assert isinstance(ast.right, BinaryOpNode)
    assert ast.right.operator == "+"


@settings(max_examples=100)
@given(
    depth=st.integers(min_value=1, max_value=5),
    value=st.integers(min_value=1, max_value=100)
)
def test_property_29_deeply_nested_parentheses(depth, value):
    """
    Test that deeply nested parentheses parse correctly
    """
    # Create expression with nested parentheses: ((((value))))
    expression = "(" * depth + str(value) + ")" * depth
    
    # Should parse without error
    ast = parse(expression)
    
    # Should ultimately resolve to a constant
    assert isinstance(ast, ConstantNode)
    assert ast.value == value


# Property 30: Complex multi-dice expressions parse correctly
# Validates: Requirements 8.4

@settings(max_examples=100)
@given(
    dice1_count=st.integers(min_value=1, max_value=10),
    dice1_size=st.integers(min_value=2, max_value=20),
    dice2_count=st.integers(min_value=1, max_value=10),
    dice2_size=st.integers(min_value=2, max_value=20),
    constant=st.integers(min_value=1, max_value=10)
)
def test_property_30_complex_multi_dice_expressions(dice1_count, dice1_size, dice2_count, dice2_size, constant):
    """
    Feature: advanced-dice-roller, Property 30: Complex multi-dice expressions parse correctly
    
    For any expression containing multiple dice terms and constants,
    the parser should successfully produce an AST representing all components.
    """
    expression = f"{dice1_count}d{dice1_size} + {dice2_count}d{dice2_size} + {constant}"
    
    # Should parse without error
    ast = parse(expression)
    
    # Should be a binary operation (addition)
    assert isinstance(ast, BinaryOpNode)
    assert ast.operator == "+"
    
    # Should have nested structure with dice and constants
    # The exact structure depends on left-to-right parsing
    # But we should be able to find both dice terms and the constant somewhere in the tree
    def find_dice_nodes(node):
        """Recursively find all DiceNode instances"""
        if isinstance(node, DiceNode):
            return [node]
        elif isinstance(node, BinaryOpNode):
            return find_dice_nodes(node.left) + find_dice_nodes(node.right)
        elif isinstance(node, UnaryOpNode):
            return find_dice_nodes(node.operand)
        return []
    
    def find_constant_nodes(node):
        """Recursively find all ConstantNode instances"""
        if isinstance(node, ConstantNode):
            return [node]
        elif isinstance(node, BinaryOpNode):
            return find_constant_nodes(node.left) + find_constant_nodes(node.right)
        elif isinstance(node, UnaryOpNode):
            return find_constant_nodes(node.operand)
        return []
    
    dice_nodes = find_dice_nodes(ast)
    constant_nodes = find_constant_nodes(ast)
    
    # Should have 2 dice nodes and 1 constant node
    assert len(dice_nodes) == 2
    assert len(constant_nodes) == 1


# Property 31: Invalid syntax produces error messages
# Validates: Requirements 9.1

@settings(max_examples=100)
@given(
    invalid_expr=st.sampled_from([
        "d",           # Missing die size
        "2d",          # Missing die size
        "d20d6",       # Two dice without operator
        "1d20+",       # Trailing operator
        "+1d20",       # Leading operator (actually valid as unary, so skip this)
        "1d20 1d6",    # Missing operator between dice
        "((1d20)",     # Unmatched parentheses
        "1d20))",      # Unmatched parentheses
        "1d20kh",      # Missing argument for operator
        "1d20>=",      # Missing threshold for comparison
    ])
)
def test_property_31_invalid_syntax_produces_errors(invalid_expr):
    """
    Feature: advanced-dice-roller, Property 31: Invalid syntax produces error messages
    
    For any syntactically invalid dice expression, the parser should
    raise an error with a user-friendly message explaining the issue.
    """
    # Skip expressions that are actually valid
    if invalid_expr == "+1d20":
        return
    
    # Should raise ParseError
    with pytest.raises((ParseError, ValueError)) as exc_info:
        parse(invalid_expr)
    
    # Error message should be informative
    error_message = str(exc_info.value)
    assert len(error_message) > 0
    # Should mention what went wrong
    assert any(word in error_message.lower() for word in ['expected', 'unexpected', 'invalid', 'missing'])


# Additional parser tests

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=100),
    die_size=st.integers(min_value=2, max_value=100),
    keep_count=st.integers(min_value=1, max_value=10)
)
def test_parser_keep_highest_operator(dice_count, die_size, keep_count):
    """Test that keep highest operator parses correctly"""
    expression = f"{dice_count}d{die_size}kh{keep_count}"
    ast = parse(expression)
    
    assert isinstance(ast, DiceNode)
    assert ast.count == dice_count
    assert ast.size == die_size
    assert ast.keep_highest == keep_count


@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=100),
    die_size=st.integers(min_value=2, max_value=100),
    reroll_value=st.integers(min_value=1, max_value=10)
)
def test_parser_reroll_operator(dice_count, die_size, reroll_value):
    """Test that reroll operator parses correctly"""
    expression = f"{dice_count}d{die_size}r{reroll_value}"
    ast = parse(expression)
    
    assert isinstance(ast, DiceNode)
    assert ast.reroll == reroll_value
    assert ast.reroll_once == True


@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=100),
    die_size=st.integers(min_value=2, max_value=100),
    threshold=st.integers(min_value=1, max_value=10)
)
def test_parser_success_counting(dice_count, die_size, threshold):
    """Test that success counting parses correctly"""
    expression = f"{dice_count}d{die_size}>={threshold}"
    ast = parse(expression)
    
    assert isinstance(ast, SuccessCountNode)
    assert isinstance(ast.dice, DiceNode)
    assert ast.dice.count == dice_count
    assert ast.dice.size == die_size
    assert ast.threshold == threshold


def test_parser_validate_function():
    """Test the validate convenience function"""
    # Valid expression
    is_valid, message = validate("2d20kh1+5")
    assert is_valid == True
    assert "valid" in message.lower()
    
    # Invalid expression
    is_valid, message = validate("2d")
    assert is_valid == False
    assert len(message) > 0
