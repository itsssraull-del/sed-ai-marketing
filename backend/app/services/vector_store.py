"""
SED Energy - Vector Store Service
Pinecone-backed RAG system with semantic search over the full knowledge base.
"""
import logging
import hashlib
import json
from typing import Optional
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings

logger = logging.getLogger("sed-ai.vector-store")

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K_DEFAULT = 6


class VectorStoreService:
    """
    Manages the Pinecone vector database for SED Energy's knowledge base.
    Supports ingestion, semantic search, and namespace management.
    """

    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.dimension = settings.PINECONE_DIMENSION
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._index = None

    def _get_index(self):
        if self._index is None:
            self._ensure_index()
            self._index = self.pc.Index(self.index_name)
        return self._index

    def _ensure_index(self):
        existing = [idx.name for idx in self.pc.list_indexes()]
        if self.index_name not in existing:
            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.PINECONE_ENV),
            )

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding using OpenAI text-embedding-3-small"""
        response = await self.openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text[:8000],  # Token limit safety
        )
        return response.data[0].embedding

    async def ingest_document(
        self,
        document_id: str,
        text: str,
        metadata: dict,
        namespace: str = "default",
    ) -> int:
        """Chunk, embed, and upsert a document into Pinecone"""
        chunks = self.splitter.split_text(text)
        if not chunks:
            logger.warning(f"Document {document_id} produced no chunks")
            return 0

        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = await self.embed_text(chunk)
            vector_id = f"{document_id}_{i}"
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    **metadata,
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_text": chunk[:500],  # Store preview for retrieval
                    "total_chunks": len(chunks),
                },
            })

        # Upsert in batches of 100
        index = self._get_index()
        for batch_start in range(0, len(vectors), 100):
            batch = vectors[batch_start:batch_start + 100]
            index.upsert(vectors=batch, namespace=namespace)

        logger.info(f"Ingested document {document_id}: {len(chunks)} chunks into namespace '{namespace}'")
        return len(chunks)

    async def search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = TOP_K_DEFAULT,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """Semantic search over the knowledge base"""
        query_embedding = await self.embed_text(query)
        index = self._get_index()

        response = index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
            filter=filter_metadata,
        )

        results = []
        for match in response.matches:
            results.append({
                "id": match.id,
                "score": round(match.score, 4),
                "text": match.metadata.get("chunk_text", ""),
                "document_id": match.metadata.get("document_id", ""),
                "document_type": match.metadata.get("doc_type", ""),
                "metadata": match.metadata,
            })

        return results

    async def search_for_content_generation(
        self, topic: str, platform: str, product_refs: list = None
    ) -> str:
        """
        Specialised search for content generation context.
        Returns formatted context string for injection into AI prompts.
        """
        queries = [
            topic,
            f"SED Energy {topic}",
            f"solar {topic} South Africa",
        ]
        if product_refs:
            queries.extend([f"{ref} specifications" for ref in product_refs[:2]])

        all_results = []
        for query in queries[:3]:
            results = await self.search(query, top_k=3)
            all_results.extend(results)

        # Deduplicate by document_id and sort by score
        seen_docs = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x["score"], reverse=True):
            if r["document_id"] not in seen_docs:
                seen_docs.add(r["document_id"])
                unique_results.append(r)
                if len(unique_results) >= TOP_K_DEFAULT:
                    break

        if not unique_results:
            return ""

        context_parts = []
        for r in unique_results:
            if r["score"] >= 0.70:
                context_parts.append(
                    f"[Source: {r.get('document_type', 'knowledge_base')} | Relevance: {r['score']}]\n{r['text']}"
                )

        return "\n\n---\n\n".join(context_parts)

    async def delete_document(self, document_id: str, namespace: str = "default"):
        """Remove all chunks for a document"""
        index = self._get_index()
        # Pinecone supports prefix-based deletion in paid tiers
        # For serverless, we query and delete by IDs
        response = index.query(
            vector=[0.0] * self.dimension,
            top_k=1000,
            namespace=namespace,
            filter={"document_id": {"$eq": document_id}},
        )
        ids_to_delete = [m.id for m in response.matches]
        if ids_to_delete:
            index.delete(ids=ids_to_delete, namespace=namespace)
            logger.info(f"Deleted {len(ids_to_delete)} chunks for document {document_id}")

    async def get_stats(self) -> dict:
        """Get index statistics"""
        index = self._get_index()
        stats = index.describe_index_stats()
        return {
            "total_vectors": stats.total_vector_count,
            "namespaces": {k: v.vector_count for k, v in stats.namespaces.items()},
            "dimension": stats.dimension,
        }


# Singleton
_vector_store: Optional[VectorStoreService] = None

def get_vector_store() -> VectorStoreService:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
