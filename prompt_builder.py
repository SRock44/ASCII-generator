"""Smart prompt builder that injects relevant examples."""
from typing import List, Dict, Any, Optional
from examples_loader import ExampleLoader
from ai.prompts import ASCII_ART_PROMPT, LOGO_PROMPT


class PromptBuilder:
    """Builds prompts with relevant examples."""

    def __init__(self, example_loader: Optional[ExampleLoader] = None):
        """
        Initialize PromptBuilder.

        Args:
            example_loader: ExampleLoader instance. Creates one if not provided.
        """
        self.example_loader = example_loader or ExampleLoader()

    def _format_examples_section(self, examples: List[Dict[str, Any]], subject: str) -> str:
        """
        Format examples into a prompt section.

        Args:
            examples: List of example dicts
            subject: Subject name for context

        Returns:
            Formatted examples section string
        """
        if not examples:
            return ""

        lines = [
            f"\n{'='*60}",
            f"REQUIRED QUALITY EXAMPLES FOR '{subject.upper()}' (from ascii-art.de):",
            f"{'='*60}",
            "Study these examples CAREFULLY - your output MUST match this quality level.",
            "Notice the key techniques:",
            "- Character variety: Uses (), {}, [], /, \\, |, -, _, etc. for different textures",
            "- Recognizable features: Each example is INSTANTLY identifiable",
            "- Artistic detail: Curves, shading, depth using character combinations",
            "- Proper structure: Complete, balanced, well-proportioned",
            ""
        ]

        for i, example in enumerate(examples, 1):
            art = example.get("art", "")
            if art:
                lines.append(f"Example {i}:")
                lines.append(art)
                lines.append("")  # Blank line between examples

        lines.append("YOUR TASK:")
        lines.append(f"Create an ORIGINAL ASCII art of '{subject}' using the SAME TECHNIQUES as above.")
        lines.append("")
        lines.append("MANDATORY REQUIREMENTS:")
        lines.append("1. QUALITY MATCH: Your art MUST be as detailed and recognizable as the examples")
        lines.append("2. CHARACTER VARIETY: Use diverse characters like the examples - (), {}, [], /, \\, |, -, _, `, ', etc.")
        lines.append("3. RECOGNIZABLE: Must be INSTANTLY identifiable as a " + subject)
        lines.append("4. COMPLETE: Finish the ENTIRE drawing - no cut-off lines or incomplete patterns")
        lines.append("5. ORIGINAL: Do NOT copy examples verbatim - create something NEW in the same style")
        lines.append("6. ARTISTIC: Add curves, shading, depth - make it beautiful like the examples")
        lines.append("")
        lines.append("STUDY THE EXAMPLES ABOVE - Match their quality, technique, and artistic style!")
        lines.append("")

        return "\n".join(lines)

    def build(self, subject: str, is_logo: bool = False, max_examples: int = 2) -> str:
        """
        Build enhanced prompt with relevant examples.

        Args:
            subject: User query (e.g., "an elephant", "cat")
            is_logo: Whether this is a logo generation (uses LOGO_PROMPT)
            max_examples: Maximum number of examples to include (default: 2)

        Returns:
            Enhanced system prompt with examples
        """
        # Get base prompt
        base_prompt = LOGO_PROMPT if is_logo else ASCII_ART_PROMPT

        # Get relevant examples
        examples = self.example_loader.get_examples(subject, count=max_examples)

        if not examples:
            # No examples found, return base prompt
            return base_prompt

        # Extract subject name for display (clean up query)
        subject_clean = subject.lower().strip()
        # Remove common prefixes
        for prefix in ['a ', 'an ', 'the ']:
            if subject_clean.startswith(prefix):
                subject_clean = subject_clean[len(prefix):].strip()

        # Format examples section
        examples_section = self._format_examples_section(examples, subject_clean)

        # Combine: base prompt + examples + instruction
        enhanced_prompt = base_prompt

        # Insert examples after the base rules but before final instructions
        # For ASCII_ART_PROMPT, insert before "CRITICAL REQUIREMENTS:"
        # For LOGO_PROMPT, insert before "OUTPUT FORMAT:"
        if is_logo:
            # Insert before "OUTPUT FORMAT:" section
            if "OUTPUT FORMAT:" in enhanced_prompt:
                parts = enhanced_prompt.split("OUTPUT FORMAT:", 1)
                enhanced_prompt = parts[0] + examples_section + "\nOUTPUT FORMAT:" + parts[1]
            else:
                enhanced_prompt += examples_section
        else:
            # Insert before "CRITICAL REQUIREMENTS:" section
            if "CRITICAL REQUIREMENTS:" in enhanced_prompt:
                parts = enhanced_prompt.split("CRITICAL REQUIREMENTS:", 1)
                enhanced_prompt = parts[0] + examples_section + "\nCRITICAL REQUIREMENTS:" + parts[1]
            else:
                enhanced_prompt += examples_section

        return enhanced_prompt

