# ASCII Generator

A fast, intuitive CLI tool that generates ASCII art, charts, and diagrams using AI (Gemini or Groq). Create beautiful terminal visualizations from natural language prompts or by analyzing codebases.

## Features

-  **ASCII Art Generation** - Create detailed ASCII art from text descriptions
-  **Chart Generation** - Generate bar charts, line charts, and more
-  **Diagram Generation** - Create flowcharts and architecture diagrams
-  **Codebase Analysis** - Auto-generate architecture diagrams from local code
-  **GitHub Integration** - Analyze GitHub repositories and generate diagrams
-  **Caching** - Fast repeated generation with intelligent caching
-  **Rate Limiting** - Respects API limits automatically

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ASCII-Generator
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API key(s)
   ```

   Set at least one API key in `.env`:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here  # Optional
   ```

   You can use either Gemini or Groq (or both). If both are set, Gemini will be used by default (auto-selection).

## Usage

**Important:** Make sure to activate the virtual environment first, or use the venv Python directly:

```bash
# Option 1: Activate the virtual environment
source .venv/bin/activate
python cli.py art "a cat wearing sunglasses"

# Option 2: Use venv Python directly (without activation)
.venv/bin/python cli.py art "a cat wearing sunglasses"
```

### ASCII Art

Generate ASCII art from a text prompt:

```bash
python cli.py art "a cat wearing sunglasses"
python cli.py art "a rocket ship"
python cli.py art "Python logo"
python cli.py art "a cat" --explain  # Get an explanation from Groq
```

### Charts

Generate terminal-based charts:

```bash
python cli.py chart "bar chart: Q1=100, Q2=150, Q3=120, Q4=200"
python cli.py chart "line chart showing sales growth over 12 months"
python cli.py chart "bar chart showing monthly sales: January=50, February=75, March=100, April=120, May=90" --provider groq
python cli.py chart "line chart showing revenue growth over 12 months" --provider groq
python cli.py chart "bar chart: Q1=100, Q2=150" --explain  # Get an explanation from Groq
```

**Example Output:**

![Chart Examples](images/01.png)

*Example charts generated with Groq showing bar charts and line charts with proper formatting and visual representation.*

### Diagrams

Create flowcharts and diagrams:

```bash
python cli.py diagram "flowchart: user login -> authenticate -> dashboard"
python cli.py diagram "architecture: frontend -> API -> database"
python cli.py chart "entity relationship diagram of a basic bank account structure" --provider groq
```

**Example Output:**

![Entity Relationship Diagram](images/2.png)

*Example ERD diagram generated with Groq showing database structure with entities, attributes, and relationships.*

### Codebase Analysis

Generate architecture diagrams from local code:

```bash
python cli.py codebase /path/to/your/project
python cli.py codebase .  # Current directory
```

### GitHub Repository Analysis

Analyze GitHub repositories:

```bash
python cli.py github owner/repo-name
python cli.py github https://github.com/owner/repo
```

For private repositories, set `GITHUB_TOKEN` environment variable or use `--token`:

```bash
export GITHUB_TOKEN=your_github_token
python cli.py github owner/private-repo
```

### Other Commands

**Check configuration:**
```bash
python cli.py check
```

**Clear cache:**
```bash
python cli.py clear-cache
```

**Disable caching:**
```bash
python cli.py art "prompt" --no-cache
```

**Get explanations:**
```bash
python cli.py art "a cat" --explain
python cli.py chart "bar chart: Q1=100, Q2=150" --explain
```

The `--explain` flag uses Groq to generate a brief explanation of the generated ASCII art or chart. This is useful for understanding complex visualizations or getting insights about the generated content. **Note:** Requires `GROQ_API_KEY` to be set in your `.env` file.

## Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-pro
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=moonshotai/kimi-k2-instruct-0905
CACHE_ENABLED=true
CACHE_DIR=.cache
```

**Model Options:**

Gemini Models:
- `gemini-2.5-pro` - Recommended: Good balance of capability and availability (default)
- `gemini-3-pro-preview` - Latest preview model (requires paid tier, may have availability issues)
- `gemini-2.5-flash` - Fast, efficient model
- `gemini-1.5-flash` - Free tier compatible
- `gemini-1.5-pro` - More capable model

Groq Models:
- `moonshotai/kimi-k2-instruct-0905` - Kimi K2 model (default)

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
├── cache.py            # Caching system
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

**Note:** Groq's free tier is much more generous than Gemini's, making it ideal for high-volume usage or when you need faster responses. The Kimi K2 model is particularly fast and well-suited for chart generation.

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

