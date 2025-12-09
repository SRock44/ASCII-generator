"""Terminal rendering with Rich library."""
from typing import Optional
from rich.console import Console
import config


class Renderer:
    """Terminal renderer using Rich library."""
    
    def __init__(self):
        """Initialize renderer."""
        self.console = Console()
    
    def render_ascii(self, content: str, title: Optional[str] = None):
        """
        Render ASCII art/content.
        
        Args:
            content: ASCII content to render
            title: Optional title for the content
        """
        # Clean up content
        content = content.strip()
        
        # Remove any markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        if title:
            self.console.print(f"\n[bold cyan]{title}[/bold cyan]\n")
        
        # Use monospace font for ASCII art
        self.console.print(content, style="white")
        self.console.print()  # Extra newline
    
    def render_error(self, message: str):
        """
        Render error message.
        
        Args:
            message: Error message
        """
        self.console.print(f"[bold red]Error:[/bold red] {message}")
    
    def render_info(self, message: str):
        """
        Render info message.
        
        Args:
            message: Info message
        """
        self.console.print(f"[bold blue]Info:[/bold blue] {message}")
    
    def render_success(self, message: str):
        """
        Render success message.
        
        Args:
            message: Success message
        """
        self.console.print(f"[bold green]Success:[/bold green] {message}")
    
    def render_loading(self, message: str = "Generating..."):
        """
        Render loading message.
        
        Args:
            message: Loading message
        """
        self.console.print(f"[yellow]{message}[/yellow]", end="\r")
    
    def clear_line(self):
        """Clear the current line."""
        self.console.print(" " * 80, end="\r")

