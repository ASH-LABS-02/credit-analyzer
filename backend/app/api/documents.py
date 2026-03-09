"""
Document Operation API Endpoints

This module implements RESTful endpoints for managing documents:
- POST /api/v1/applications/{app_id}/documents - Upload document
- GET /api/v1/applications/{app_id}/documents - List documents
- GET /api/v1/documents/{doc_id} - Get document
- DELETE /api/v1/documents/{doc_id} - Delete document

Requirements: 1.1, 1.4, 14.1
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uuid

from app.database.config import get_db
from app.database.models import Document
from app.repositories.document_repository import DocumentRepository
from app.repositories.application_repository import ApplicationRepository
from app.services.file_storage_service import FileStorageService
from app.core.config import settings


# Response Models
class DocumentResponse(BaseModel):
    """Response model for document data."""
    id: str
    application_id: str
    filename: str
    content_type: str
    document_type: Optional[str] = None
    uploaded_at: datetime
    file_path: str
    file_size: int
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[DocumentResponse]
    total: int
    application_id: str


# Initialize router
router = APIRouter(
    prefix="/api/v1",
    tags=["documents"]
)

# Initialize file storage service
_file_storage = None


def get_file_storage() -> FileStorageService:
    """Get or initialize file storage service."""
    global _file_storage
    if _file_storage is None:
        _file_storage = FileStorageService(settings.FILE_STORAGE_ROOT)
    return _file_storage


def document_to_response(doc: Document) -> DocumentResponse:
    """
    Convert Document database model to DocumentResponse.
    
    Args:
        doc: Document database model
        
    Returns:
        DocumentResponse model
    """
    return DocumentResponse(
        id=doc.id,
        application_id=doc.application_id,
        filename=doc.filename,
        content_type=doc.content_type or '',
        document_type=doc.document_type,
        uploaded_at=doc.uploaded_at,
        file_path=doc.file_path,
        file_size=doc.file_size or 0
    )


@router.post(
    "/applications/{app_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document",
    description="""
    Upload a document for a credit application.
    
    Accepts PDF, DOCX, Excel, CSV, and image formats (JPG, PNG, TIFF).
    Maximum file size: 50MB.
    
    The document is stored in local filesystem and metadata is saved to database.
    
    **Requirements**: 1.1, 1.2, 1.3, 1.4, 1.5, 14.1
    """
)
def upload_document(
    app_id: str,
    file: UploadFile = File(..., description="Document file to upload"),
    document_type: str = Form(..., description="Type of document (e.g., financial_statement, bank_statement)"),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Upload a document for an application.
    """
    try:
        # Verify application exists
        app_repo = ApplicationRepository(db)
        application = app_repo.get_by_id(app_id)
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Read file data
        file_data = file.file.read()
        file_size = len(file_data)
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        
        # Extract file extension and determine content type
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        content_type = file.content_type or f'application/{file_extension}'
        
        # Save file to storage
        file_storage = get_file_storage()
        file_path = file_storage.save_file(file_data, app_id, file.filename)
        
        # Create document record
        document_data = {
            "id": doc_id,
            "application_id": app_id,
            "filename": file.filename,
            "content_type": content_type,
            "document_type": document_type,
            "file_size": file_size,
            "file_path": file_path,
            "uploaded_at": datetime.utcnow()
        }
        
        # Save to repository
        doc_repo = DocumentRepository(db)
        created_doc = doc_repo.create(document_data)
        
        return document_to_response(created_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get(
    "/applications/{app_id}/documents",
    response_model=DocumentListResponse,
    summary="List documents",
    description="""
    List all documents for a specific application.
    
    Documents are returned in descending order by upload date (newest first).
    
    **Requirements**: 1.4, 14.1
    """
)
def list_documents(
    app_id: str,
    db: Session = Depends(get_db)
) -> DocumentListResponse:
    """
    List all documents for an application.
    """
    try:
        # Verify application exists
        app_repo = ApplicationRepository(db)
        application = app_repo.get_by_id(app_id)
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Get documents for application
        doc_repo = DocumentRepository(db)
        documents = doc_repo.get_by_application_id(app_id)
        
        # Convert to response models
        doc_responses = [document_to_response(doc) for doc in documents]
        
        return DocumentListResponse(
            documents=doc_responses,
            total=len(doc_responses),
            application_id=app_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get(
    "/documents/{doc_id}",
    response_model=DocumentResponse,
    summary="Get document",
    description="""
    Retrieve detailed information about a specific document.
    
    Returns document metadata. Use a separate endpoint to download the actual file content.
    
    **Requirements**: 1.4, 14.1
    """
)
def get_document(
    doc_id: str,
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Get document details by ID.
    """
    try:
        # Get document from repository
        doc_repo = DocumentRepository(db)
        document = doc_repo.get_by_id(doc_id)
        
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        return document_to_response(document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.get(
    "/documents/{doc_id}/download",
    summary="Download document",
    description="""
    Download the actual file content for a document.
    
    Returns the file as a binary stream with appropriate content type.
    
    **Requirements**: 1.4, 14.1
    """
)
def download_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Download document file by ID.
    """
    try:
        from fastapi.responses import Response
        
        # Get document metadata
        doc_repo = DocumentRepository(db)
        document = doc_repo.get_by_id(doc_id)
        
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        # Read file from storage
        file_storage = get_file_storage()
        try:
            file_content = file_storage.read_file(document.file_path)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document file not found on disk"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read document file: {str(e)}"
            )
        
        # Return file with appropriate headers
        return Response(
            content=file_content,
            media_type=document.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'inline; filename="{document.filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download document: {str(e)}"
        )


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="""
    Delete a document by ID from both database and filesystem.
    
    **Requirements**: 1.4, 14.1
    """
)
def delete_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document by ID.
    """
    try:
        # Get document metadata first
        doc_repo = DocumentRepository(db)
        document = doc_repo.get_by_id(doc_id)
        
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        # Delete file from storage
        file_storage = get_file_storage()
        try:
            file_storage.delete_file(document.file_path)
        except Exception as e:
            # Log but don't fail if file deletion fails
            pass
        
        # Delete from database
        deleted = doc_repo.delete(doc_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
