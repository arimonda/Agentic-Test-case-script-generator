"""
RAG (Retrieval Augmented Generation) Knowledge Base Engine.

Ingests user manuals and technical documents into a local vector store
(ChromaDB) so the AI agent can retrieve relevant navigation context
that isn't explicit in the requirement documents.
"""

import logging
from pathlib import Path
from typing import Optional

from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Local RAG engine using ChromaDB for vector storage.

    Ingests documents, chunks them, and provides semantic retrieval
    for the AI agent to augment its prompts with relevant context.
    """

    def __init__(
        self,
        persist_dir: str = "output/vectorstore",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        collection_name: str = "knowledge_base",
    ):
        self.persist_dir = persist_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def _ensure_initialized(self) -> None:
        """Lazy-init ChromaDB client and collection."""
        if self._client is None:
            import chromadb

            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "ChromaDB initialized: %s (%d documents)",
                self.persist_dir,
                self._collection.count(),
            )

    def ingest_document(self, file_path: str) -> int:
        """
        Ingest a .docx or .txt file into the knowledge base.

        Returns the number of chunks created.
        """
        self._ensure_initialized()
        path = Path(file_path)

        if path.suffix.lower() == ".docx":
            text = self._read_docx(path)
        elif path.suffix.lower() in (".txt", ".md"):
            text = path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported format for RAG: {path.suffix}")

        chunks = self._splitter.split_text(text)

        if not chunks:
            logger.warning("No chunks extracted from %s", file_path)
            return 0

        ids = [f"{path.stem}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": str(path), "chunk_index": i} for i in range(len(chunks))]

        self._collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
        )

        logger.info("Ingested %d chunks from %s", len(chunks), file_path)
        return len(chunks)

    def ingest_directory(self, dir_path: str) -> int:
        """Ingest all supported documents in a directory."""
        total = 0
        for ext in ("*.docx", "*.txt", "*.md"):
            for file_path in Path(dir_path).glob(ext):
                total += self.ingest_document(str(file_path))
        return total

    def query(self, question: str, n_results: int = 5) -> list[dict]:
        """
        Retrieve the most relevant chunks for a given question.

        Returns a list of dicts with 'content', 'source', and 'distance'.
        """
        self._ensure_initialized()

        if self._collection.count() == 0:
            logger.warning("Knowledge base is empty — no results to return")
            return []

        results = self._collection.query(
            query_texts=[question],
            n_results=min(n_results, self._collection.count()),
        )

        retrieved = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                retrieved.append({
                    "content": doc,
                    "source": metadata.get("source", "unknown"),
                    "distance": distance,
                })

        logger.info("RAG query returned %d results for: %s", len(retrieved), question[:80])
        return retrieved

    def get_context_for_step(self, intent: str, max_chars: int = 3000) -> str:
        """
        Retrieve and format RAG context relevant to a test step intent.
        Returns a formatted string suitable for inclusion in an AI prompt.
        """
        results = self.query(intent, n_results=3)
        if not results:
            return ""

        context_parts = ["## Relevant Knowledge Base Context"]
        total_chars = 0
        for r in results:
            content = r["content"]
            if total_chars + len(content) > max_chars:
                break
            context_parts.append(f"Source: {r['source']}\n{content}")
            total_chars += len(content)

        return "\n\n".join(context_parts)

    def _read_docx(self, path: Path) -> str:
        """Extract text from a Word document."""
        doc = DocxDocument(str(path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def clear(self) -> None:
        """Clear all documents from the knowledge base."""
        self._ensure_initialized()
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Knowledge base cleared")
