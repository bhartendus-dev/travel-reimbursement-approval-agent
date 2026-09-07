from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


POLICY_PATH = Path("data/policies/domestic_travel_policy.md")


@dataclass(frozen=True)
class PolicyChunk:
    policy_id: str
    section: str
    title: str
    text: str


def _tokenize(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_-]+", text)
        if len(token) > 1
    }


def load_policy_chunks(path: Path = POLICY_PATH) -> list[PolicyChunk]:
    raw = path.read_text(encoding="utf-8")

    policy_id_match = re.search(r"Policy ID:\s*([^\n]+)", raw)
    policy_id = policy_id_match.group(1).strip() if policy_id_match else "UNKNOWN"

    chunks: list[PolicyChunk] = []
    pattern = re.compile(
        r"^##\s+([A-Z]+-\d+)\s+—\s+([^\n]+)\n(.*?)(?=^##\s+|\Z)",
        flags=re.M | re.S,
    )

    for match in pattern.finditer(raw):
        section, title, body = match.groups()
        chunks.append(
            PolicyChunk(
                policy_id=policy_id,
                section=section.strip(),
                title=title.strip(),
                text=f"## {section} — {title}\n{body.strip()}",
            )
        )

    return chunks


def retrieve_policy(query: str, top_k: int = 2) -> list[dict]:
    """
    Lightweight lexical retrieval for the one-day prototype.

    This is still RAG: relevant external policy chunks are retrieved at runtime
    and supplied to generation. A production implementation can replace this
    retriever with enterprise vector / hybrid search without changing the
    workflow contract.
    """
    query_tokens = _tokenize(query)
    scored: list[tuple[float, PolicyChunk]] = []

    synonyms = {
        "cab": "taxi",
        "lodging": "hotel",
        "airfare": "flight",
        "food": "meal",
    }
    expanded = set(query_tokens)
    for token in list(query_tokens):
        if token in synonyms:
            expanded.add(synonyms[token])

    for chunk in load_policy_chunks():
        chunk_tokens = _tokenize(
            f"{chunk.section} {chunk.title} {chunk.text}"
        )

        overlap = len(expanded & chunk_tokens)
        section_bonus = 0

        # Strong category cues keep this tiny demo deterministic and explainable.
        for category in ("flight", "hotel", "meal", "taxi", "general"):
            if category in expanded and category in chunk.title.lower():
                section_bonus += 5

        score = float(overlap + section_bonus)
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)

    results: list[dict] = []
    for score, chunk in scored[:top_k]:
        results.append(
            {
                "policy_id": chunk.policy_id,
                "section": chunk.section,
                "title": chunk.title,
                "text": chunk.text,
                "retrieval_score": score,
            }
        )
    return results
