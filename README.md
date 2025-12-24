# ASCII Generator

Expected Alpha Testing: January 2026

A fast, intuitive CLI tool that generates ASCII art, charts, and diagrams using AI (Gemini or Groq). Create beautiful terminal visualizations from natural language prompts or by analyzing codebases.

## Features

-  **Intelligent Context-Aware Coloring** - Beautiful colors based on what you're drawing (NEW!)
-  **ASCII Art Generation** - Create detailed ASCII art from text descriptions
-  **Chart Generation** - Generate bar charts, line charts, and more with colorful data visualization
-  **Diagram Generation** - Create flowcharts and architecture diagrams with vibrant colors
-  **Live Streaming Mode** - Watch your ASCII being drawn in real-time with colors
-  **Codebase Analysis** - Auto-generate architecture diagrams from local code
-  **GitHub Integration** - Analyze GitHub repositories and generate diagrams
-  **Rate Limiting** - Respects API limits automatically

## Quick Installation (30 Seconds!)

```bash
cd ~/Projects/ASCII-Generator
./install.sh
```

The automated installer:
1. Installs the package in your virtual environment
2. Sets up a global `ascii` command (works from any directory!)
3. No manual virtual environment activation needed

After installation:
```bash
# Reload your shell
source ~/.bashrc  # or source ~/.zshrc

# First run triggers automatic API key setup wizard
ascii check

# Generate your first ASCII art!
ascii art "a cat" --live
```

**Get your free API keys:**
- **Groq**: https://console.groq.com/keys (Recommended, faster)
- **Gemini**: https://makersuite.google.com/app/apikey (Optional)

API keys are stored locally in `.env` file (never uploaded, private to you).

---

## Usage

No need to activate virtual environments - just use `ascii` from anywhere:

```bash
# From ANY directory:
ascii art "a cat wearing sunglasses"
ascii chart "Q1=100, Q2=150, Q3=200" --live
ascii diagram "user login flow" --provider groq
```

---

## Command-Line Reference

### Complete Command Guide

```bash
ascii <command> [arguments] [options]
```

### Commands Overview

| Command | Description |
|---------|-------------|
| `art` | Generate ASCII art from text prompts |
| `chart` | Generate terminal-based charts and graphs |
| `diagram` | Create flowcharts and architecture diagrams |
| `codebase` | Analyze local codebase and generate diagrams |
| `github` | Analyze GitHub repositories |
| `check` | Verify API configuration and test connection |
| `models` | List all available AI models |
| `clear-cache` | Clear the cache of generated content |

---

### `ascii art` - Generate ASCII Art

Generate ASCII art from one or more text descriptions.

**Syntax:**
```bash
ascii art <prompt>... [options]
```

**Arguments:**
- `<prompt>` - One or more text descriptions (required)

**Options:**
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--provider` | choice | `auto` | AI provider: `gemini`, `groq`, or `auto` |
| `--no-colors` | flag | enabled | Disable color output (monochrome mode) |
| `--explain` | flag | disabled | Get AI-generated explanation of the art |
| `--no-live` | flag | enabled | Disable live progressive rendering |
| `--logo` | flag | auto-detect | Force logo/branding mode (150 chars width, 100 lines) |

**Examples:**
```bash
# Basic usage
ascii art "a cat wearing sunglasses"

# Multiple prompts
ascii art "a cat" "a dog" "a bird"

# With provider selection
ascii art "a dragon" --provider groq

# Monochrome output
ascii art "a mountain landscape" --no-colors

# Get explanation
ascii art "a robot" --explain

# Logo mode (auto-detected for uppercase text or "logo" keyword)
ascii art "ACME CORP"
ascii art "logo for Newton Inc" --logo
```

**Auto-Detection:**
- Logo mode is automatically enabled for:
  - Prompts containing "logo", "branding", "company", "brand"
  - Text in ALL CAPS (e.g., "MY COMPANY")
  - Use `--logo` to force logo mode

---

### `ascii chart` - Generate Charts

Create terminal-based charts and data visualizations.

**Syntax:**
```bash
ascii chart <prompt>... [options]
```

**Arguments:**
- `<prompt>` - Chart description or data (required)

**Options:**
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--provider` | choice | `auto` | AI provider: `gemini`, `groq`, or `auto` |
| `--explain` | flag | disabled | Get AI-generated explanation of the chart |
| `--no-live` | flag | enabled | Disable live progressive rendering |

**Examples:**
```bash
# Simple bar chart
ascii chart "Q1=100, Q2=150, Q3=120, Q4=200"

# Descriptive prompt
ascii chart "sales growth over 12 months"

# With specific data
ascii chart "monthly sales: Jan=50, Feb=75, Mar=100"

# Get explanation
ascii chart "quarterly revenue 2024" --explain

# Using Groq provider
ascii chart "user signups by month" --provider groq
```

---

### `ascii diagram` - Generate Diagrams

Create flowcharts, architecture diagrams, and process flows.

**Syntax:**
```bash
ascii diagram <prompt>... [options]
```

**Arguments:**
- `<prompt>` - Diagram description (required)

**Options:**
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--orientation` | choice | `top-to-bottom` | Layout: `top-to-bottom`, `left-to-right`, `t2b`, `l2r` |
| `--provider` | choice | `auto` | AI provider: `gemini`, `groq`, or `auto` |
| `--no-live` | flag | enabled | Disable live progressive rendering |

**Examples:**
```bash
# Simple flow
ascii diagram "user login -> authenticate -> dashboard"

# Architecture diagram
ascii diagram "frontend -> API -> database"

# Horizontal layout
ascii diagram "CI/CD pipeline" --orientation left-to-right
ascii diagram "oauth2 flow" --orientation l2r

# Complex process
ascii diagram "e-commerce checkout process" --provider groq
```

**Orientation Options:**
- `top-to-bottom` or `t2b` - Vertical flow (default)
- `left-to-right` or `l2r` - Horizontal flow

---

### `ascii codebase` - Analyze Local Codebase

Generate architecture diagrams from local code repositories.

**Syntax:**
```bash
ascii codebase [path] [options]
```

**Arguments:**
- `[path]` - Path to codebase (default: current directory `.`)

**Options:**
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--max-files` | integer | `50` | Maximum number of files to analyze |
| `--orientation` | choice | `top-to-bottom` | Layout: `top-to-bottom`, `left-to-right`, `t2b`, `l2r` |
| `--provider` | choice | `auto` | AI provider: `gemini`, `groq`, or `auto` |

**Examples:**
```bash
# Analyze current directory
ascii codebase

# Analyze specific project
ascii codebase /path/to/project

# Limit file analysis
ascii codebase ./my-app --max-files 100

# Horizontal layout
ascii codebase . --orientation left-to-right

# Use specific provider
ascii codebase ~/projects/app --provider groq
```

---

### `ascii github` - Analyze GitHub Repository

Generate architecture diagrams from GitHub repositories (public or private).

**Syntax:**
```bash
ascii github <repo> [options]
```

**Arguments:**
- `<repo>` - GitHub repository (required)
  - Format: `owner/repo-name`
  - Or full URL: `https://github.com/owner/repo`

**Options:**
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--max-files` | integer | `50` | Maximum number of files to analyze |
| `--token` | string | `$GITHUB_TOKEN` | GitHub personal access token (for private repos) |
| `--orientation` | choice | `top-to-bottom` | Layout: `top-to-bottom`, `left-to-right`, `t2b`, `l2r` |
| `--provider` | choice | `auto` | AI provider: `gemini`, `groq`, or `auto` |

**Examples:**
```bash
# Analyze public repository
ascii github facebook/react

# Using full URL
ascii github https://github.com/microsoft/vscode

# Private repository (with token)
ascii github myorg/private-repo --token ghp_xxxxxxxxxxxx

# Or set environment variable
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
ascii github myorg/private-repo

# With custom options
ascii github golang/go --max-files 100 --orientation l2r
```

---

### `ascii check` - Verify Configuration

Test API configuration and verify connectivity.

**Syntax:**
```bash
ascii check [options]
```

**Options:**
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--provider` | choice | `auto` | Provider to check: `gemini`, `groq`, or `auto` |

**Examples:**
```bash
# Check all configured providers
ascii check

# Check specific provider
ascii check --provider groq
ascii check --provider gemini
```

**First-Time Setup:**
- If `.env` file doesn't exist, this command triggers the interactive setup wizard
- Prompts for Groq API key (recommended)
- Optionally configure Gemini API key
- Saves configuration to `.env` file

---

### `ascii models` - List Available Models

Display all available AI models for both Gemini and Groq providers.

**Syntax:**
```bash
ascii models
```

**Output includes:**
- Gemini models (gemini-2.5-pro, gemini-3-pro-preview, etc.)
- Groq models (llama-3.3-70b-versatile, openai/gpt-oss-120b, etc.)
- Current configured models
- Model descriptions and capabilities

**Example:**
```bash
ascii models
```

---

### `ascii clear-cache` - Clear Cache

Clear the cache of generated ASCII content.

**Syntax:**
```bash
ascii clear-cache
```

**Example:**
```bash
ascii clear-cache
```

---

## Global Options

These options work with most commands:

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--provider` | `gemini`, `groq`, `auto` | `auto` | Select AI provider |
| `--no-live` | flag | live enabled | Disable progressive rendering |
| `--orientation` | `top-to-bottom`, `left-to-right`, `t2b`, `l2r` | `top-to-bottom` | Diagram layout (diagrams only) |
| `--no-colors` | flag | colors enabled | Monochrome output (art only) |
| `--explain` | flag | disabled | Generate explanation (art/chart only) |
| `--help` | flag | - | Show command help |
| `--version` | flag | - | Show version information |

---

## Quick Tips

**Provider Selection:**
- `auto` (default) - Automatically selects available provider
- `groq` - Fast, generous free tier (recommended for live mode)
- `gemini` - Google's models, good for complex tasks

**Live Mode:**
- Enabled by default for real-time streaming
- Use `--no-live` for traditional batch rendering
- Works best with Groq provider

**Logo Mode:**
- Auto-detects uppercase text or "logo" keywords
- Supports larger output (150 chars × 100 lines)
- Includes block characters (█░▒▓)

**File Analysis Limits:**
- Default: 50 files
- Increase with `--max-files` for larger projects
- Higher values may increase API usage

---

### ASCII Art

Generate ASCII art from a text prompt:

```bash
ascii art "a cat wearing sunglasses"
ascii art "a rocket ship" --live
ascii art "Python logo" --provider groq
ascii art "a dragon" --explain  # Get an explanation
```

### Charts

Generate terminal-based charts:

```bash
ascii chart "Q1=100, Q2=150, Q3=120, Q4=200"
ascii chart "sales growth over 12 months" --live
ascii chart "monthly sales: Jan=50, Feb=75, Mar=100" --provider groq
ascii chart "Q1=100, Q2=150" --explain  # Get an explanation
```

**Example Output:**

![Chart Examples](images/01.png)

*Example charts generated with Groq showing bar charts and line charts with proper formatting and visual representation.*

### Diagrams

Create flowcharts and diagrams:

```bash
ascii diagram "user login -> authenticate -> dashboard"
ascii diagram "frontend -> API -> database" --live
ascii diagram "oauth2 authentication flow" --provider groq
ascii diagram "CI/CD pipeline" --orientation left-to-right
```

**Example Output:**

![Entity Relationship Diagram](images/2.png)

*Example ERD diagram generated with Groq showing database structure with entities, attributes, and relationships.*

### Codebase Analysis

Generate architecture diagrams from local code:

```bash
ascii codebase /path/to/your/project
ascii codebase .  # Current directory
```

### GitHub Repository Analysis

Analyze GitHub repositories:

```bash
ascii github owner/repo-name
ascii github https://github.com/owner/repo
```

For private repositories, set `GITHUB_TOKEN` environment variable or use `--token`:

```bash
export GITHUB_TOKEN=your_github_token
ascii github owner/private-repo
```

### Other Commands

**Check configuration:**
```bash
ascii check  # Triggers setup wizard if .env doesn't exist
```

**List available models:**
```bash
ascii models  # List all available AI models for Gemini and Groq
```

**Note:** The generator uses session-based context (in-memory) to maintain continuity across requests. Context automatically expires after 60 minutes.

**Get explanations:**
```bash
ascii art "a cat" --explain
ascii chart "Q1=100, Q2=150" --explain
```

The `--explain` flag generates a brief explanation of the ASCII art or chart. Useful for understanding complex visualizations.

## Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-pro
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

**Model Options:**

Gemini Models:
- `gemini-2.5-pro` - Recommended: Good balance of capability and availability (default)
- `gemini-3-pro-preview` - Latest preview model (requires paid tier, may have availability issues)
- `gemini-2.5-flash` - Fast, efficient model
- `gemini-1.5-flash` - Free tier compatible
- `gemini-1.5-pro` - More capable model

Groq Models:
- `llama-3.3-70b-versatile` - LLaMa 3.3 70B with 128K context (default, recommended)
- `openai/gpt-oss-120b` - GPT-OSS 120B MoE model, 500+ tokens/sec
- `moonshotai/kimi-k2-instruct-0905` - Kimi K2 model (legacy)

## Project Structure

```
ASCII-Generator/
├── cli.py              # Main CLI entry point
├── config.py           # Configuration management
├── ai/
│   ├── client.py       # Abstract AI client interface
│   ├── gemini.py       # Google Gemini implementation
│   ├── groq_client.py  # Groq API implementation
│   ├── factory.py      # AI client factory (auto-select provider)
│   └── prompts.py      # System prompts
├── generators/
│   ├── ascii_art.py    # ASCII art generator
│   ├── charts.py       # Chart generator
│   └── diagrams.py     # Diagram generator
├── parsers/
│   ├── codebase.py     # Local codebase parser
│   └── github.py       # GitHub repository parser
├── renderer.py         # Terminal output with Rich
├── rate_limiter.py     # Rate limiting
└── requirements.txt    # Dependencies
```

## API Limits

### Gemini Free Tier
- **15 requests per minute (RPM)**
- **1 million tokens per day**

### Groq Free Tier (Very Generous!)
- **60 requests per minute (RPM)**
- **1,000 requests per day**
- **10,000 tokens per minute**
- **300,000 tokens per day**

The rate limiter automatically handles these limits. If you hit the limit, the tool will wait before making the next request.

**Note:** Groq's free tier is much more generous than Gemini's, making it ideal for high-volume usage or when you need faster responses. The LLaMa 3.3 70B model offers excellent performance with 128K context, while GPT-OSS 120B provides blazing-fast inference at 500+ tokens/sec.

## Requirements

- Python 3.11+
- Google Gemini API key (free tier available)
- Internet connection for AI generation

## Dependencies

- `click` - CLI framework
- `rich` - Terminal formatting and colors
- `google-generativeai` - Google Gemini SDK
- `groq` - Groq API SDK (for Kimi K2 model)
- `python-dotenv` - Environment variable management
- `requests` - HTTP requests
- `PyGithub` - GitHub API client

## Examples

### Example 1: ASCII Art
```bash
$ python cli.py art "a coffee cup"
```

### Example 2: Chart
```bash
$ python cli.py chart "bar chart: January=50, February=75, March=100"
```

### Example 3: Architecture Diagram
```bash
$ python cli.py codebase ./my-project
```

### Example 4: GitHub Analysis
```bash
$ python cli.py github facebook/react
```

## Troubleshooting

**Error: GEMINI_API_KEY is required**
- Make sure you've created a `.env` file with your API key
- Or set the environment variable: `export GEMINI_API_KEY=your_key`

**Error: Rate limit exceeded**
- The tool automatically handles rate limiting, but if you see this, wait a minute and try again

**Error: GitHub token not configured**
- For private repositories, set `GITHUB_TOKEN` environment variable
- Or use `--token` flag: `python cli.py github owner/repo --token your_token`

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

