"""Deterministic retrieval over the bundled offline research corpus."""

import json
import re
from pathlib import Path
from typing import Any

from multi_agent_research_lab.core.schemas import SourceDocument

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "with",
    "write",
}


class SearchClient:
    """Search embedded articles and source cards without network access."""

    def __init__(self, corpus_dir: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[3]
        self.corpus_dir = corpus_dir or project_root / "ai_agent_offline_research_corpus_v2/topics"
        self._documents: list[SourceDocument] | None = None

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Return highest-scoring documents for query."""

        if not 1 <= max_results <= 20:
            raise ValueError("max_results must be between 1 and 20")
        query_tokens = self._tokens(query)
        scored = [
            (self._score(document, query_tokens), index, document)
            for index, document in enumerate(self._load_documents())
        ]
        scored.sort(key=lambda item: (-item[0], item[1]))
        ranked = self._deduplicate([document for _, _, document in scored])
        public = [
            document
            for document in ranked
            if document.metadata.get("document_class") == "public_reference_summary"
        ]
        selected = public[: min(4, max_results)]
        selected_ids = {str(document.metadata.get("source_id")) for document in selected}
        selected.extend(
            document
            for document in ranked
            if str(document.metadata.get("source_id")) not in selected_ids
        )
        return [document.model_copy(deep=True) for document in selected[:max_results]]

    def _load_documents(self) -> list[SourceDocument]:
        if self._documents is not None:
            return self._documents
        if not self.corpus_dir.is_dir():
            raise FileNotFoundError(f"Offline corpus directory not found: {self.corpus_dir}")

        documents: list[SourceDocument] = []
        for path in sorted(self.corpus_dir.glob("*.json")):
            raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            metadata = raw.get("benchmark_metadata", {})
            topic = raw.get("topic", {})
            topic_id = str(metadata.get("topic_id", path.stem))
            topic_name = str(topic.get("name", path.stem.replace("_", " ")))
            tags = topic.get("tags", [])
            knowledge = raw.get("knowledge_base", {})

            for item in knowledge.get("source_documents", []):
                source_id = str(item.get("document_id") or item.get("source_id"))
                documents.append(
                    SourceDocument(
                        title=str(item.get("title", source_id)),
                        url=item.get("provenance_url"),
                        snippet=str(item.get("full_text", ""))[:2_400],
                        metadata={
                            "source_id": source_id,
                            "topic_id": topic_id,
                            "topic_name": topic_name,
                            "tags": tags,
                            "document_class": item.get("document_class", "source_document"),
                            "is_synthetic": bool(item.get("is_synthetic", False)),
                        },
                    )
                )

            for item in knowledge.get("knowledge_articles", []):
                article_id = str(item.get("article_id"))
                source_id = f"{topic_id}:{article_id}"
                documents.append(
                    SourceDocument(
                        title=str(item.get("title", source_id)),
                        snippet=str(item.get("content", ""))[:2_400],
                        metadata={
                            "source_id": source_id,
                            "article_id": article_id,
                            "topic_id": topic_id,
                            "topic_name": topic_name,
                            "tags": tags,
                            "document_class": "knowledge_article",
                            "is_synthetic": False,
                        },
                    )
                )

        if not documents:
            raise ValueError(f"No documents found in offline corpus: {self.corpus_dir}")
        self._documents = documents
        return documents

    def _score(self, document: SourceDocument, query_tokens: set[str]) -> int:
        title_tokens = self._tokens(document.title)
        topic_tokens = self._tokens(
            f"{document.metadata.get('topic_name', '')} "
            f"{' '.join(str(tag) for tag in document.metadata.get('tags', []))}"
        )
        body_tokens = self._tokens(document.snippet)
        return (
            6 * len(query_tokens & title_tokens)
            + 4 * len(query_tokens & topic_tokens)
            + len(query_tokens & body_tokens)
        )

    @staticmethod
    def _deduplicate(documents: list[SourceDocument]) -> list[SourceDocument]:
        result: list[SourceDocument] = []
        seen: set[str] = set()
        for document in documents:
            identifier = str(document.metadata.get("source_id", document.title))
            if identifier not in seen:
                seen.add(identifier)
                result.append(document)
        return result

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            token
            for token in _TOKEN_RE.findall(value.lower())
            if len(token) > 1 and token not in _STOP_WORDS
        }
