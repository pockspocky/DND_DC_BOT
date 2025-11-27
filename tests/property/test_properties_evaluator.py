"""
Property-Based Tests for Dice Evaluator
Tests correctness properties related to evaluation
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
from dice.expression_parser import parse
from dice.dice_evaluator import DiceEvaluator
from dice.ast_nodes import DiceNode, ConstantNode


# Property 3: Arithmetic operator precedence is respected (evaluator)
# Validates: Requirements 1.3, 8.3

@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=20),
    b=st.integers(min_value=1, max_value=20),
    c=st.integers(min_value=1, max_value=20)
)
def test_property_3_evaluator_arithmetic_precedence(a, b, c):
    """
    Feature: advanced-dice-roller, Property 3: Arithmetic operator precedence is respected
    
    For any expression with mixed operators, evaluation should follow
    standard mathematical precedence.
    """
    expression = f"{a} + {b} * {c}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    # Should evaluate as a + (b * c), not (a + b) * c
    expected = a + (b * c)
    assert result.final_value == expected


# Property 4: Parentheses override operator precedence (evaluator)
# Validates: Requirements 1.4

@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=20),
    b=st.integers(min_value=1, max_value=20),
    c=st.integers(min_value=1, max_value=20)
)
def test_property_4_evaluator_parentheses_override(a, b, c):
    """
    Feature: advanced-dice-roller, Property 4: Parentheses override operator precedence
    
    For any expression with parentheses, operations inside parentheses
    should be evaluated first.
    """
    expr_with_parens = f"({a} + {b}) * {c}"
    expr_without_parens = f"{a} + {b} * {c}"
    
    ast_with = parse(expr_with_parens)
    ast_without = parse(expr_without_parens)
    
    evaluator = DiceEvaluator()
    result_with = evaluator.evaluate(ast_with, expr_with_parens)
    result_without = evaluator.evaluate(ast_without, expr_without_parens)
    
    # With parentheses: (a + b) * c
    expected_with = (a + b) * c
    assert result_with.final_value == expected_with
    
    # Without parentheses: a + (b * c)
    expected_without = a + (b * c)
    assert result_without.final_value == expected_without
    
    # They should be different (unless by coincidence)
    if a != 0 and b != 0 and c != 1:
        assert result_with.final_value != result_without.final_value


# Additional evaluator tests

@settings(max_examples=100)
@given(
    value=st.integers(min_value=-1000, max_value=1000)
)
def test_evaluator_constant_node(value):
    """Test that constant nodes evaluate correctly"""
    node = ConstantNode(value=value)
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(node, str(value))
    
    assert result.final_value == value


@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=100),
    b=st.integers(min_value=1, max_value=100)
)
def test_evaluator_addition(a, b):
    """Test that addition evaluates correctly"""
    expression = f"{a} + {b}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    assert result.final_value == a + b


@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=100),
    b=st.integers(min_value=1, max_value=100)
)
def test_evaluator_subtraction(a, b):
    """Test that subtraction evaluates correctly"""
    expression = f"{a} - {b}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    assert result.final_value == a - b


@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=100),
    b=st.integers(min_value=1, max_value=100)
)
def test_evaluator_multiplication(a, b):
    """Test that multiplication evaluates correctly"""
    expression = f"{a} * {b}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    assert result.final_value == a * b


@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=100),
    b=st.integers(min_value=1, max_value=100)
)
def test_evaluator_division(a, b):
    """Test that division evaluates correctly"""
    expression = f"{a} / {b}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    assert result.final_value == int(a / b)


@settings(max_examples=100)
@given(
    value=st.integers(min_value=-100, max_value=100)
)
def test_evaluator_unary_negation(value):
    """Test that unary negation evaluates correctly"""
    expression = f"-{abs(value)}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    assert result.final_value == -abs(value)


def test_evaluator_division_by_zero():
    """Test that division by zero raises an error"""
    from dice.exceptions import EvaluationError
    
    expression = "10 / 0"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    with pytest.raises(EvaluationError) as exc_info:
        evaluator.evaluate(ast, expression)
    
    assert "division by zero" in str(exc_info.value).lower()


@settings(max_examples=50)
@given(
    dice_count=st.integers(min_value=1, max_value=10),
    die_size=st.integers(min_value=2, max_value=20)
)
def test_evaluator_basic_dice_roll(dice_count, die_size):
    """Test that basic dice rolls produce results in valid range"""
    expression = f"{dice_count}d{die_size}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    # Result should be between min and max possible
    min_possible = dice_count * 1
    max_possible = dice_count * die_size
    
    assert min_possible <= result.final_value <= max_possible
    
    # Should have dice results
    assert len(result.dice_results) == 1
    assert len(result.dice_results[0].rolls) == dice_count


@settings(max_examples=50)
@given(
    dice_count=st.integers(min_value=1, max_value=10),
    die_size=st.integers(min_value=2, max_value=20),
    modifier=st.integers(min_value=-10, max_value=10)
)
def test_evaluator_dice_with_modifier(dice_count, die_size, modifier):
    """Test that dice with modifiers evaluate correctly"""
    expression = f"{dice_count}d{die_size}{modifier:+d}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    # Result should be between min and max possible
    min_possible = dice_count * 1 + modifier
    max_possible = dice_count * die_size + modifier
    
    assert min_possible <= result.final_value <= max_possible



# Property 1: Basic dice rolling produces correct count and range
# Validates: Requirements 1.1

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=100),
    die_size=st.integers(min_value=2, max_value=100)
)
def test_property_1_basic_dice_rolling_count_and_range(dice_count, die_size):
    """
    Feature: advanced-dice-roller, Property 1: Basic dice rolling produces correct count and range
    
    For any valid dice expression "XdY", rolling the expression should produce
    exactly X results, each with a value between 1 and Y inclusive.
    """
    expression = f"{dice_count}d{die_size}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    # Should have exactly one dice result
    assert len(result.dice_results) == 1
    dice_result = result.dice_results[0]
    
    # Should have exactly dice_count rolls
    assert len(dice_result.rolls) == dice_count
    
    # Each roll should be between 1 and die_size
    for roll in dice_result.rolls:
        assert 1 <= roll.final_value <= die_size
        assert 1 <= roll.original_value <= die_size
    
    # Total should be sum of all rolls
    expected_total = sum(roll.final_value for roll in dice_result.rolls if roll.kept)
    assert dice_result.total == expected_total
    assert result.final_value == expected_total
