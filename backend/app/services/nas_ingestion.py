"""
SED Energy - NAS Ingestion Service
Ingests documents from the company NAS (SMB share) and S3, processes them into the vector store.
Supports PDF, DOCX, XLSX, images, and text files.
"""
import logging
import hashlib
import io
import os
from typing import Optional, AsyncGenerator
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("sed-ai.nas-ingestion")

try:
    import fitz  # PyMuPDF for PDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import openpyxl
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".txt": "text",
    ".md": "text",
    ".csv": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
}

NAMESPACE_MAP = {
    "product_catalogue": "products",
    "price_list": "pricing",
    "datasheet": "products",
    "brand_guidelines": "branding",
    "sop": "operations",
    "sales_script": "sales",
    "supplier_doc": "suppliers",
    "marketing_asset": "marketing",
    "whatsapp_export": "communication",
    "social_export": "communication",
    "industry_news": "industry",
    "company_info": "company",
}


class NASIngestionService:
    """
    Ingests and processes company documents into the vector knowledge base.
    """

    def __init__(self):
        from app.config import settings
        from app.services.vector_store import get_vector_store
        self.settings = settings
        self.vector_store = get_vector_store()
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )

    def _compute_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def extract_text_from_pdf(self, content: bytes) -> str:
        if not PDF_AVAILABLE:
            return ""
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()

    def extract_text_from_docx(self, content: bytes) -> str:
        if not DOCX_AVAILABLE:
            return ""
        doc = DocxDocument(io.BytesIO(content))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    def extract_text_from_xlsx(self, content: bytes) -> str:
        if not XLSX_AVAILABLE:
            return ""
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        rows = []
        for sheet in wb.sheetnames[:5]:  # First 5 sheets
            ws = wb[sheet]
            for row in ws.iter_rows(values_only=True):
                row_text = " | ".join(str(v) for v in row if v is not None)
                if row_text.strip():
                    rows.append(row_text)
        return "\n".join(rows)

    def extract_text(self, content: bytes, file_type: str, filename: str = "") -> str:
        try:
            if file_type == "pdf":
                return self.extract_text_from_pdf(content)
            elif file_type == "docx":
                return self.extract_text_from_docx(content)
            elif file_type == "xlsx":
                return self.extract_text_from_xlsx(content)
            elif file_type == "text":
                return content.decode("utf-8", errors="replace")
            elif file_type == "image":
                return f"[Image file: {filename}]"  # Images handled by vision model separately
            return ""
        except Exception as e:
            logger.error(f"Text extraction error for {filename}: {e}")
            return ""

    async def ingest_file(
        self,
        content: bytes,
        filename: str,
        document_type: str,
        document_id: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Process a single file and ingest into vector store"""
        ext = Path(filename).suffix.lower()
        file_type = SUPPORTED_EXTENSIONS.get(ext, "text")
        namespace = NAMESPACE_MAP.get(document_type, "default")

        # Extract text
        text = self.extract_text(content, file_type, filename)
        if not text or len(text.strip()) < 50:
            logger.warning(f"File {filename} produced insufficient text ({len(text)} chars)")
            return {"document_id": document_id, "chunks": 0, "status": "skipped"}

        # Upload raw file to S3
        s3_key = f"knowledge-base/{document_type}/{document_id}/{filename}"
        try:
            self.s3.put_object(
                Bucket=self.settings.S3_BUCKET_NAME,
                Key=s3_key,
                Body=content,
            )
        except Exception as e:
            logger.warning(f"S3 upload failed for {filename}: {e}")
            s3_key = None

        # Ingest into vector store
        doc_metadata = {
            "filename": filename,
            "doc_type": document_type,
            "file_type": file_type,
            "s3_key": s3_key or "",
            "file_size": len(content),
            **(metadata or {}),
        }

        chunk_count = await self.vector_store.ingest_document(
            document_id=document_id,
            text=text,
            metadata=doc_metadata,
            namespace=namespace,
        )

        return {
            "document_id": document_id,
            "filename": filename,
            "document_type": document_type,
            "namespace": namespace,
            "chunks": chunk_count,
            "text_length": len(text),
            "s3_key": s3_key,
            "status": "indexed",
        }

    async def scan_s3_bucket(self, prefix: str = "uploads/") -> AsyncGenerator[dict, None]:
        """Scan S3 bucket for unindexed documents"""
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.settings.S3_BUCKET_NAME, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                ext = Path(key).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    yield {
                        "key": key,
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                        "file_type": SUPPORTED_EXTENSIONS[ext],
                    }

    async def ingest_from_s3(self, s3_key: str, document_type: str, document_id: str) -> dict:
        """Download from S3 and ingest"""
        try:
            obj = self.s3.get_object(Bucket=self.settings.S3_BUCKET_NAME, Key=s3_key)
            content = obj["Body"].read()
            filename = Path(s3_key).name
            return await self.ingest_file(content, filename, document_type, document_id)
        except ClientError as e:
            logger.error(f"S3 download error for {s3_key}: {e}")
            return {"document_id": document_id, "status": "error", "error": str(e)}
