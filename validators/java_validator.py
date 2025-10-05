"""
Java Validator for lightweight syntax checking.

This module provides minimal syntax validation for Java code.
It does NOT perform semantic analysis - just checks if code is parseable.
"""

from typing import Dict, Any, Optional
import logging


class JavaValidator:
    """
    Lightweight Java syntax validator.

    Uses javalang library for basic syntax checking only.
    Does NOT analyze semantics, dependencies, or business logic.

    This is a defensive layer to catch obviously malformed input,
    not a replacement for LLM analysis.
    """

    def __init__(self):
        """Initialize the Java validator."""
        self.logger = logging.getLogger("validators.java_validator")

        # Import javalang with lazy loading
        try:
            import javalang
            self.javalang = javalang
            self.available = True
        except ImportError:
            self.logger.warning(
                "javalang not installed - Java validation disabled. "
                "Install with: pip install javalang"
            )
            self.available = False

    def validate_syntax(self, code: str) -> Dict[str, Any]:
        """
        Check if Java code is syntactically valid.

        Args:
            code: Java source code as string

        Returns:
            Dictionary with validation result:
            {
                "valid": bool,
                "error": str or None,
                "error_line": int or None,
                "validator_available": bool
            }
        """
        if not self.available:
            # Validator not available - pass through
            return {
                "valid": True,  # Assume valid if we can't check
                "error": None,
                "error_line": None,
                "validator_available": False
            }

        try:
            # Attempt to parse the Java code
            self.javalang.parse.parse(code)

            return {
                "valid": True,
                "error": None,
                "error_line": None,
                "validator_available": True
            }

        except self.javalang.parser.JavaSyntaxError as e:
            # Syntax error found
            error_line = getattr(e, 'lineno', None)
            error_msg = str(e)

            self.logger.debug(
                f"Java syntax error at line {error_line}: {error_msg}"
            )

            return {
                "valid": False,
                "error": error_msg,
                "error_line": error_line,
                "validator_available": True
            }

        except Exception as e:
            # Unexpected error during parsing
            self.logger.warning(f"Unexpected error during Java validation: {e}")

            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "error_line": None,
                "validator_available": True
            }

    def extract_class_name(self, code: str) -> Optional[str]:
        """
        Quick extraction of class name (validation helper).

        This is a convenience method, not used for core analysis.
        LLM should extract class names - this is just for sanity checks.

        Args:
            code: Java source code

        Returns:
            Class name if found, None otherwise
        """
        if not self.available:
            return None

        try:
            tree = self.javalang.parse.parse(code)

            # Find first class declaration
            for path, node in tree:
                if isinstance(node, self.javalang.tree.ClassDeclaration):
                    return node.name

            return None

        except Exception as e:
            self.logger.debug(f"Could not extract class name: {e}")
            return None

    def extract_package(self, code: str) -> Optional[str]:
        """
        Quick extraction of package name.

        Args:
            code: Java source code

        Returns:
            Package name if found, None otherwise
        """
        if not self.available:
            return None

        try:
            tree = self.javalang.parse.parse(code)

            if tree.package:
                return tree.package.name

            return None

        except Exception as e:
            self.logger.debug(f"Could not extract package: {e}")
            return None

    def is_controller(self, code: str) -> bool:
        """
        Quick check if code appears to be a Spring Controller.

        Looks for @Controller or @RestController annotations.
        This is a heuristic check, not exhaustive.

        Args:
            code: Java source code

        Returns:
            True if appears to be a controller, False otherwise
        """
        # Simple string check (fast)
        controller_indicators = [
            "@Controller",
            "@RestController"
        ]

        return any(indicator in code for indicator in controller_indicators)

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        status = "available" if self.available else "unavailable"
        return f"<JavaValidator(status={status})>"
