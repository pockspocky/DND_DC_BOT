"""
Property-Based Tests for Tokenizer
Tests correctness properties related to tokenization
"""
import pytest
from hypothesis import given, settings, strategies as st
from dice.tokenizer import tokenize, UnsupportedFeatureError


# Property 32: Exploding dice syntax is rejected
# Validates: Requirements 9.2

@settings(max_examples=100)
@given(
    base_expr=st.sampled_from(['d20', '2d6', '1d8+3', '4d6kh3']),
    exploding_syntax=st.sampled_from(['!', '!!', '!p'])
)
def test_property_32_exploding_dice_rejected(base_expr, exploding_syntax):
    """
    Feature: advanced-dice-roller, Property 32: Exploding dice syntax is rejected
    
    For any expression containing exploding dice characters (!, !!, !p),
    the tokenizer should raise UnsupportedFeatureError with appropriate message.
    """
    # Insert exploding syntax into expression
    expression = f"{base_expr}{exploding_syntax}"
    
    # Should raise UnsupportedFeatureError
    with pytest.raises(UnsupportedFeatureError) as exc_info:
        tokenize(expression)
    
    # Error message should mention exploding dice
    error_message = str(exc_info.value).lower()
    assert 'exploding' in error_message or '!' in error_message
    assert 'not supported' in error_message


@settings(max_examples=100)
@given(
    exploding_position=st.sampled_from(['start', 'middle', 'end'])
)
def test_property_32_exploding_dice_rejected_various_positions(exploding_position):
    """
    Test that exploding syntax is rejected regardless of position in expression
    """
    if exploding_position == 'start':
        expression = '!d20+5'
    elif exploding_position == 'middle':
        expression = '2d6!+3'
    else:  # end
        expression = '1d8+3!'
    
    with pytest.raises(UnsupportedFeatureError) as exc_info:
        tokenize(expression)
    
    error_message = str(exc_info.value).lower()
    assert 'not supported' in error_message


# Property 33: Table syntax is rejected
# Validates: Requirements 9.3

@settings(max_examples=100)
@given(
    table_keyword=st.sampled_from(['table', 'rolltable', 'TABLE', 'RollTable', 'ROLLTABLE']),
    base_expr=st.sampled_from(['', 'd20', '2d6+3'])
)
def test_property_33_table_syntax_rejected(table_keyword, base_expr):
    """
    Feature: advanced-dice-roller, Property 33: Table syntax is rejected
    
    For any expression containing table keywords (table, rolltable),
    the tokenizer should raise UnsupportedFeatureError with appropriate message.
    """
    # Create expression with table keyword
    if base_expr:
        expression = f"{base_expr} {table_keyword}"
    else:
        expression = table_keyword
    
    # Should raise UnsupportedFeatureError
    with pytest.raises(UnsupportedFeatureError) as exc_info:
        tokenize(expression)
    
    # Error message should mention table rolls
    error_message = str(exc_info.value).lower()
    assert 'table' in error_message
    assert 'not supported' in error_message


@settings(max_examples=100)
@given(
    table_variant=st.sampled_from([
        'table', 'rolltable', 'TABLE', 'RollTable', 'ROLLTABLE', 'Table'
    ])
)
def test_property_33_table_syntax_rejected_variants(table_variant):
    """
    Test that various table keyword variants are rejected (case-insensitive)
    """
    expression = f"1d20 {table_variant}"
    
    with pytest.raises(UnsupportedFeatureError) as exc_info:
        tokenize(expression)
    
    error_message = str(exc_info.value).lower()
    assert 'table' in error_message
    assert 'not supported' in error_message


# Additional tests for tokenizer correctness

@settings(max_examples=100)
@given(
    dice_count=st.integers(min_value=1, max_value=100),
    die_size=st.integers(min_value=2, max_value=100)
)
def test_tokenizer_basic_dice_expression(dice_count, die_size):
    """Test that basic dice expressions tokenize correctly"""
    expression = f"{dice_count}d{die_size}"
    tokens = tokenize(expression)
    
    # Should have: NUMBER, DICE, NUMBER, EOF
    assert len(tokens) == 4
    assert tokens[0].type.value == "number"
    assert tokens[0].value == dice_count
    assert tokens[1].type.value == "dice"
    assert tokens[2].type.value == "number"
    assert tokens[2].value == die_size
    assert tokens[3].type.value == "eof"


@settings(max_examples=100)
@given(
    die_size=st.integers(min_value=2, max_value=100)
)
def test_tokenizer_omitted_dice_count(die_size):
    """Test that omitted dice count (d20) tokenizes correctly"""
    expression = f"d{die_size}"
    tokens = tokenize(expression)
    
    # Should have: DICE, NUMBER, EOF
    assert len(tokens) == 3
    assert tokens[0].type.value == "dice"
    assert tokens[1].type.value == "number"
    assert tokens[1].value == die_size
    assert tokens[2].type.value == "eof"


@settings(max_examples=100)
@given(
    operator=st.sampled_from(['kh', 'kl', 'dh', 'dl', 'r', 'ro', 'min', 'max', 's', 'sd'])
)
def test_tokenizer_dice_operators(operator):
    """Test that dice operators tokenize correctly"""
    expression = f"2d6{operator}1"
    tokens = tokenize(expression)
    
    # Should contain the operator token
    operator_tokens = [t for t in tokens if t.value == operator]
    assert len(operator_tokens) == 1


@settings(max_examples=100)
@given(
    comparison=st.sampled_from(['>=', '<=', '>', '<', '='])
)
def test_tokenizer_comparison_operators(comparison):
    """Test that comparison operators tokenize correctly"""
    expression = f"10d6{comparison}5"
    tokens = tokenize(expression)
    
    # Should contain the comparison token
    comparison_tokens = [t for t in tokens if t.value == comparison]
    assert len(comparison_tokens) == 1


@settings(max_examples=100)
@given(
    arithmetic_op=st.sampled_from(['+', '-', '*', '/'])
)
def test_tokenizer_arithmetic_operators(arithmetic_op):
    """Test that arithmetic operators tokenize correctly"""
    expression = f"1d8{arithmetic_op}3"
    tokens = tokenize(expression)
    
    # Should contain the arithmetic operator token
    op_tokens = [t for t in tokens if t.value == arithmetic_op]
    assert len(op_tokens) == 1


def test_tokenizer_parentheses():
    """Test that parentheses tokenize correctly"""
    expression = "(1d8+2)*3"
    tokens = tokenize(expression)
    
    # Should contain LPAREN and RPAREN tokens
    lparen_tokens = [t for t in tokens if t.type.value == "lparen"]
    rparen_tokens = [t for t in tokens if t.type.value == "rparen"]
    assert len(lparen_tokens) == 1
    assert len(rparen_tokens) == 1


def test_tokenizer_whitespace_handling():
    """Test that whitespace is handled correctly"""
    expression1 = "1d8+3"
    expression2 = "1d8 + 3"
    expression3 = "  1d8  +  3  "
    
    tokens1 = tokenize(expression1)
    tokens2 = tokenize(expression2)
    tokens3 = tokenize(expression3)
    
    # All should produce the same token sequence (ignoring positions)
    assert len(tokens1) == len(tokens2) == len(tokens3)
    for t1, t2, t3 in zip(tokens1, tokens2, tokens3):
        assert t1.type == t2.type == t3.type
        assert t1.value == t2.value == t3.value
