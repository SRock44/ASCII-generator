#!/usr/bin/env python3
"""Main CLI entry point for ASCII Generator."""
import click
import sys
from pathlib import Path

from ai.factory import create_ai_client
from ai.groq_client import GroqClient
from generators.ascii_art import ASCIIArtGenerator
from generators.charts import ChartGenerator
from generators.diagrams import DiagramGenerator
from parsers.codebase import CodebaseParser
from parsers.github import GitHubParser
from renderer import Renderer
from cache import Cache
from rate_limiter import RateLimiter
import config


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """ASCII Generator - Generate ASCII art, charts, and diagrams using AI."""
    pass


def generate_explanation(content: str, content_type: str, original_prompt: str) -> str:
    """
    Generate an explanation of the generated ASCII art or chart using Groq.
    
    Args:
        content: The generated ASCII art or chart content
        content_type: Type of content ('art' or 'chart')
        original_prompt: The original user prompt
        
    Returns:
        Explanation text from Groq
    """
    try:
        # Always use Groq for explanations
        groq_client = GroqClient()
        rate_limiter = RateLimiter()
        
        # Wait for rate limit
        rate_limiter.wait_if_needed()
        
        # Create explanation prompt
        if content_type == 'art':
            explanation_prompt = f"""Please provide a brief, clear explanation of this ASCII art. 

Original prompt: {original_prompt}

ASCII Art:
{content}

Explain what the ASCII art depicts, its key features, and any notable artistic elements. Keep it concise (2-3 sentences)."""
        else:  # chart
            explanation_prompt = f"""Please provide a brief, clear explanation of this ASCII chart/diagram.

Original prompt: {original_prompt}

Chart/Diagram:
{content}

Explain what the chart/diagram shows, the data relationships, and key insights. Keep it concise (2-3 sentences) If the diagram is a codebase diagram, explain the codebase structure and the relationships between the codebase."""
        
        # Generate explanation
        explanation = groq_client.generate(explanation_prompt)
        
        # Check for errors
        if explanation.startswith("ERROR_CODE:"):
            return "Unable to generate explanation. Please try again."
        
        return explanation.strip()
    except Exception as e:
        return f"Unable to generate explanation: {str(e)}"


@cli.command()
@click.argument('prompts', nargs=-1, required=True)
@click.option('--no-cache', is_flag=True, help='Disable caching for this request')
@click.option('--no-colors', is_flag=True, help='Disable color output (monochrome)')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False),
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
@click.option('--explain', is_flag=True, help='Get an explanation of the generated art from Groq')
@click.option('--live', is_flag=True, help='Show live progressive drawing animation as art is generated')
def art(prompts, no_cache, no_colors, provider, explain, live):
    """Generate ASCII art from one or more text prompts.
    
    Examples:
      ascii-gen art "a cat wearing sunglasses"
      ascii-gen art "a cat" "a dog" "a bird" --provider groq
      ascii-gen art "a cat" --provider groq --no-cache --no-colors
      ascii-gen art "a cat" --explain
    """
    try:
        renderer = Renderer()
        
        # Check if Groq is available for explanations
        if explain and not config.GROQ_API_KEY:
            renderer.render_error("--explain requires GROQ_API_KEY to be set in .env")
            sys.exit(1)
        
        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name, mode="art")
        cache = Cache() if not no_cache else None
        rate_limiter = RateLimiter()
        generator = ASCIIArtGenerator(ai_client, cache, rate_limiter)
        
        # Process each prompt
        for i, prompt in enumerate(prompts, 1):
            if len(prompts) > 1:
                renderer.render_info(f"Generating ASCII art {i}/{len(prompts)}: {prompt[:50]}...")
            else:
                if not live:
                    renderer.render_loading("Generating ASCII art...")

            if live:
                # Use live progressive rendering
                title = f"ASCII Art {i}" if len(prompts) > 1 else "ASCII Art"
                stream_generator = generator.generate_stream(prompt, use_cache=not no_cache)
                renderer.render_ascii_progressive(stream_generator, title=title, use_colors=not no_colors)

                # For explanation, we need the full result
                if explain:
                    # Re-generate or get from cache (will be cached from streaming)
                    result = generator.generate(prompt, use_cache=True)
                    if not result.startswith("ERROR_CODE:"):
                        renderer.render_loading("Generating explanation...")
                        explanation = generate_explanation(result, 'art', prompt)
                        renderer.clear_line()
                        renderer.render_explanation(explanation, title="Explanation")
            else:
                # Traditional non-streaming rendering
                result = generator.generate(prompt, use_cache=not no_cache)

                renderer.clear_line()
                # Check if result is an error
                if result.startswith("ERROR_CODE:"):
                    renderer.render_error(result)
                    if len(prompts) > 1:
                        continue  # Continue with next prompt
                    else:
                        sys.exit(1)
                else:
                    title = f"ASCII Art {i}" if len(prompts) > 1 else "ASCII Art"
                    renderer.render_ascii(result, title=title, use_colors=not no_colors)

                    # Generate explanation if requested
                    if explain:
                        renderer.render_loading("Generating explanation...")
                        explanation = generate_explanation(result, 'art', prompt)
                        renderer.clear_line()
                        renderer.render_explanation(explanation, title="Explanation")
        
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('prompts', nargs=-1, required=True)
@click.option('--no-cache', is_flag=True, help='Disable caching for this request')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False),
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
@click.option('--explain', is_flag=True, help='Get an explanation of the generated chart from Groq')
@click.option('--live', is_flag=True, help='Show live progressive drawing animation as chart is generated')
def chart(prompts, no_cache, provider, explain, live):
    """Generate a chart from one or more text prompts.
    
    Examples:
      ascii-gen chart "bar chart: Q1=100, Q2=150, Q3=120, Q4=200"
      ascii-gen chart "sales data" "revenue growth" --provider groq --no-cache
      ascii-gen chart "bar chart: Q1=100, Q2=150" --explain
    """
    try:
        renderer = Renderer()
        
        # Check if Groq is available for explanations
        if explain and not config.GROQ_API_KEY:
            renderer.render_error("--explain requires GROQ_API_KEY to be set in .env")
            sys.exit(1)
        
        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name, mode="chart")
        cache = Cache() if not no_cache else None
        rate_limiter = RateLimiter()
        generator = ChartGenerator(ai_client, cache, rate_limiter)
        
        # Process each prompt
        for i, prompt in enumerate(prompts, 1):
            if len(prompts) > 1:
                renderer.render_info(f"Generating chart {i}/{len(prompts)}: {prompt[:50]}...")
            else:
                if not live:
                    renderer.render_loading("Generating chart...")

            if live:
                # Use live progressive rendering
                title = f"Chart {i}" if len(prompts) > 1 else "Chart"
                stream_generator = generator.generate_stream(prompt, use_cache=not no_cache)
                renderer.render_ascii_progressive(stream_generator, title=title, use_colors=True)

                # For explanation, we need the full result
                if explain:
                    # Re-generate or get from cache (will be cached from streaming)
                    result = generator.generate(prompt, use_cache=True)
                    if not result.startswith("ERROR_CODE:"):
                        renderer.render_loading("Generating explanation...")
                        explanation = generate_explanation(result, 'chart', prompt)
                        renderer.clear_line()
                        renderer.render_explanation(explanation, title="Explanation")
            else:
                # Traditional non-streaming rendering
                result = generator.generate(prompt, use_cache=not no_cache)

                renderer.clear_line()
                # Check if result is an error
                if result.startswith("ERROR_CODE:"):
                    renderer.render_error(result)
                    if len(prompts) > 1:
                        continue  # Continue with next prompt
                    else:
                        sys.exit(1)
                else:
                    title = f"Chart {i}" if len(prompts) > 1 else "Chart"
                    renderer.render_ascii(result, title=title)

                    # Generate explanation if requested
                    if explain:
                        renderer.render_loading("Generating explanation...")
                        explanation = generate_explanation(result, 'chart', prompt)
                        renderer.clear_line()
                        renderer.render_explanation(explanation, title="Explanation")
        
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('prompts', nargs=-1, required=True)
@click.option('--no-cache', is_flag=True, help='Disable caching for this request')
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False),
              default='top-to-bottom', help='Diagram orientation: top-to-bottom or left-to-right (default: top-to-bottom)')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False),
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
@click.option('--live', is_flag=True, help='Show live progressive drawing animation as diagram is generated')
def diagram(prompts, no_cache, orientation, provider, live):
    """Generate a diagram from one or more text prompts.
    
    Examples:
      ascii-gen diagram "flowchart: user login -> authenticate -> dashboard"
      ascii-gen diagram "workflow" "auth flow" --orientation left-to-right --provider groq --no-cache
    """
    try:
        renderer = Renderer()
        
        # Normalize orientation values
        if orientation.lower() in ['t2b', 'top-to-bottom', 'vertical', 'tb']:
            orientation = 'top-to-bottom'
        elif orientation.lower() in ['l2r', 'left-to-right', 'horizontal', 'lr']:
            orientation = 'left-to-right'
        
        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name, mode="diagram")
        cache = Cache() if not no_cache else None
        rate_limiter = RateLimiter()
        generator = DiagramGenerator(ai_client, cache, rate_limiter)
        
        # Process each prompt
        for i, prompt in enumerate(prompts, 1):
            if len(prompts) > 1:
                renderer.render_info(f"Generating diagram {i}/{len(prompts)}: {prompt[:50]}...")
            else:
                if not live:
                    renderer.render_loading("Generating diagram...")

            if live:
                # Use live progressive rendering
                title = f"Diagram {i}" if len(prompts) > 1 else "Diagram"
                stream_generator = generator.generate_stream(prompt, use_cache=not no_cache, orientation=orientation)
                renderer.render_ascii_progressive(stream_generator, title=title, use_colors=True)
            else:
                # Traditional non-streaming rendering
                result = generator.generate(prompt, use_cache=not no_cache, orientation=orientation)

                renderer.clear_line()
                # Check if result is an error
                if result.startswith("ERROR_CODE:"):
                    renderer.render_error(result)
                    if len(prompts) > 1:
                        continue  # Continue with next prompt
                    else:
                        sys.exit(1)
                else:
                    title = f"Diagram {i}" if len(prompts) > 1 else "Diagram"
                    renderer.render_ascii(result, title=title)
        
    except Exception as e:
        renderer = Renderer()
        renderer.render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--no-cache', is_flag=True, help='Disable caching for this request')
@click.option('--max-files', default=50, help='Maximum number of files to analyze (default: 50)')
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False), 
              default='top-to-bottom', help='Diagram orientation: top-to-bottom or left-to-right (default: top-to-bottom)')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
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
        ai_client = create_ai_client(provider_name, mode="diagram")
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
@click.option('--no-cache', is_flag=True, help='Disable caching for this request')
@click.option('--max-files', default=50, help='Maximum number of files to analyze (default: 50)')
@click.option('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False), 
              default='top-to-bottom', help='Diagram orientation: top-to-bottom or left-to-right (default: top-to-bottom)')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
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
        ai_client = create_ai_client(provider_name, mode="diagram")
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

