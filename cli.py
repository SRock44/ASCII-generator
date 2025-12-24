#!/usr/bin/env python3
"""Main CLI entry point for ASCII Generator."""
import click
import sys
import os
from pathlib import Path

from ai.factory import create_ai_client
from ai.groq_client import GroqClient
from generators.ascii_art import ASCIIArtGenerator
from generators.charts import ChartGenerator
from generators.diagrams import DiagramGenerator
from parsers.codebase import CodebaseParser
from parsers.github import GitHubParser
from renderer import Renderer
from session_context import SessionContext
from rate_limiter import RateLimiter
import config


def check_first_time_setup():
    """Check if this is first time use and run setup wizard if needed."""
    project_dir = Path(__file__).parent.absolute()
    env_file = project_dir / ".env"

    # If .env doesn't exist, this is first time use
    if not env_file.exists():
        click.echo()
        click.echo("=" * 70)
        click.echo("  Welcome to ASCII-Generator! 🎨")
        click.echo("=" * 70)
        click.echo()
        click.echo("It looks like this is your first time running ASCII-Generator.")
        click.echo("Let's get you set up with API keys (takes 1 minute).")
        click.echo()

        # Ask if they want to run setup
        if click.confirm("Would you like to set up your API keys now?", default=True):
            # Import and run setup wizard
            setup_keys_path = project_dir / "setup_keys.py"
            if setup_keys_path.exists():
                import subprocess
                result = subprocess.run([sys.executable, str(setup_keys_path)])
                if result.returncode != 0:
                    click.echo()
                    click.echo("❌ Setup failed. You can run it manually later:")
                    click.echo(f"   python {setup_keys_path}")
                    sys.exit(1)
            else:
                click.echo()
                click.echo("⚠️  Setup wizard not found. Please create a .env file manually.")
                click.echo(f"   See: {project_dir}/INSTALL.md")
                sys.exit(1)
        else:
            click.echo()
            click.echo("No problem! You can set up API keys later by running:")
            click.echo(f"   python {project_dir}/setup_keys.py")
            click.echo()
            click.echo("Or create a .env file manually with your API keys.")
            sys.exit(0)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """ASCII Generator - Generate ASCII art, charts, and diagrams using AI."""
    # Check for first-time setup on every command
    check_first_time_setup()


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
@click.option('--no-colors', is_flag=True, help='Disable color output (monochrome)')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False),
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
@click.option('--explain', is_flag=True, help='Get an explanation of the generated art from Groq')
@click.option('--no-live', is_flag=True, help='Disable live progressive drawing animation (use traditional rendering)')
@click.option('--logo', is_flag=True, help='Enable logo/branding mode for larger, more detailed ASCII art (up to 150 chars width, 100 lines)')
def art(prompts, no_colors, provider, explain, no_live, logo):
    """Generate ASCII art from one or more text prompts.
    
    Live progressive rendering is enabled by default. Use --no-live to disable.
    Logo mode is automatically detected for prompts containing words like "logo", "branding", 
    "company", "text", etc. Use --logo to force logo mode, or --no-logo to disable auto-detection.
    
    Examples:
      ascii-gen art "a cat wearing sunglasses"
      ascii-gen art "a cat" "a dog" "a bird" --provider groq
      ascii-gen art "a cat" --provider groq --no-colors
      ascii-gen art "a cat" --explain
      ascii-gen art "a cat" --no-live  # Use traditional rendering
      ascii-gen art "logo for a company called Newton"  # Auto-detects logo mode
      ascii-gen art "MY COMPANY"  # Auto-detects logo mode (capitalized text)
      ascii-gen art "ASCII ART" --provider groq  # Auto-detects logo mode
      ascii-gen art "MY COMPANY" --logo  # Force logo mode
    """
    try:
        # Check if Groq is available for explanations (use temp renderer for errors)
        if explain and not config.GROQ_API_KEY:
            Renderer().render_error("--explain requires GROQ_API_KEY to be set in .env")
            sys.exit(1)

        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        # Start with art mode - will be auto-detected or overridden by --logo flag
        ai_client = create_ai_client(provider_name, mode="art")
        session_context = SessionContext()  # Session-based context instead of cache
        rate_limiter = RateLimiter()
        generator = ASCIIArtGenerator(ai_client, session_context, rate_limiter)

        # Process each prompt
        for i, prompt in enumerate(prompts, 1):
            # Create renderer with prompt context for intelligent coloring
            renderer = Renderer(prompt=prompt, mode="art")
            if len(prompts) > 1:
                renderer.render_info(f"Generating ASCII art {i}/{len(prompts)}: {prompt[:50]}...")
            else:
                if no_live:
                    renderer.render_loading("Generating ASCII art...")

            # Auto-detect logo mode (unless explicitly set via --logo flag)
            # logo is True if --logo flag is set, False if not set
            # Pass None to auto-detect, True to force logo, False to force art
            is_logo_mode = True if logo else None  # None = auto-detect, True = force logo
            
            # Determine title based on detected/forced mode
            if logo:
                # Explicitly set to logo mode
                detected_logo = True
            else:
                # Auto-detect
                detected_logo = generator._detect_logo_request(prompt)
            
            if detected_logo:
                title = f"Logo {i}" if len(prompts) > 1 else "Logo"
            else:
                title = f"ASCII Art {i}" if len(prompts) > 1 else "ASCII Art"
            
            if not no_live:
                # Use live progressive rendering
                stream_generator = generator.generate_stream(prompt, is_logo=is_logo_mode)
                final_content = renderer.render_ascii_progressive(stream_generator, title=title, use_colors=not no_colors)

                # For explanation, we need the full result
                if explain:
                    # Use streamed final content to avoid an extra paid API call
                    if final_content and not final_content.startswith("ERROR_CODE:"):
                        renderer.render_loading("Generating explanation...")
                        explanation = generate_explanation(final_content, 'art', prompt)
                        renderer.clear_line()
                        renderer.render_explanation(explanation, title="Explanation")
            else:
                # Traditional non-streaming rendering
                result = generator.generate(prompt, is_logo=is_logo_mode)

                renderer.clear_line()
                # Check if result is an error
                if result.startswith("ERROR_CODE:"):
                    renderer.render_error(result)
                    if len(prompts) > 1:
                        continue  # Continue with next prompt
                    else:
                        sys.exit(1)
                else:
                    # Title already determined above
                    renderer.render_ascii(result, title=title, use_colors=not no_colors)

                    # Generate explanation if requested
                    if explain:
                        renderer.render_loading("Generating explanation...")
                        explanation = generate_explanation(result, 'art', prompt)
                        renderer.clear_line()
                        renderer.render_explanation(explanation, title="Explanation")
        
    except Exception as e:
        Renderer().render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('prompts', nargs=-1, required=True)
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False),
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
@click.option('--explain', is_flag=True, help='Get an explanation of the generated chart from Groq')
@click.option('--no-live', is_flag=True, help='Disable live progressive drawing animation (use traditional rendering)')
def chart(prompts, provider, explain, no_live):
    """Generate a chart from one or more text prompts.

    Live progressive rendering is enabled by default. Use --no-live to disable.

    Examples:
      ascii-gen chart "bar chart: Q1=100, Q2=150, Q3=120, Q4=200"
      ascii-gen chart "sales data" "revenue growth" --provider groq
      ascii-gen chart "bar chart: Q1=100, Q2=150" --explain
      ascii-gen chart "bar chart: Q1=100" --no-live  # Use traditional rendering
    """
    try:
        # Check if Groq is available for explanations
        if explain and not config.GROQ_API_KEY:
            Renderer().render_error("--explain requires GROQ_API_KEY to be set in .env")
            sys.exit(1)

        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name, mode="chart")
        session_context = SessionContext()
        rate_limiter = RateLimiter()
        generator = ChartGenerator(ai_client, session_context, rate_limiter)

        # Process each prompt
        for i, prompt in enumerate(prompts, 1):
            # Create renderer with prompt context for intelligent coloring
            renderer = Renderer(prompt=prompt, mode="chart")
            if len(prompts) > 1:
                renderer.render_info(f"Generating chart {i}/{len(prompts)}: {prompt[:50]}...")
            else:
                if no_live:
                    renderer.render_loading("Generating chart...")

            if not no_live:
                # Use live progressive rendering
                title = f"Chart {i}" if len(prompts) > 1 else "Chart"
                try:
                    stream_generator = generator.generate_stream(prompt)
                    final_content = renderer.render_ascii_progressive(stream_generator, title=title, use_colors=True)
                except KeyboardInterrupt:
                    renderer.clear_line()
                    renderer.render_error("Generation interrupted by user")
                    if len(prompts) > 1:
                        continue
                    else:
                        sys.exit(1)
                except Exception as e:
                    renderer.clear_line()
                    renderer.render_error(f"Error during chart generation: {str(e)}")
                    if len(prompts) > 1:
                        continue
                    else:
                        sys.exit(1)

                # For explanation, we need the full result
                if explain:
                    # Use streamed final content to avoid an extra paid API call
                    if final_content and not final_content.startswith("ERROR_CODE:"):
                        renderer.render_loading("Generating explanation...")
                        explanation = generate_explanation(final_content, 'chart', prompt)
                        renderer.clear_line()
                        renderer.render_explanation(explanation, title="Explanation")
            else:
                # Traditional non-streaming rendering
                result = generator.generate(prompt)

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
                    renderer.render_ascii(result, title=title, use_colors=True)

                    # Generate explanation if requested
                    if explain:
                        renderer.render_loading("Generating explanation...")
                        explanation = generate_explanation(result, 'chart', prompt)
                        renderer.clear_line()
                        renderer.render_explanation(explanation, title="Explanation")
        
    except Exception as e:
        Renderer().render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('prompts', nargs=-1, required=True)
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False),
              default='top-to-bottom', help='Diagram orientation: top-to-bottom or left-to-right (default: top-to-bottom)')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False),
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
@click.option('--no-live', is_flag=True, help='Disable live progressive drawing animation (use traditional rendering)')
def diagram(prompts, orientation, provider, no_live):
    """Generate a diagram from one or more text prompts.

    Live progressive rendering is enabled by default. Use --no-live to disable.

    Examples:
      ascii-gen diagram "flowchart: user login -> authenticate -> dashboard"
      ascii-gen diagram "workflow" "auth flow" --orientation left-to-right --provider groq
      ascii-gen diagram "flowchart" --no-live  # Use traditional rendering
    """
    try:
        # Normalize orientation values
        if orientation.lower() in ['t2b', 'top-to-bottom', 'vertical', 'tb']:
            orientation = 'top-to-bottom'
        elif orientation.lower() in ['l2r', 'left-to-right', 'horizontal', 'lr']:
            orientation = 'left-to-right'

        # Initialize components
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        ai_client = create_ai_client(provider_name, mode="diagram")
        session_context = SessionContext()
        rate_limiter = RateLimiter()
        generator = DiagramGenerator(ai_client, session_context, rate_limiter)

        # Process each prompt
        for i, prompt in enumerate(prompts, 1):
            # Create renderer with prompt context for intelligent coloring
            renderer = Renderer(prompt=prompt, mode="diagram")
            if len(prompts) > 1:
                renderer.render_info(f"Generating diagram {i}/{len(prompts)}: {prompt[:50]}...")
            else:
                if no_live:
                    renderer.render_loading("Generating diagram...")

            if not no_live:
                # Use live progressive rendering
                title = f"Diagram {i}" if len(prompts) > 1 else "Diagram"
                stream_generator = generator.generate_stream(prompt, orientation=orientation)
                renderer.render_ascii_progressive(stream_generator, title=title, use_colors=True)
            else:
                # Traditional non-streaming rendering
                result = generator.generate(prompt, orientation=orientation)

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
        Renderer().render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--max-files', default=50, help='Maximum number of files to analyze (default: 50)')
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False), 
              default='top-to-bottom', help='Diagram orientation: top-to-bottom or left-to-right (default: top-to-bottom)')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
def codebase(path, max_files, orientation, provider):
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
        
        # Limit summary size to avoid prompt issues
        max_summary_length = 2000
        if len(summary) > max_summary_length:
            summary = summary[:max_summary_length] + "\n\n... (summary truncated for brevity)"
            renderer.render_info(f"Note: Codebase summary truncated to {max_summary_length} chars")
        
        # Generate diagram
        provider_name = None if provider.lower() == 'auto' else provider.lower()
        try:
            ai_client = create_ai_client(provider_name, mode="diagram")
        except Exception as e:
            renderer.clear_line()
            renderer.render_error(f"Failed to create AI client: {str(e)}")
            renderer.render_info("Make sure GEMINI_API_KEY or GROQ_API_KEY is set in .env")
            sys.exit(1)
        
        session_context = SessionContext()
        rate_limiter = RateLimiter()

        generator = DiagramGenerator(ai_client, session_context, rate_limiter)
        
        # Normalize orientation values
        if orientation.lower() in ['t2b', 'top-to-bottom', 'vertical', 'tb']:
            orientation = 'top-to-bottom'
        elif orientation.lower() in ['l2r', 'left-to-right', 'horizontal', 'lr']:
            orientation = 'left-to-right'
        
        # Create prompt with codebase summary
        prompt = f"Create an architecture diagram for this codebase:\n\n{summary}"
        
        # Generate with error handling
        try:
            result = generator.generate(prompt, is_codebase=True, orientation=orientation)
        except KeyboardInterrupt:
            renderer.clear_line()
            renderer.render_error("Generation interrupted by user")
            sys.exit(1)
        except Exception as e:
            renderer.clear_line()
            renderer.render_error(f"Error generating diagram: {str(e)}")
            renderer.render_info("Try: --max-files 20 --provider groq")
            sys.exit(1)
        
        renderer.clear_line()
        # Check if result is an error
        if result.startswith("ERROR_CODE:"):
            renderer.render_error(result)
            sys.exit(1)
        else:
            renderer.render_ascii(result, title="Architecture Diagram")
        
    except Exception as e:
        Renderer().render_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('repo_url', required=True)
@click.option('--max-files', default=50, help='Maximum number of files to analyze (default: 50)')
@click.option('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
@click.option('--orientation', type=click.Choice(['top-to-bottom', 'left-to-right', 't2b', 'l2r'], case_sensitive=False), 
              default='top-to-bottom', help='Diagram orientation: top-to-bottom or left-to-right (default: top-to-bottom)')
@click.option('--provider', type=click.Choice(['gemini', 'groq', 'auto'], case_sensitive=False), 
              default='auto', help='AI provider: gemini, groq, or auto (default: auto)')
def github(repo_url, max_files, token, orientation, provider):
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
        session_context = SessionContext()
        rate_limiter = RateLimiter()

        generator = DiagramGenerator(ai_client, session_context, rate_limiter)
        
        # Normalize orientation values
        if orientation.lower() in ['t2b', 'top-to-bottom', 'vertical', 'tb']:
            orientation = 'top-to-bottom'
        elif orientation.lower() in ['l2r', 'left-to-right', 'horizontal', 'lr']:
            orientation = 'left-to-right'
        
        # Create prompt with codebase summary
        prompt = f"Create an architecture diagram for this codebase:\n\n{summary}"
        result = generator.generate(prompt, is_codebase=True, orientation=orientation)
        
        renderer.clear_line()
        # Check if result is an error
        if result.startswith("ERROR_CODE:"):
            renderer.render_error(result)
            sys.exit(1)
        else:
            renderer.render_ascii(result, title="Architecture Diagram")
        
    except Exception as e:
        Renderer().render_error(str(e))
        sys.exit(1)


@cli.command()
def clear_cache():
    """Clear the cache of generated content."""
    try:
        # Session context is in-memory only and auto-expires
        renderer = Renderer()
        renderer.render_info("Session context is in-memory only and auto-expires after 60 minutes.")
    except Exception as e:
        Renderer().render_error(str(e))
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


@cli.command()
def models():
    """List all available AI models for Gemini and Groq providers."""
    try:
        renderer = Renderer()
        
        # Gemini Models
        renderer.render_plain("=" * 70, style="bold blue")
        renderer.render_plain("Google Gemini Models", style="bold blue")
        renderer.render_plain("=" * 70, style="bold blue")
        renderer.render_plain("")
        
        gemini_models = [
            ("gemini-2.5-pro", "Recommended: Good balance of capability and availability (default)"),
            ("gemini-3-pro-preview", "Latest preview model (requires paid tier, may have availability issues)"),
            ("gemini-2.5-flash", "Fast, efficient model"),
            ("gemini-1.5-flash", "Free tier compatible"),
            ("gemini-1.5-pro", "More capable model"),
        ]
        
        current_gemini = config.GEMINI_MODEL
        for model, description in gemini_models:
            marker = " (current)" if model == current_gemini else ""
            renderer.render_plain(f"- {model}{marker}")
            renderer.render_plain(f"  {description}", style="dim")
            renderer.render_plain("")
        
        # Groq Models
        renderer.render_plain("=" * 70, style="bold blue")
        renderer.render_plain("Groq Models", style="bold blue")
        renderer.render_plain("=" * 70, style="bold blue")
        renderer.render_plain("")
        
        groq_models = [
            ("llama-3.3-70b-versatile", "LLaMa 3.3 70B - 128K context, highly capable (recommended)"),
            ("openai/gpt-oss-120b", "GPT-OSS 120B - OpenAI's open-weight MoE model, 500+ t/s"),
            ("moonshotai/kimi-k2-instruct-0905", "Kimi K2 model - Fast and efficient"),
        ]
        
        current_groq = config.GROQ_MODEL
        for model, description in groq_models:
            marker = " (current)" if model == current_groq else ""
            renderer.render_plain(f"- {model}{marker}")
            renderer.render_plain(f"  {description}", style="dim")
            renderer.render_plain("")
        
        # Configuration info
        renderer.render_plain("=" * 70, style="bold blue")
        renderer.render_plain("Configuration", style="bold blue")
        renderer.render_plain("=" * 70, style="bold blue")
        renderer.render_plain("")
        renderer.render_plain("To change the model, set the following in your .env file:", style="dim")
        renderer.render_plain("  GEMINI_MODEL=gemini-2.5-pro")
        renderer.render_plain("  GROQ_MODEL=moonshotai/kimi-k2-instruct-0905")
        renderer.render_plain("")
        renderer.render_plain("Current configuration:", style="dim")
        if config.GEMINI_API_KEY:
            renderer.render_success(f"  Gemini: {current_gemini} (API key configured)")
        else:
            renderer.render_plain(f"  Gemini: {current_gemini} (API key not set)")
        
        if config.GROQ_API_KEY:
            renderer.render_success(f"  Groq: {current_groq} (API key configured)")
        else:
            renderer.render_plain(f"  Groq: {current_groq} (API key not set)")
        renderer.render_plain("")
        
    except Exception as e:
        Renderer().render_error(f"Error listing models: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    cli()

