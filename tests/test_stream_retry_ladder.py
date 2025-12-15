"""Ensure streaming retries don't loop forever on ladder/template failures."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.client import AIClient
from generators.ascii_art import ASCIIArtGenerator


class FakeStreamClient(AIClient):
    """Fake AI client that yields predetermined streaming outputs per call."""

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = 0

    def generate(self, prompt: str, system_prompt=None) -> str:
        # Not used in this test.
        self.calls += 1
        return self.outputs[min(self.calls - 1, len(self.outputs) - 1)]

    def generate_stream(self, prompt: str, system_prompt=None):
        self.calls += 1
        out = self.outputs[min(self.calls - 1, len(self.outputs) - 1)]
        # Yield as a single chunk for simplicity.
        yield out

    def is_available(self) -> bool:
        return True


class NoopRateLimiter:
    def wait_if_needed(self):
        return None


def test_stream_stops_after_repeated_ladder_failures():
    # A degenerate ladder-like output (same line repeated 12 times).
    ladder = "\n".join(["/ /| |\\ \\"] * 12) + "\n"
    client = FakeStreamClient([ladder, ladder, ladder, ladder])
    gen = ASCIIArtGenerator(client, session_context=None, rate_limiter=NoopRateLimiter(), max_retries=2)

    chunks = list(gen.generate_stream("a dragon", is_logo=False))
    joined = "".join(chunks)

    assert "ERROR_CODE: VALIDATION_FAILED" in joined
    # Ensure we did not retry unboundedly: initial + (max_retries+1) attempts maximum.
    assert client.calls <= 1 + (gen.max_retries + 1)


