"""
Prompt Manager for template and example management.

This module manages prompt templates, few-shot examples, and learned patterns
for all LLM-driven agents. It supports dynamic prompt construction, learning
from feedback, and prompt versioning.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pathlib import Path
import json
import logging
from datetime import datetime

if TYPE_CHECKING:
    pass


class PromptManager:
    """
    Manages prompt templates and few-shot examples.

    Features:
    1. Load templates from prompts/base/*.txt
    2. Load few-shot examples from prompts/examples/*.json
    3. Inject examples into prompts
    4. Learn from successful/failed results
    5. Version prompts for A/B testing

    Attributes:
        prompts_dir: Base directory for all prompts
        base_prompts: Loaded prompt templates
        examples: Loaded few-shot examples
        learned_patterns: Runtime-collected successful patterns
        logger: Logger instance
    """

    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the Prompt Manager.

        Args:
            prompts_dir: Base directory containing prompt files

        Raises:
            Warning: If directories don't exist (will be logged, not raised)
        """
        self.prompts_dir = Path(prompts_dir)
        self.logger = logging.getLogger("core.prompt_manager")

        # Ensure directories exist
        self._ensure_directories()

        # Load base prompts from prompts/base/*.txt
        self.base_prompts = self._load_base_prompts()

        # Load few-shot examples from prompts/examples/*.json
        self.examples = self._load_examples()

        # Learned patterns (runtime collection)
        self.learned_patterns: List[Dict[str, Any]] = []

        self.logger.info(
            f"PromptManager initialized: {len(self.base_prompts)} templates, "
            f"{len(self.examples)} example sets"
        )

    def _ensure_directories(self):
        """Ensure required directories exist."""
        dirs_to_create = [
            self.prompts_dir / "base",
            self.prompts_dir / "examples",
            self.prompts_dir / "learned"
        ]

        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {directory}")

    def _load_base_prompts(self) -> Dict[str, str]:
        """
        Load all prompt templates from prompts/base/*.txt

        Returns:
            Dictionary mapping template name to template content
        """
        prompts = {}
        base_dir = self.prompts_dir / "base"

        if not base_dir.exists():
            self.logger.warning(f"Base prompts directory not found: {base_dir}")
            return prompts

        for file_path in base_dir.glob("*.txt"):
            prompt_name = file_path.stem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    prompts[prompt_name] = f.read()
                self.logger.debug(f"Loaded prompt template: {prompt_name}")
            except Exception as e:
                self.logger.error(f"Failed to load prompt {prompt_name}: {e}")

        self.logger.info(f"Loaded {len(prompts)} base prompt templates")
        return prompts

    def _load_examples(self) -> Dict[str, List[Dict]]:
        """
        Load few-shot examples from prompts/examples/*.json

        Returns:
            Dictionary mapping example set name to list of examples
        """
        examples = {}
        examples_dir = self.prompts_dir / "examples"

        if not examples_dir.exists():
            self.logger.warning(f"Examples directory not found: {examples_dir}")
            return examples

        for file_path in examples_dir.glob("*.json"):
            example_name = file_path.stem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_examples = json.load(f)

                # Validate example structure
                if not isinstance(loaded_examples, list):
                    self.logger.error(f"Examples in {example_name} must be a list, got {type(loaded_examples)}")
                    continue

                # Validate each example
                valid_examples = []
                for idx, example in enumerate(loaded_examples):
                    if self._validate_example(example, example_name, idx):
                        valid_examples.append(example)

                if valid_examples:
                    examples[example_name] = valid_examples
                    self.logger.debug(
                        f"Loaded {len(valid_examples)} valid examples for {example_name}"
                    )
                else:
                    self.logger.warning(f"No valid examples found in {example_name}")

            except Exception as e:
                self.logger.error(f"Failed to load examples {example_name}: {e}")

        self.logger.info(
            f"Loaded {len(examples)} example sets "
            f"({sum(len(ex) for ex in examples.values())} total examples)"
        )
        return examples

    def _validate_example(
        self,
        example: Any,
        example_name: str,
        index: int
    ) -> bool:
        """
        Validate example structure.

        Args:
            example: Example dictionary to validate
            example_name: Name of example set (for logging)
            index: Index in example list (for logging)

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(example, dict):
            self.logger.warning(
                f"Example #{index} in {example_name} must be a dict, got {type(example)}"
            )
            return False

        # Required keys for examples
        required_keys = ["description", "input", "output"]

        for key in required_keys:
            if key not in example:
                self.logger.warning(
                    f"Example #{index} in {example_name} missing required key: {key}"
                )
                return False

        # Validate output is dict or appropriate type
        if not isinstance(example["output"], (dict, list, str)):
            self.logger.warning(
                f"Example #{index} in {example_name} has invalid output type: {type(example['output'])}"
            )
            return False

        return True

    def build_prompt(
        self,
        template_name: str,
        context: Dict[str, Any],
        include_examples: bool = True,
        max_examples: int = 3
    ) -> str:
        """
        Build complete prompt from template + context + examples.

        Args:
            template_name: Name of template (e.g., "controller_analysis")
            context: Variables to inject (e.g., {"file_path": "...", "code": "..."})
            include_examples: Whether to add few-shot examples
            max_examples: Maximum number of examples to include

        Returns:
            Complete prompt ready for LLM

        Raises:
            ValueError: If template not found or context variables missing
        """
        # Get base template
        if template_name not in self.base_prompts:
            available = list(self.base_prompts.keys())
            raise ValueError(
                f"Prompt template not found: '{template_name}'. "
                f"Available templates: {available}"
            )

        template = self.base_prompts[template_name]

        # Inject few-shot examples if requested
        if include_examples and template_name in self.examples:
            examples_text = self._format_examples(
                self.examples[template_name][:max_examples]
            )
            # Prepend examples before template
            template = f"{examples_text}\n\n---\n\n{template}"
            self.logger.debug(
                f"Added {min(max_examples, len(self.examples[template_name]))} "
                f"examples to prompt"
            )

        # Inject context variables
        try:
            prompt = template.format(**context)
        except KeyError as e:
            missing_key = str(e).strip("'")
            available_keys = list(context.keys())
            raise ValueError(
                f"Missing required context variable: {missing_key}. "
                f"Available: {available_keys}"
            )

        self.logger.debug(
            f"Built prompt: {len(prompt)} chars, template={template_name}"
        )

        return prompt

    def _format_examples(self, examples: List[Dict]) -> str:
        """
        Format few-shot examples as text.

        Args:
            examples: List of example dictionaries

        Returns:
            Formatted examples as string
        """
        if not examples:
            return ""

        formatted = ["# Few-Shot Examples\n"]

        for i, example in enumerate(examples, 1):
            formatted.append(f"## Example {i}")

            # Add description if available
            if "description" in example:
                formatted.append(f"**Description**: {example['description']}\n")

            # Add input
            if "input" in example:
                formatted.append(f"**Input**:")
                formatted.append(f"```\n{example['input']}\n```\n")

            # Add output
            if "output" in example:
                formatted.append(f"**Expected Output**:")
                formatted.append(f"```json\n{json.dumps(example['output'], indent=2)}\n```\n")

        return "\n".join(formatted)

    def learn_from_result(
        self,
        template_name: str,
        input_data: Dict[str, Any],
        output: Dict[str, Any],
        feedback: Dict[str, Any]
    ):
        """
        Learn from analysis result.

        If correct: Save as positive example
        If incorrect: Log for later analysis (could improve prompt)

        Args:
            template_name: Which prompt was used
            input_data: Input context that was provided
            output: LLM's output
            feedback: Feedback dictionary with structure:
                {
                    "correct": bool,
                    "issues": List[str],  # If incorrect
                    "suggestions": List[str]  # Optional improvement suggestions
                }
        """
        if feedback.get("correct"):
            # Save as positive example
            pattern = {
                "template": template_name,
                "input": input_data,
                "output": output,
                "rating": 5,
                "timestamp": self._get_timestamp()
            }

            self.learned_patterns.append(pattern)

            # Persist to disk
            self._save_learned_pattern(template_name, pattern)

            self.logger.info(
                f"Learned positive pattern for {template_name} "
                f"(total learned: {len(self.learned_patterns)})"
            )

        else:
            # Log failure for analysis
            issues = feedback.get("issues", [])
            suggestions = feedback.get("suggestions", [])

            self.logger.warning(
                f"Prompt {template_name} produced incorrect result. "
                f"Issues: {issues}, Suggestions: {suggestions}"
            )

            # Could implement automatic prompt improvement here in future
            # For now, just log for manual review

    def _save_learned_pattern(self, template_name: str, pattern: Dict):
        """
        Save learned pattern to prompts/learned/<template>_learned.jsonl

        Args:
            template_name: Name of the template
            pattern: Pattern dictionary to save
        """
        learned_dir = self.prompts_dir / "learned"
        learned_dir.mkdir(exist_ok=True)

        file_path = learned_dir / f"{template_name}_learned.jsonl"

        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(pattern) + "\n")

            self.logger.debug(f"Saved learned pattern to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save learned pattern: {e}")

    def get_template(self, template_name: str) -> str:
        """
        Get raw template content.

        Args:
            template_name: Name of the template

        Returns:
            Template content as string

        Raises:
            KeyError: If template not found
        """
        if template_name not in self.base_prompts:
            raise KeyError(
                f"Template '{template_name}' not found. "
                f"Available: {list(self.base_prompts.keys())}"
            )

        return self.base_prompts[template_name]

    def get_examples(self, example_set_name: str) -> List[Dict]:
        """
        Get examples for a specific set.

        Args:
            example_set_name: Name of the example set

        Returns:
            List of example dictionaries

        Raises:
            KeyError: If example set not found
        """
        if example_set_name not in self.examples:
            raise KeyError(
                f"Example set '{example_set_name}' not found. "
                f"Available: {list(self.examples.keys())}"
            )

        return self.examples[example_set_name].copy()

    def list_templates(self) -> List[str]:
        """
        Get list of available template names.

        Returns:
            List of template names
        """
        return list(self.base_prompts.keys())

    def list_example_sets(self) -> List[str]:
        """
        Get list of available example set names.

        Returns:
            List of example set names
        """
        return list(self.examples.keys())

    def reload(self):
        """
        Reload all templates and examples from disk.

        Useful for development when templates are being edited.
        """
        self.logger.info("Reloading prompt templates and examples...")

        self.base_prompts = self._load_base_prompts()
        self.examples = self._load_examples()

        self.logger.info(
            f"Reload complete: {len(self.base_prompts)} templates, "
            f"{len(self.examples)} example sets"
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format."""
        return datetime.now().isoformat()

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"<PromptManager(templates={len(self.base_prompts)}, "
            f"example_sets={len(self.examples)}, "
            f"learned_patterns={len(self.learned_patterns)})>"
        )
