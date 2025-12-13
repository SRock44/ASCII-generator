"""Lazy-loading example cache for ASCII art generation."""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


class ExampleLoader:
    """Lazy-loading example cache. Zero memory when idle."""

    MAX_CACHE_SIZE = 10  # Max cached categories

    def __init__(self, examples_dir: Optional[Path] = None):
        """
        Initialize ExampleLoader.

        Args:
            examples_dir: Path to examples directory. Defaults to project examples/.
        """
        if examples_dir is None:
            # Default to project examples directory
            project_root = Path(__file__).parent
            examples_dir = project_root / "examples"

        self.examples_dir = Path(examples_dir)
        self._index: Optional[Dict[str, Any]] = None  # Loaded on first use
        self._cache: Dict[str, Dict[str, Any]] = {}  # LRU cache: subject -> data
        self._access_times: Dict[str, float] = {}  # Track access times for LRU

    def _load_index(self) -> Dict[str, Any]:
        """Load index.json if not already loaded."""
        if self._index is None:
            index_file = self.examples_dir / "index.json"
            if not index_file.exists():
                # Return empty index if file doesn't exist
                self._index = {
                    "keywords": {},
                    "subjects": {},
                    "categories": {}
                }
            else:
                try:
                    with open(index_file, 'r') as f:
                        self._index = json.load(f)
                except Exception:
                    self._index = {
                        "keywords": {},
                        "subjects": {},
                        "categories": {}
                    }
        return self._index

    def _find_subject(self, query: str) -> Optional[str]:
        """
        Find matching subject from query using keyword matching.

        Args:
            query: User query (e.g., "an elephant", "cat", "a dog")

        Returns:
            Subject name if found, None otherwise
        """
        index = self._load_index()
        query_lower = query.lower().strip()

        # Extract keywords from query (remove common words)
        stop_words = {'a', 'an', 'the', 'of', 'in', 'on', 'at', 'for', 'with', 'and', 'or'}
        query_words = [w.strip('.,!?;:') for w in query_lower.split() if w not in stop_words]

        # Check direct keyword matches
        keywords = index.get("keywords", {})
        for word in query_words:
            if word in keywords:
                return keywords[word]

        # Check if query itself is a keyword
        if query_lower in keywords:
            return keywords[query_lower]

        # Check if any query word matches a subject name
        subjects = index.get("subjects", {})
        for word in query_words:
            if word in subjects:
                return word

        # Check partial matches (e.g., "elephants" -> "elephant")
        for word in query_words:
            for keyword, subject in keywords.items():
                if word in keyword or keyword in word:
                    return subject

        return None

    def _load_subject_file(self, subject: str) -> Optional[Dict[str, Any]]:
        """
        Load a subject's JSON file from disk.

        Args:
            subject: Subject name (e.g., "elephant")

        Returns:
            Subject data dict or None if not found
        """
        index = self._load_index()
        subjects = index.get("subjects", {})

        if subject not in subjects:
            return None

        rel_path = subjects[subject]
        file_path = self.examples_dir / rel_path

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data
        except Exception:
            return None

    def _evict_if_needed(self):
        """LRU eviction - removes oldest if over limit."""
        if len(self._cache) > self.MAX_CACHE_SIZE:
            # Find oldest accessed item
            if self._access_times:
                oldest = min(self._access_times.items(), key=lambda x: x[1])[0]
                del self._cache[oldest]
                del self._access_times[oldest]

    def get_examples(self, subject: str, count: int = 2) -> List[Dict[str, Any]]:
        """
        Get relevant examples for a subject. Loads from disk only when needed.

        Args:
            subject: User query (e.g., "an elephant", "cat")
            count: Number of examples to return (default: 2)

        Returns:
            List of example dicts with 'art', 'lines', 'width' keys
        """
        import time

        # Find matching subject
        matched_subject = self._find_subject(subject)
        if not matched_subject:
            return []  # No match found

        # Check cache first
        if matched_subject in self._cache:
            self._access_times[matched_subject] = time.time()
            examples = self._cache[matched_subject].get("examples", [])
            return examples[:count]

        # Load from disk
        data = self._load_subject_file(matched_subject)
        if not data or not data.get("examples"):
            return []

        # Cache it
        self._evict_if_needed()
        self._cache[matched_subject] = data
        self._access_times[matched_subject] = time.time()

        examples = data.get("examples", [])
        return examples[:count]

    def clear_cache(self):
        """Clear the in-memory cache (useful for testing)."""
        self._cache.clear()
        self._access_times.clear()

