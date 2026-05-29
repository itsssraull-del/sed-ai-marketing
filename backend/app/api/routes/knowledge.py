"""Knowledge base management — upload, search, index, manage documents"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.knowledge import KnowledgeDocument, DocumentType
from app.models.user import User
from app.core.security import get_current_user, require_editor, require_manager
from app.services.vector_store import get_vector_store
from app.services.nas_ingestion import NASIngestionService

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 6
    namespace: Optional[str] = None
    filter_doc_type: Optional[str] = None


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(default=DocumentType.MISC),
    title: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    """Upload a document and queue it for indexing into the knowledge base"""
    content = await file.read()
    doc_id = str(uuid.uuid4())
    doc_title = title or file.filename

    # Create DB record
    doc = KnowledgeDocument(
        id=uuid.UUID(doc_id),
        title=doc_title,
        doc_type=document_type,
        file_size_bytes=len(content),
        mime_type=file.content_type,
        tags=tags.split(",") if tags else [],
        is_indexed=False,
    )
    db.add(doc)
    await db.commit()

    # Queue ingestion as background task
    background_tasks.add_task(
        _ingest_document_background,
        content=content,
        filename=file.filename,
        document_type=document_type.value,
        document_id=doc_id,
    )

    return {
        "document_id": doc_id,
        "title": doc_title,
        "status": "queued_for_indexing",
        "file_size": len(content),
    }


async def _ingest_document_background(content: bytes, filename: str,
                                       document_type: str, document_id: str):
    service = NASIngestionService()
    result = await service.ingest_file(content, filename, document_type, document_id)
    # Update DB
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        r = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == document_id))
        doc = r.scalar_one_or_none()
        if doc:
            doc.is_indexed = result.get("status") == "indexed"
            doc.chunk_count = result.get("chunks", 0)
            doc.s3_key = result.get("s3_key")
            from datetime import datetime, timezone
            doc.last_refreshed = datetime.now(timezone.utc).isoformat()
            await db.commit()


@router.post("/search")
async def search_knowledge_base(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Semantic search over the knowledge base"""
    vector_store = get_vector_store()
    filter_meta = None
    if request.filter_doc_type:
        filter_meta = {"doc_type": {"$eq": request.filter_doc_type}}

    results = await vector_store.search(
        query=request.query,
        namespace=request.namespace or "default",
        top_k=request.top_k,
        filter_metadata=filter_meta,
    )
    return {"query": request.query, "results": results, "count": len(results)}


@router.get("/documents")
async def list_documents(
    doc_type: Optional[DocumentType] = None,
    is_indexed: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = []
    if doc_type:
        filters.append(KnowledgeDocument.doc_type == doc_type)
    if is_indexed is not None:
        filters.append(KnowledgeDocument.is_indexed == is_indexed)

    from sqlalchemy import and_, desc
    result = await db.execute(
        select(KnowledgeDocument)
        .where(and_(*filters) if filters else True)
        .order_by(desc(KnowledgeDocument.created_at))
        .limit(100)
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "doc_type": d.doc_type.value,
            "is_indexed": d.is_indexed,
            "chunk_count": d.chunk_count,
            "file_size_bytes": d.file_size_bytes,
            "tags": d.tags,
            "last_refreshed": d.last_refreshed,
        }
        for d in docs
    ]


@router.delete("/documents/{document_id}", dependencies=[Depends(require_manager)])
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from vector store
    vector_store = get_vector_store()
    await vector_store.delete_document(document_id)

    await db.delete(doc)
    await db.commit()
    return {"message": f"Document {document_id} deleted from knowledge base"}


@router.get("/stats")
async def get_knowledge_stats(current_user: User = Depends(get_current_user)):
    """Get vector store statistics"""
    vector_store = get_vector_store()
    stats = await vector_store.get_stats()
    return stats
