"""LLM Protocol + a deterministic fake for offline tests."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLM(Protocol):
    name: str

    def generate(self, system: str, user: str) -> str: ...


class FakeLLM:
    """Echoes a deterministic, citation-respecting answer.

    The fake always returns a string of the form::

        Based on [1] and [2]: <first sentence of chunk 1>

    so tests can assert structure without hitting a model. If the user
    prompt contains no chunk markers, returns an empty string — which
    the CitationValidator must downgrade.
    """

    name: str = "fake:echo"

    def __init__(self, *, force_empty: bool = False) -> None:
        self._force_empty = force_empty

    def generate(self, system: str, user: str) -> str:
        if self._force_empty:
            return ""
        markers: list[str] = []
        first_sentence = ""
        for line in user.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and "]" in stripped:
                marker = stripped.split("]")[0] + "]"
                markers.append(marker)
                rest = stripped.split("]", 1)[1].strip()
                if not first_sentence and rest:
                    first_sentence = rest.split(".")[0] + "."
        if not markers:
            return ""
        joined = " and ".join(markers)
        return f"Based on {joined}: {first_sentence}".strip()


def make_llm(spec: str) -> LLM:
    if spec.startswith("fake"):
        return FakeLLM()
    raise RuntimeError(
        f"LLM spec '{spec}' not implemented in v0.1.0. "
        "Configure FILEWISE_LLM=fake:echo for offline use."
    )
