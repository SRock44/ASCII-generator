#!/usr/bin/env python3
"""Main CLI entry point for ASCII Generator."""
import click
import sys
from pathlib import Path

from ai.factory import create_ai_client
from generators.ascii_art import ASCIIArtGenerator
from generators.charts import ChartGenerator
from generators.diagrams import DiagramGenerator
from parsers.codebase import CodebaseParser
from parsers.github import GitHubParser
from renderer import Renderer
from cache import Cache
from rate_limiter import RateLimiter


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """ASCII Generator - Generate ASCII art, charts, and diagrams using AI."""
    pass


@cli.command()
@click.argument('prompt', required=True)
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--no-colors', is_flag=True, help='Disable color output')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider to use: gemini, groq, or auto (default)')
def art(prompt, no_cache, no_colors, provider):
    """Generate ASCII art from a text prompt.
    
    Example: ascii-gen art "a cat wearing sunglasses"
    Example: ascii-gen art "a cat" --provider groq
    """
    try:
        renderer = Renderer()
        renderer.render_loading("Generating ASCII art...")
        
        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name)
        cache = Cache() if not no_cache else None
        rate_limiter = RateLimiter()
        
        generator = ASCIIArtGenerator(ai_client, cache, rate_limiter)
        result = generator.generate(prompt, use_cache=not no_cache)
        
        renderer.clear_line()
        # Check if result is an error
        if result.startswith("ERROR_CODE:"):
            renderer.render_error(result)
            sys.exit(1)
        else:
            renderer.render_ascii(result, title="ASCII Art", use_colors=not no_colors)
        
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('prompt', required=True)
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider to use: gemini, groq, or auto (default)')
def chart(prompt, no_cache, provider):
    """Generate a chart from a text prompt.
    
    Example: ascii-gen chart "bar chart: Q1=100, Q2=150, Q3=120, Q4=200"
    """
    try:
        renderer = Renderer()
        renderer.render_loading("Generating chart...")
        
        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name)
        cache = Cache() if not no_cache else None
        rate_limiter = RateLimiter()
        
        generator = ChartGenerator(ai_client, cache, rate_limiter)
        result = generator.generate(prompt, use_cache=not no_cache)
        
        renderer.clear_line()
        # Check if result is an error
        if result.startswith("ERROR_CODE:"):
            renderer.render_error(result)
            sys.exit(1)
        else:
            renderer.render_ascii(result, title="Chart")
        
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('prompt', required=True)
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False), 
              default='top-to-bottom', help='Diagram orientation: top-to-bottom (default) or left-to-right')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider to use: gemini, groq, or auto (default)')
def diagram(prompt, no_cache, orientation, provider):
    """Generate a diagram from a text prompt.
    
    Example: ascii-gen diagram "flowchart: user login -> authenticate -> dashboard"
    Example: ascii-gen diagram "workflow" --orientation left-to-right
    """
    try:
        renderer = Renderer()
        renderer.render_loading("Generating diagram...")
        
        # Normalize orientation values
        if orientation.lower() in ['t2b', 'top-to-bottom', 'vertical', 'tb']:
            orientation = 'top-to-bottom'
        elif orientation.lower() in ['l2r', 'left-to-right', 'horizontal', 'lr']:
            orientation = 'left-to-right'
        
        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name)
        cache = Cache() if not no_cache else None
        rate_limiter = RateLimiter()
        
        generator = DiagramGenerator(ai_client, cache, rate_limiter)
        result = generator.generate(prompt, use_cache=not no_cache, orientation=orientation)
        
        renderer.clear_line()
        # Check if result is an error
        if result.startswith("ERROR_CODE:"):
            renderer.render_error(result)
            sys.exit(1)
        else:
            renderer.render_ascii(result, title="Diagram")
        
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--max-files', default=50, help='Maximum files to analyze')
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False), 
              default='top-to-bottom', help='Diagram orientation: top-to-bottom (default) or left-to-right')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider to use: gemini, groq, or auto (default)')
def codebase(path, no_cache, max_files, orientation, provider):
    """Generate an architecture diagram from a local codebase.
    
    Example: ascii-gen codebase /path/to/project
    """
    try:
        renderer = Renderer()
        renderer.render_info(f"Analyzing codebase at: {path}")
        renderer.render_loading("Parsing codebase structure...")
        
        # Parse codebase
        parser = CodebaseParser(path)
        summary = parser.analyze(max_files=max_files)
        
        renderer.clear_line()
        renderer.render_loading("Generating architecture diagram...")
        
        # Generate diagram
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name)
        cache = Cache() if not no_cache else None
        rate_limiter = RateLimiter()
        
        generator = DiagramGenerator(ai_client, cache, rate_limiter)
        
        # Normalize orientation values
        if orientation.lower() in ['t2b', 'top-to-bottom', 'vertical', 'tb']:
            orientation = 'top-to-bottom'
        elif orientation.lower() in ['l2r', 'left-to-right', 'horizontal', 'lr']:
            orientation = 'left-to-right'
        
        # Create prompt with codebase summary
        prompt = f"Create an architecture diagram for this codebase:\n\n{summary}"
        result = generator.generate(prompt, use_cache=not no_cache, is_codebase=True, orientation=orientation)
        
        renderer.clear_line()
        # Check if result is an error
        if result.startswith("ERROR_CODE:"):
            renderer.render_error(result)
            sys.exit(1)
        else:
            renderer.render_ascii(result, title="Architecture Diagram")
        
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('repo_url', required=True)
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--max-files', default=50, help='Maximum files to analyze')
@click.option('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False), 
              default='top-to-bottom', help='Diagram orientation: top-to-bottom (default) or left-to-right')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider to use: gemini, groq, or auto (default)')
def github(repo_url, no_cache, max_files, token, orientation, provider):
    """Generate an architecture diagram from a GitHub repository.
    
    Example: ascii-gen github owner/repo-name
    """
    try:
        renderer = Renderer()
        renderer.render_info(f"Fetching repository: {repo_url}")
        renderer.render_loading("Cloning and analyzing repository...")
        
        # Parse GitHub repo
        parser = GitHubParser(github_token=token)
        summary = parser.parse_repo(repo_url, max_files=max_files)
        
        if summary.startswith("Error:"):
            renderer.clear_line()
            renderer.render_error(summary)
            sys.exit(1)
        
        renderer.clear_line()
        renderer.render_loading("Generating architecture diagram...")
        
        # Generate diagram
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name)
        cache = Cache() if not no_cache else None
        rate_limiter = RateLimiter()
        
        generator = DiagramGenerator(ai_client, cache, rate_limiter)
        
        # Normalize orientation values
        if orientation.lower() in ['t2b', 'top-to-bottom', 'vertical', 'tb']:
            orientation = 'top-to-bottom'
        elif orientation.lower() in ['l2r', 'left-to-right', 'horizontal', 'lr']:
            orientation = 'left-to-right'
        
        # Create prompt with codebase summary
        prompt = f"Create an architecture diagram for this codebase:\n\n{summary}"
        result = generator.generate(prompt, use_cache=not no_cache, is_codebase=True, orientation=orientation)
        
        renderer.clear_line()
        # Check if result is an error
        if result.startswith("ERROR_CODE:"):
            renderer.render_error(result)
            sys.exit(1)
        else:
            renderer.render_ascii(result, title="Architecture Diagram")
        
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
def clear_cache():
    """Clear the cache of generated content."""
    try:
        cache = Cache()
        cache.clear()
        renderer = Renderer()
        renderer.render_success("Cache cleared successfully")
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider to check: gemini, groq, or auto (default)')
def check(provider):
    """Check if the AI client is configured and available."""
    try:
        renderer = Renderer()
        renderer.render_info("Checking AI client configuration...")
        
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name)
        if ai_client.is_available():
            provider_used = provider_name or "auto-selected"
            renderer.render_success(f"AI client is configured and available (provider: {provider_used})")
        else:
            renderer.render_error("AI client is not available")
            sys.exit(1)
    except ValueError as e:
        renderer = Renderer()
        renderer.render_error(f"Configuration error: {str(e)}")
        renderer.render_info("Make sure GEMINI_API_KEY or GROQ_API_KEY is set in your .env file")
        sys.exit(1)
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(f"Configuration error: {str(e)}")
        renderer.render_info("Make sure GEMINI_API_KEY or GROQ_API_KEY is set in your .env file")
        sys.exit(1)


if __name__ == '__main__':
    cli()

