# TODO / Future Plans

## API & Model Support

1. **Local LLM support** - Support for local models (for those with deep pockets or decent NPU)
   - Integration with Ollama, LM Studio, or similar local inference servers
   - Support for quantized models that can run on consumer hardware

2. **Additional API support** - Support for other paid/free APIs
   - OpenAI GPT-4 / GPT-4o
   - Anthropic Claude
   - Mistral AI
   - Continue supporting free Gemini API tier

3. **MacOS support** - Ensure full compatibility and test on MacOS
   - Currently have no way to test if this works, someone let me know

## Feature Enhancements

4. **Size modifiers** - Allow users to specify output size
   - Small, medium, large, extra-large options
   - Custom width/height parameters
   - Adaptive sizing based on terminal dimensions

5. **Better color generation** - Enhanced color support
   - More sophisticated color schemes
   - Theme support (monochrome, pastel, vibrant, etc.)
   - Custom color palettes
   - Better color detection and application algorithms

6. **Terminal-based progressive rendering** - Real-time drawing animation
   - Draw the ASCII art progressively as it's being generated
   - Animate the drawing process in the terminal (like it's being drawn live)
   - Show progress character by character or line by line
   - Not just pasting the final result, but showing the creation process
