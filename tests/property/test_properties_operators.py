"""
Property-Based Tests for Dice Operators
Tests correctness properties for reroll, clamp, keep/drop, and success counting
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
from dice.expression_parser import parse
from dice.dice_evaluator import DiceEvaluator
from dice.exceptions import EvaluationError


# Property 5: Keep highest retains only the N highest dice
# Validates: Requirements 2.1, 3.1

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=2, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    keep_count=st.integers(min_value=1, max_value=10)
)
def test_property_5_keep_highest(dice_count, die_size, keep_count):
    """
    Feature: advanced-dice-roller, Property 5: Keep highest retains only the N highest dice
    
    For any dice pool "XdYkhN", after rolling X dice, exactly N dice should be
    marked as kept, and those N dice should be the highest values from the pool.
    """
    assume(keep_count <= dice_count)
    
    expression = f"{dice_count}d{die_size}kh{keep_count}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    kept_rolls = [r for r in dice_result.rolls if r.kept]
    dropped_rolls = [r for r in dice_result.rolls if not r.kept]
    
    # Should have exactly keep_count kept dice
    assert len(kept_rolls) == keep_count
    assert len(dropped_rolls) == dice_count - keep_count
    
    # All kept dice should be >= all dropped dice
    if dropped_rolls:
        min_kept = min(r.final_value for r in kept_rolls)
        max_dropped = max(r.final_value for r in dropped_rolls)
        assert min_kept >= max_dropped


# Property 6: Keep lowest retains only the N lowest dice
# Validates: Requirements 2.2, 3.2

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=2, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    keep_count=st.integers(min_value=1, max_value=10)
)
def test_property_6_keep_lowest(dice_count, die_size, keep_count):
    """
    Feature: advanced-dice-roller, Property 6: Keep lowest retains only the N lowest dice
    
    For any dice pool "XdYklN", after rolling X dice, exactly N dice should be
    marked as kept, and those N dice should be the lowest values from the pool.
    """
    assume(keep_count <= dice_count)
    
    expression = f"{dice_count}d{die_size}kl{keep_count}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    kept_rolls = [r for r in dice_result.rolls if r.kept]
    dropped_rolls = [r for r in dice_result.rolls if not r.kept]
    
    # Should have exactly keep_count kept dice
    assert len(kept_rolls) == keep_count
    assert len(dropped_rolls) == dice_count - keep_count
    
    # All kept dice should be <= all dropped dice
    if dropped_rolls:
        max_kept = max(r.final_value for r in kept_rolls)
        min_dropped = min(r.final_value for r in dropped_rolls)
        assert max_kept <= min_dropped


# Property 7: Drop highest removes the N highest dice
# Validates: Requirements 3.3

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=2, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    drop_count=st.integers(min_value=1, max_value=10)
)
def test_property_7_drop_highest(dice_count, die_size, drop_count):
    """
    Feature: advanced-dice-roller, Property 7: Drop highest removes the N highest dice
    
    For any dice pool "XdYdhN", after rolling X dice, exactly N dice should be
    marked as dropped, and those N dice should be the highest values from the pool.
    """
    assume(drop_count < dice_count)
    
    expression = f"{dice_count}d{die_size}dh{drop_count}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    kept_rolls = [r for r in dice_result.rolls if r.kept]
    dropped_rolls = [r for r in dice_result.rolls if not r.kept]
    
    # Should have exactly drop_count dropped dice
    assert len(dropped_rolls) == drop_count
    assert len(kept_rolls) == dice_count - drop_count
    
    # All dropped dice should be >= all kept dice
    if kept_rolls and dropped_rolls:
        min_dropped = min(r.final_value for r in dropped_rolls)
        max_kept = max(r.final_value for r in kept_rolls)
        assert min_dropped >= max_kept


# Property 8: Drop lowest removes the N lowest dice
# Validates: Requirements 3.4

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=2, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    drop_count=st.integers(min_value=1, max_value=10)
)
def test_property_8_drop_lowest(dice_count, die_size, drop_count):
    """
    Feature: advanced-dice-roller, Property 8: Drop lowest removes the N lowest dice
    
    For any dice pool "XdYdlN", after rolling X dice, exactly N dice should be
    marked as dropped, and those N dice should be the lowest values from the pool.
    """
    assume(drop_count < dice_count)
    
    expression = f"{dice_count}d{die_size}dl{drop_count}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    kept_rolls = [r for r in dice_result.rolls if r.kept]
    dropped_rolls = [r for r in dice_result.rolls if not r.kept]
    
    # Should have exactly drop_count dropped dice
    assert len(dropped_rolls) == drop_count
    assert len(kept_rolls) == dice_count - drop_count
    
    # All dropped dice should be <= all kept dice
    if kept_rolls and dropped_rolls:
        max_dropped = max(r.final_value for r in dropped_rolls)
        min_kept = min(r.final_value for r in kept_rolls)
        assert max_dropped <= min_kept


# Property 21: Min clamping enforces lower bound
# Validates: Requirements 6.1

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=10),
    die_size=st.integers(min_value=4, max_value=20),
    min_value=st.integers(min_value=2, max_value=10)
)
def test_property_21_min_clamping(dice_count, die_size, min_value):
    """
    Feature: advanced-dice-roller, Property 21: Min clamping enforces lower bound
    
    For any dice expression "XdYminK", every die result should be at least K
    (values below K should be raised to K).
    """
    assume(min_value < die_size)
    
    expression = f"{dice_count}d{die_size}min{min_value}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    
    # All final values should be >= min_value
    for roll in dice_result.rolls:
        assert roll.final_value >= min_value


# Property 22: Max clamping enforces upper bound
# Validates: Requirements 6.2

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=10),
    die_size=st.integers(min_value=4, max_value=20),
    max_value=st.integers(min_value=2, max_value=10)
)
def test_property_22_max_clamping(dice_count, die_size, max_value):
    """
    Feature: advanced-dice-roller, Property 22: Max clamping enforces upper bound
    
    For any dice expression "XdYmaxK", every die result should be at most K
    (values above K should be lowered to K).
    """
    assume(max_value < die_size)
    
    expression = f"{dice_count}d{die_size}max{max_value}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    
    # All final values should be <= max_value
    for roll in dice_result.rolls:
        assert roll.final_value <= max_value


# Property 14-18: Success counting
# Validates: Requirements 5.1-5.5

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    threshold=st.integers(min_value=1, max_value=10)
)
def test_property_14_success_counting_ge(dice_count, die_size, threshold):
    """
    Feature: advanced-dice-roller, Property 14: Success counting with >= counts correctly
    
    For any dice pool "XdY>=T", the success count should equal the number of
    dice showing values greater than or equal to T.
    """
    assume(threshold <= die_size)
    
    expression = f"{dice_count}d{die_size}>={threshold}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    # Count successes manually
    dice_result = result.dice_results[0]
    expected_successes = sum(1 for r in dice_result.rolls if r.kept and r.final_value >= threshold)
    
    assert result.final_value == expected_successes
    assert result.is_success_count == True
    assert result.success_count == expected_successes


@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    threshold=st.integers(min_value=1, max_value=10)
)
def test_property_15_success_counting_le(dice_count, die_size, threshold):
    """
    Feature: advanced-dice-roller, Property 15: Success counting with <= counts correctly
    """
    assume(threshold <= die_size)
    
    expression = f"{dice_count}d{die_size}<={threshold}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    expected_successes = sum(1 for r in dice_result.rolls if r.kept and r.final_value <= threshold)
    
    assert result.final_value == expected_successes


@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    threshold=st.integers(min_value=1, max_value=10)
)
def test_property_16_success_counting_gt(dice_count, die_size, threshold):
    """
    Feature: advanced-dice-roller, Property 16: Success counting with > counts correctly
    """
    assume(threshold < die_size)
    
    expression = f"{dice_count}d{die_size}>{threshold}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    expected_successes = sum(1 for r in dice_result.rolls if r.kept and r.final_value > threshold)
    
    assert result.final_value == expected_successes


@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    threshold=st.integers(min_value=1, max_value=10)
)
def test_property_17_success_counting_lt(dice_count, die_size, threshold):
    """
    Feature: advanced-dice-roller, Property 17: Success counting with < counts correctly
    """
    assume(threshold <= die_size)
    
    expression = f"{dice_count}d{die_size}<{threshold}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    expected_successes = sum(1 for r in dice_result.rolls if r.kept and r.final_value < threshold)
    
    assert result.final_value == expected_successes


@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=20),
    die_size=st.integers(min_value=2, max_value=20),
    threshold=st.integers(min_value=1, max_value=10)
)
def test_property_18_success_counting_eq(dice_count, die_size, threshold):
    """
    Feature: advanced-dice-roller, Property 18: Success counting with = counts correctly
    """
    assume(threshold <= die_size)
    
    expression = f"{dice_count}d{die_size}={threshold}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    dice_result = result.dice_results[0]
    expected_successes = sum(1 for r in dice_result.rolls if r.kept and r.final_value == threshold)
    
    assert result.final_value == expected_successes


# Property 20: Success counts are usable in arithmetic
# Validates: Requirements 5.7

@settings(max_examples=50)
@given(
    dice_count=st.integers(min_value=1, max_value=10),
    die_size=st.integers(min_value=2, max_value=10),
    threshold=st.integers(min_value=1, max_value=5),
    constant=st.integers(min_value=1, max_value=10)
)
def test_property_20_success_count_arithmetic(dice_count, die_size, threshold, constant):
    """
    Feature: advanced-dice-roller, Property 20: Success counts are usable in arithmetic
    
    For any expression containing success counting in arithmetic operations,
    the success count should be treated as a numeric value in the calculation.
    """
    assume(threshold <= die_size)
    
    expression = f"({dice_count}d{die_size}>={threshold}) + {constant}"
    ast = parse(expression)
    
    evaluator = DiceEvaluator()
    result = evaluator.evaluate(ast, expression)
    
    # Result should be success_count + constant
    # We can't predict the exact success count, but we can verify the range
    min_possible = 0 + constant  # No successes
    max_possible = dice_count + constant  # All successes
    
    assert min_possible <= result.final_value <= max_possible
