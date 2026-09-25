import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.schemas.ingest import (
    DocumentUploadResponse,
    DocumentMetadata,
    DocumentListResponse,
    DocumentListItem,
    DocumentDeleteResponse,
)
from app.services.document_parser import (
    extract_text_and_metadata,
    split_text_into_chunks,
    calculate_file_hash,
)
from app.services.vector_store import vector_store_service
from app.core.config import settings

router = APIRouter()

SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "md"}


@router.post(
    "/ingest/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Document Ingestion"],
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and ingest a document (PDF, DOCX, TXT, MD) into ChromaDB vector store.
    Prevents duplicate file uploads using SHA-256 content hashing.
    """
    filename = file.filename or "uploaded_file.txt"
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    try:
        content = await file.read()
        if not content or len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # 1. Duplicate check via SHA-256 hash
        file_hash = calculate_file_hash(content)
        existing_doc = vector_store_service.is_duplicate_hash(file_hash)

        if existing_doc:
            doc_id = existing_doc.get("document_id", "existing")
            return DocumentUploadResponse(
                success=True,
                message=f"Document '{filename}' already ingested (Duplicate SHA-256 hash detected).",
                document=DocumentMetadata(
                    document_id=doc_id,
                    filename=existing_doc.get("filename", filename),
                    file_type=existing_doc.get("file_type", ext),
                    file_size_bytes=existing_doc.get("file_size_bytes", len(content)),
                    file_hash=file_hash,
                    chunk_count=existing_doc.get("total_chunks", 1),
                    upload_date=existing_doc.get("upload_date", ""),
                ),
            )

        # 2. Extract text and metadata
        try:
            raw_text, meta = extract_text_and_metadata(filename, content)
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(ve),
            )

        if not raw_text or not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract text content from document.",
            )

        # 3. Split into semantic chunks
        chunks = split_text_into_chunks(
            raw_text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Document contained no chunkable text content.",
            )

        # 4. Generate unique document ID & add to ChromaDB
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        vector_store_service.add_document_chunks(
            document_id=document_id, chunks=chunks, metadata=meta
        )

        doc_meta = DocumentMetadata(
            document_id=document_id,
            filename=meta["filename"],
            file_type=meta["file_type"],
            file_size_bytes=meta["file_size_bytes"],
            file_hash=meta["file_hash"],
            chunk_count=len(chunks),
            upload_date=meta["upload_date"],
        )

        return DocumentUploadResponse(
            success=True,
            message=f"Successfully ingested '{filename}' into vector store ({len(chunks)} chunks created).",
            document=doc_meta,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing document: {str(e)}",
        )



@router.get(
    "/ingest/documents",
    response_model=DocumentListResponse,
    tags=["Document Ingestion"],
)
async def list_documents():
    """
    List all ingested documents and vector storage statistics.
    """
    try:
        docs, total_chunks = vector_store_service.list_documents()
        items = [DocumentListItem(**d) for d in docs]
        return DocumentListResponse(
            total_documents=len(items),
            total_chunks=total_chunks,
            documents=items,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.delete(
    "/ingest/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    tags=["Document Ingestion"],
)
async def delete_document(document_id: str):
    """
    Delete a document and all associated vector chunks from ChromaDB.
    """
    try:
        deleted_chunks = vector_store_service.delete_document(document_id)
        if deleted_chunks == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )

        return DocumentDeleteResponse(
            success=True,
            message=f"Successfully deleted document '{document_id}' and {deleted_chunks} chunks.",
            document_id=document_id,
            deleted_chunks=deleted_chunks,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )
