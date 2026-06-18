from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.config import KNOWLEDGE_ROOT, settings


@dataclass
class KnowledgeHit:
    title: str
    source: str
    snippet: str
    score: int


class LocalKnowledgeBase:
    """Small local retrieval layer for the POC before Vertex AI Search is enabled."""

    STOPWORDS = {
        "about",
        "after",
        "also",
        "and",
        "are",
        "can",
        "change",
        "could",
        "for",
        "from",
        "have",
        "help",
        "how",
        "into",
        "may",
        "need",
        "please",
        "should",
        "that",
        "the",
        "this",
        "want",
        "what",
        "when",
        "where",
        "with",
        "you",
        "your",
    }

    def __init__(self, root: Path = KNOWLEDGE_ROOT) -> None:
        self.root = root
        self.documents = self._load_documents()

    def _load_documents(self) -> list[dict[str, str]]:
        documents: list[dict[str, str]] = []
        for path in sorted(self.root.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = self._extract_title(text) or path.stem.replace("_", " ").title()
            documents.append(
                {
                    "title": title,
                    "source": str(path.relative_to(self.root)),
                    "text": text,
                }
            )
        return documents

    @staticmethod
    def _extract_title(text: str) -> str | None:
        for line in text.splitlines():
            if line.startswith("# "):
                return line.replace("# ", "", 1).strip()
        return None

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
            if len(token) > 2 and token not in LocalKnowledgeBase.STOPWORDS
        }

    def search(self, query: str, limit: int = 3) -> list[KnowledgeHit]:
        query_tokens = self._tokens(query)
        hits: list[KnowledgeHit] = []

        for document in self.documents:
            text = document["text"]
            doc_tokens = self._tokens(text)
            score = len(query_tokens & doc_tokens)
            if score == 0:
                continue
            snippet = self._best_snippet(text, query_tokens)
            hits.append(
                KnowledgeHit(
                    title=document["title"],
                    source=document["source"],
                    snippet=snippet,
                    score=score,
                )
            )

        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]

    @staticmethod
    def _best_snippet(text: str, query_tokens: set[str]) -> str:
        paragraphs = [paragraph.strip() for paragraph in text.split("\n\n")]
        scored = []
        for paragraph in paragraphs:
            score = len(LocalKnowledgeBase._tokens(paragraph) & query_tokens)
            scored.append((score, paragraph))
        best = max(scored, key=lambda item: item[0], default=(0, ""))
        return best[1].replace("\n", " ")[:700]


class KnowledgeService:
    def __init__(self) -> None:
        self.local = LocalKnowledgeBase()

    def search(self, query: str, limit: int = 3) -> dict[str, object]:
        if settings.knowledge_backend == "vertex_ai_search":
            return {
                "backend": "vertex_ai_search",
                "status": "not_connected_in_local_runtime",
                "message": (
                    "Vertex AI Search is configured through GCP. Use the docs and scripts "
                    "to create/import the data store, then wire the serving client here."
                ),
                "hits": [],
            }

        hits = self.local.search(query=query, limit=limit)
        return {
            "backend": "local",
            "hits": [
                {
                    "title": hit.title,
                    "source": hit.source,
                    "snippet": hit.snippet,
                    "score": hit.score,
                }
                for hit in hits
            ],
        }
