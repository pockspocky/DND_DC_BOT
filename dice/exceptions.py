"""
Custom Exception Classes for Dice System
Provides clear error types for different failure modes
"""


class DiceError(Exception):
    """Base exception for dice system errors"""
    pass


class ParseError(DiceError):
    """Raised when expression cannot be parsed"""
    pass


class UnsupportedFeatureError(DiceError):
    """Raised when expression uses unsupported features"""
    pass


class ValidationError(DiceError):
    """Raised when expression exceeds validation limits"""
    pass


class EvaluationError(DiceError):
    """Raised when evaluation fails"""
    pass
