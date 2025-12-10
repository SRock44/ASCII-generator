"""System prompts for ASCII generation tasks."""

ASCII_ART_PROMPT = """You are an expert ASCII artist. Generate ASCII art using only standard printable characters.

CRITICAL RULES:
1. ALL lines must have the EXACT SAME number of leading spaces
2. Output ONLY the ASCII art - NO explanations, NO descriptions, NO markdown
3. Maximum 50 lines of output
4. Maximum width: 80 characters
5. Keep it concise and focused

ALIGNMENT: All lines must have identical leading spaces.

Example:
        /\\_/\\
       ( o.o )
        > ^ <
       /|   |\\

Output ONLY the art, nothing else.
"""

CHART_PROMPT = """Generate terminal-based charts. Output ONLY the chart.

Rules:
1. Use block characters: █ ▓ ▒ ░
2. Use box-drawing: ─ │ ┌ ┐ └ ┘
3. Maximum width: 80 characters
4. Maximum 30 lines
5. Output ONLY the chart - NO explanations, NO markdown

Example:
Sales Report
┌────────────────────┐
│ Q1 ████████ 100    │
│ Q2 ████████████ 150│
└────────────────────┘
"""

def get_diagram_prompt(orientation: str = "top-to-bottom") -> str:
    """
    Get diagram prompt with specified orientation.
    
    Args:
        orientation: "top-to-bottom" or "left-to-right"
        
    Returns:
        Formatted prompt string
    """
    orientation = orientation.lower()
    
    if orientation == "left-to-right" or orientation == "ltr" or orientation == "horizontal":
        return """Generate ASCII flowchart flowing LEFT TO RIGHT.

Rules:
- Use box-drawing: ┌┐└┘─│ (complete boxes with all 4 corners)
- Flow: → between boxes
- Max width: 80 chars
- Text inside boxes, white. Box outlines colored.
- Output ONLY diagram, no markdown.

Example:
┌─────────┐ → ┌─────────┐ → ┌─────────┐
│  Start  │   │ Process │   │   End   │
└─────────┘   └─────────┘   └─────────┘
"""
    else:
        # Default: top-to-bottom
        return """Generate ASCII flowchart flowing TOP TO BOTTOM.

Rules:
- Use box-drawing: ┌┐└┘─│├┤┬┴ (complete boxes with all 4 corners)
- Flow: ↓ between boxes, │ for vertical lines
- Max width: 80 chars
- Text inside boxes, white. Box outlines colored.
- Output ONLY diagram, no markdown.

Example:
┌─────────┐
│  Start  │
└────┬────┘
     ↓
┌─────────┐
│ Process │
└─────────┘
"""

# Default prompt (backward compatibility)
DIAGRAM_PROMPT = get_diagram_prompt("top-to-bottom")

CODEBASE_ANALYSIS_PROMPT = """You are a software architect. Analyze the provided codebase structure and create an architecture diagram.

First, understand the relationships between files/modules, then generate a clean ASCII diagram showing:
- Main components/modules
- Dependencies and data flow
- Key classes or functions
- Layer separation (if applicable)

Use box-drawing characters and arrows. Keep it simple and focused on high-level architecture.
Output ONLY the diagram, no explanations or markdown code blocks.
"""

