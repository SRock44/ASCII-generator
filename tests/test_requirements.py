"""Validate that requirements.txt dependencies are importable in the test environment."""

import re
import sys
from importlib import import_module
from pathlib import Path


def _parse_requirement_name(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    # Drop inline comments
    if " #" in line:
        line = line.split(" #", 1)[0].strip()
    # Skip options/includes
    if line.startswith(("-r", "--requirement", "-f", "--find-links", "--extra-index-url", "--index-url")):
        return None
    # Extract the distribution name before version specifiers/extras/markers
    m = re.match(r"^([A-Za-z0-9_.-]+)", line)
    return m.group(1) if m else None


def test_requirements_txt_deps_importable():
    project_root = Path(__file__).parent.parent
    req_file = project_root / "requirements.txt"
    assert req_file.exists(), "requirements.txt should exist"

    # Map PyPI distribution name -> import name
    import_name_overrides = {
        "google-generativeai": "google.generativeai",
        "python-dotenv": "dotenv",
        "PyGithub": "github",
    }

    requirements = []
    for raw in req_file.read_text(encoding="utf-8").splitlines():
        name = _parse_requirement_name(raw)
        if name:
            requirements.append(name)

    assert requirements, "requirements.txt should list at least one dependency"

    failures = []
    for dist_name in requirements:
        import_name = import_name_overrides.get(dist_name, dist_name.replace("-", "_"))
        try:
            import_module(import_name)
        except Exception as e:
            failures.append(f"{dist_name} -> import {import_name}: {type(e).__name__}: {e}")

    assert not failures, "Some requirements are not importable:\n" + "\n".join(failures)


