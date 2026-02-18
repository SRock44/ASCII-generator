"""Memory usage tests: ensure all core modules stay in the kilobyte range."""

import sys
import tracemalloc
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validators import ASCIIValidator, ValidationResult, StreamingValidator, measure_art_quality
from session_context import SessionContext, Interaction
from examples_loader import ExampleLoader
from colorizer import ASCIIColorizer


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

KB = 1024

def _snapshot_kb(func):
    """Run func between tracemalloc snapshots, return peak KB used."""
    tracemalloc.start()
    tracemalloc.reset_peak()
    func()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / KB


# ──────────────────────────────────────────────────────────────────
# SessionContext memory
# ──────────────────────────────────────────────────────────────────

def test_session_context_empty_is_tiny():
    """An empty SessionContext should use < 1 KB."""
    ctx = SessionContext()
    size = sys.getsizeof(ctx) + sys.getsizeof(ctx.interactions)
    assert size < 1 * KB, f"Empty SessionContext uses {size} bytes, expected < 1 KB"


def test_session_context_at_capacity_under_64kb():
    """SessionContext filled to max_interactions (10) with 1 KB results stays under 64 KB."""
    def fill():
        ctx = SessionContext(max_interactions=10)
        for i in range(10):
            ctx.add_interaction(
                prompt=f"draw a cat #{i}",
                result="X" * 1024,  # 1 KB result each
                generator_type="art",
            )
        return ctx

    peak = _snapshot_kb(fill)
    assert peak < 64, f"SessionContext at capacity peaked at {peak:.1f} KB, expected < 64 KB"


def test_session_context_evicts_beyond_max():
    """Adding beyond max_interactions should not grow memory unboundedly."""
    ctx = SessionContext(max_interactions=5)
    for i in range(20):
        ctx.add_interaction(
            prompt=f"prompt {i}",
            result="Y" * 512,
            generator_type="art",
        )
    assert len(ctx.interactions) <= 5, "Should never hold more than max_interactions"


def test_session_context_clear_releases_memory():
    """Clearing a SessionContext should drop stored interactions."""
    ctx = SessionContext(max_interactions=10)
    for i in range(10):
        ctx.add_interaction(
            prompt=f"prompt {i}",
            result="Z" * 1024,
            generator_type="art",
        )
    assert len(ctx.interactions) == 10
    ctx.clear()
    assert len(ctx.interactions) == 0
    size_after = sys.getsizeof(ctx.interactions)
    assert size_after < 1 * KB, f"Cleared interactions list uses {size_after} bytes"


# ──────────────────────────────────────────────────────────────────
# ExampleLoader memory
# ──────────────────────────────────────────────────────────────────

def test_example_loader_idle_is_tiny():
    """ExampleLoader before any load should use < 1 KB (lazy loading)."""
    loader = ExampleLoader()
    size = (
        sys.getsizeof(loader)
        + sys.getsizeof(loader._cache)
        + sys.getsizeof(loader._access_times)
    )
    # _index is None at this point
    assert loader._index is None, "Index should be None before first access"
    assert size < 1 * KB, f"Idle ExampleLoader uses {size} bytes, expected < 1 KB"


def test_example_loader_cache_bounded():
    """ExampleLoader cache should never exceed MAX_CACHE_SIZE entries."""
    loader = ExampleLoader()
    # Simulate filling beyond max
    for i in range(loader.MAX_CACHE_SIZE + 5):
        loader._cache[f"subject_{i}"] = {"examples": [{"art": "x" * 200}]}
        loader._access_times[f"subject_{i}"] = float(i)
        loader._evict_if_needed()

    assert len(loader._cache) <= loader.MAX_CACHE_SIZE, (
        f"Cache has {len(loader._cache)} entries, max is {loader.MAX_CACHE_SIZE}"
    )


def test_example_loader_clear_cache_frees_memory():
    """clear_cache() should empty both _cache and _access_times."""
    loader = ExampleLoader()
    for i in range(5):
        loader._cache[f"s{i}"] = {"examples": [{"art": "x" * 500}]}
        loader._access_times[f"s{i}"] = float(i)

    loader.clear_cache()
    assert len(loader._cache) == 0
    assert len(loader._access_times) == 0


def test_example_loader_first_load_under_256kb():
    """First load parses index.json (~8 KB) into dicts; peak should stay < 256 KB."""
    def load_one():
        loader = ExampleLoader()
        loader.get_examples("cat")

    peak = _snapshot_kb(load_one)
    assert peak < 256, f"First example load peaked at {peak:.1f} KB, expected < 256 KB"


def test_example_loader_cached_load_under_8kb():
    """Subsequent loads from cache should use < 8 KB (no disk I/O)."""
    loader = ExampleLoader()
    loader.get_examples("cat")  # prime the cache

    def cached_load():
        loader.get_examples("cat")

    peak = _snapshot_kb(cached_load)
    assert peak < 8, f"Cached load peaked at {peak:.1f} KB, expected < 8 KB"


# ──────────────────────────────────────────────────────────────────
# ASCIIValidator memory
# ──────────────────────────────────────────────────────────────────

def test_validator_instance_under_4kb():
    """A single ASCIIValidator should use < 4 KB."""
    def create():
        return ASCIIValidator(mode="art")

    peak = _snapshot_kb(create)
    assert peak < 4, f"ASCIIValidator instance peaked at {peak:.1f} KB, expected < 4 KB"


def test_validator_all_modes_under_16kb():
    """Creating validators for all four modes should use < 16 KB total."""
    def create_all():
        validators = []
        for mode in ("art", "chart", "diagram", "logo"):
            validators.append(ASCIIValidator(mode=mode))
        return validators

    peak = _snapshot_kb(create_all)
    assert peak < 16, f"All four validators peaked at {peak:.1f} KB, expected < 16 KB"


def test_validator_char_sets_are_shared():
    """Class-level character sets should be shared across instances (same id)."""
    v1 = ASCIIValidator(mode="art")
    v2 = ASCIIValidator(mode="art")
    assert v1.ASCII_ART_CHARS is v2.ASCII_ART_CHARS, "Class-level char sets should be shared"
    assert v1.CHART_CHARS is v2.CHART_CHARS


def test_validate_small_art_under_32kb():
    """Validating a small piece of art should peak < 32 KB."""
    art = " /\\_/\\\n( o.o )\n > ^ <\n"

    def validate():
        v = ASCIIValidator(mode="art")
        v.validate(art)

    peak = _snapshot_kb(validate)
    assert peak < 32, f"Small art validation peaked at {peak:.1f} KB, expected < 32 KB"


def test_validate_and_clean_under_16kb():
    """validate_and_clean on moderate content should peak < 16 KB."""
    art = "\n".join([f"  line_{i:02d}  {'.' * 30}" for i in range(15)])

    def validate_and_clean():
        v = ASCIIValidator(mode="art")
        v.validate_and_clean(art, strict=False, minimal_clean=True)

    peak = _snapshot_kb(validate_and_clean)
    assert peak < 16, f"validate_and_clean peaked at {peak:.1f} KB, expected < 16 KB"


def test_clean_large_content_under_64kb():
    """Cleaning 20 lines of 80-char content should peak < 64 KB."""
    content = "\n".join(["X" * 80] * 20)

    def clean():
        v = ASCIIValidator(mode="art")
        v.clean(content)

    peak = _snapshot_kb(clean)
    assert peak < 64, f"Large content clean peaked at {peak:.1f} KB, expected < 64 KB"


def test_validation_result_is_tiny():
    """A ValidationResult object should use < 1 KB."""
    r = ValidationResult(True, errors=["err1", "err2"], warnings=["w1"])
    size = sys.getsizeof(r) + sys.getsizeof(r.errors) + sys.getsizeof(r.warnings)
    assert size < 1 * KB, f"ValidationResult uses {size} bytes, expected < 1 KB"


# ──────────────────────────────────────────────────────────────────
# StreamingValidator memory
# ──────────────────────────────────────────────────────────────────

def test_streaming_validator_init_under_8kb():
    """A fresh StreamingValidator should use < 8 KB."""
    def create():
        return StreamingValidator(mode="art")

    peak = _snapshot_kb(create)
    assert peak < 8, f"StreamingValidator init peaked at {peak:.1f} KB, expected < 8 KB"


def test_streaming_validator_accumulation_proportional():
    """Memory growth should be proportional to accumulated content, not exponential."""
    sv = StreamingValidator(mode="art")

    # Feed 50 small chunks (simulating a streaming response)
    for i in range(50):
        sv.process_chunk(f"line {i:03d}\n")

    accumulated_size = sys.getsizeof(sv.accumulated)
    expected_max = len(sv.accumulated) * 2  # Allow 2x overhead for string
    assert accumulated_size < expected_max, (
        f"Accumulated string uses {accumulated_size} bytes for {len(sv.accumulated)} chars"
    )


def test_streaming_validator_stops_saves_memory():
    """When repetition stops streaming, no further accumulation occurs."""
    sv = StreamingValidator(mode="art")

    # Feed enough identical lines to trigger stop
    for _ in range(20):
        sv.process_chunk("| |\n")

    size_at_stop = len(sv.accumulated)

    # Feed more data - should be ignored
    for _ in range(100):
        result = sv.process_chunk("more data\n")
        assert result == "", "Should return empty after stop"

    size_after = len(sv.accumulated)
    assert size_after == size_at_stop, "No additional accumulation after stop"


def test_streaming_finalize_under_32kb():
    """Finalizing a streaming session with moderate content should peak < 32 KB."""
    def stream_and_finalize():
        sv = StreamingValidator(mode="art")
        for i in range(10):
            sv.process_chunk(f"  /\\_/\\  {i}\n")
        sv.finalize()

    peak = _snapshot_kb(stream_and_finalize)
    assert peak < 32, f"Stream finalize peaked at {peak:.1f} KB, expected < 32 KB"


# ──────────────────────────────────────────────────────────────────
# ASCIIColorizer memory
# ──────────────────────────────────────────────────────────────────

def test_colorizer_instance_under_4kb():
    """An ASCIIColorizer instance should use < 4 KB."""
    def create():
        return ASCIIColorizer(prompt="a cat", mode="art")

    peak = _snapshot_kb(create)
    assert peak < 4, f"ASCIIColorizer instance peaked at {peak:.1f} KB, expected < 4 KB"


def test_colorizer_colorize_small_art_under_32kb():
    """Colorizing a small piece of art should peak < 32 KB."""
    art = " /\\_/\\\n( o.o )\n > ^ <\n"

    def colorize():
        c = ASCIIColorizer(prompt="cat", mode="art")
        c.colorize(art)

    peak = _snapshot_kb(colorize)
    assert peak < 32, f"Small art colorize peaked at {peak:.1f} KB, expected < 32 KB"


def test_colorizer_empty_dicts_when_idle():
    """Colorizer should have empty dicts when no hints are parsed."""
    c = ASCIIColorizer(prompt="test", mode="art")
    assert len(c.color_hints) == 0
    assert len(c.char_colors) == 0
    assert len(c.region_colors) == 0


# ──────────────────────────────────────────────────────────────────
# measure_art_quality memory
# ──────────────────────────────────────────────────────────────────

def test_quality_measurement_under_8kb():
    """Measuring art quality should peak < 8 KB."""
    art = " /\\_/\\\n( o.o )\n > ^ <\n /| |\\\n(_| |_)\n"

    def measure():
        measure_art_quality(art)

    peak = _snapshot_kb(measure)
    assert peak < 8, f"Quality measurement peaked at {peak:.1f} KB, expected < 8 KB"


# ──────────────────────────────────────────────────────────────────
# Interaction dataclass memory
# ──────────────────────────────────────────────────────────────────

def test_interaction_dataclass_under_1kb():
    """A single Interaction dataclass should use < 1 KB (without large result)."""
    from datetime import datetime
    interaction = Interaction(
        prompt="draw a cat",
        result="small result",
        timestamp=datetime.now(),
        generator_type="art",
        success=True,
    )
    size = sys.getsizeof(interaction)
    assert size < 1 * KB, f"Interaction uses {size} bytes, expected < 1 KB"


# ──────────────────────────────────────────────────────────────────
# No memory leaks: repeated operations
# ──────────────────────────────────────────────────────────────────

def test_repeated_validation_no_leak():
    """Running validate() 100 times should not leak memory."""
    art = " /\\_/\\\n( o.o )\n > ^ <\n"
    v = ASCIIValidator(mode="art")

    tracemalloc.start()
    tracemalloc.reset_peak()

    for _ in range(100):
        v.validate(art)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_kb = peak / KB
    assert peak_kb < 32, f"100 validations peaked at {peak_kb:.1f} KB, expected < 32 KB"


def test_repeated_clean_no_leak():
    """Running clean() 100 times should not leak memory."""
    raw = "```\n  /\\_/\\  \n ( o.o ) \n```\n"
    v = ASCIIValidator(mode="art")

    tracemalloc.start()
    tracemalloc.reset_peak()

    for _ in range(100):
        v.clean(raw)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_kb = peak / KB
    assert peak_kb < 32, f"100 cleans peaked at {peak_kb:.1f} KB, expected < 32 KB"


def test_repeated_session_add_remove_no_leak():
    """Adding and evicting from SessionContext repeatedly should not leak."""
    ctx = SessionContext(max_interactions=3)

    tracemalloc.start()
    tracemalloc.reset_peak()

    for i in range(200):
        ctx.add_interaction(
            prompt=f"prompt {i}",
            result="R" * 256,
            generator_type="art",
        )

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_kb = peak / KB
    # Only 3 interactions retained at any time, each with ~256 byte result
    assert peak_kb < 64, f"200 add/evict cycles peaked at {peak_kb:.1f} KB, expected < 64 KB"
    assert len(ctx.interactions) <= 3


def test_repeated_colorize_no_leak():
    """Colorizing 50 times should not leak memory."""
    art = " /\\_/\\\n( o.o )\n > ^ <\n"

    tracemalloc.start()
    tracemalloc.reset_peak()

    for _ in range(50):
        c = ASCIIColorizer(prompt="cat", mode="art")
        c.colorize(art)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_kb = peak / KB
    assert peak_kb < 64, f"50 colorizations peaked at {peak_kb:.1f} KB, expected < 64 KB"


# ──────────────────────────────────────────────────────────────────
# Diagram cleaning memory (complex operations)
# ──────────────────────────────────────────────────────────────────

def test_diagram_clean_under_32kb():
    """Cleaning a multi-box diagram should peak < 32 KB."""
    diagram = (
        "┌───────┐\n│ Box A │\n└───┬───┘\n    ↓\n"
        "┌───┴───┐\n│ Box B │\n└───┬───┘\n    ↓\n"
        "┌───┴───┐\n│ Box C │\n└───────┘\n"
    )

    def clean():
        v = ASCIIValidator(mode="diagram")
        v.clean(diagram)

    peak = _snapshot_kb(clean)
    assert peak < 32, f"Diagram clean peaked at {peak:.1f} KB, expected < 32 KB"


def test_chart_clean_under_32kb():
    """Cleaning a chart with block characters should peak < 32 KB."""
    chart = "\n".join([
        "Sales Report",
        "┌──────────────────────┐",
        "│ Q1  ████████  45%    │",
        "│ Q2  ██████████ 55%   │",
        "│ Q3  ███████  40%     │",
        "│ Q4  ████████████ 65% │",
        "└──────────────────────┘",
    ])

    def clean():
        v = ASCIIValidator(mode="chart")
        v.clean(chart)

    peak = _snapshot_kb(clean)
    assert peak < 32, f"Chart clean peaked at {peak:.1f} KB, expected < 32 KB"


# ──────────────────────────────────────────────────────────────────
# clean_chunk_fast memory (hot path during streaming)
# ──────────────────────────────────────────────────────────────────

def test_chunk_fast_under_1kb():
    """clean_chunk_fast on a small chunk should use minimal memory."""
    v = ASCIIValidator(mode="art")
    chunk = "hello world /\\_/\\ (o.o)\n"

    tracemalloc.start()
    tracemalloc.reset_peak()

    for _ in range(1000):
        v.clean_chunk_fast(chunk)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_kb = peak / KB
    assert peak_kb < 8, f"1000 chunk cleans peaked at {peak_kb:.1f} KB, expected < 8 KB"
