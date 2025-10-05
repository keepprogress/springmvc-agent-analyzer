"""
Lightweight validators for LLM-generated analysis results.

These validators ensure syntax correctness and basic structural validity
without re-implementing full parsing logic.
"""

from validators.java_validator import JavaValidator

__all__ = [
    "JavaValidator",
]
