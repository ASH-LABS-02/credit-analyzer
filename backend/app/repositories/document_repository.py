"""
Document Repository for SQLAlchemy operations.

Handles CRUD operations for Document entities using SQLite3 database.
Replaces Firebase Firestore with local database storage.

Requirements: 2.2, 2.4, 2.5, 2.7
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

from app.database.models import Document


class DocumentRepository:
    """Repository for Document entity operations using SQLAlchemy."""
    
    def __init__(self, session: Session):
        """
        Initialize the repository with a SQLAlchemy session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session 
    
    def create(self, document_data: dict) -> Document:
        """
        Create a new document record in the database.
        
        Args:
            document_data: Dictionary containing document fields
            
        Returns:
            Created Document instance
            
        Raises:
            ValueError: If document with same ID already exists or invalid foreign key
            Exception: For other database errors
        """
        try:
            document = Document(**document_data)
            self.session.add(document)
            self.session.commit()
            self.session.refresh(document)
            return document
        except IntegrityError as e:
            self.session.rollback()
            if 'PRIMARY KEY' in str(e) or 'UNIQUE constraint failed: documents.id' in str(e):
                raise ValueError(f"Document with ID {document_data.get('id')} already exists")
            elif 'FOREIGN KEY constraint failed' in str(e):
                raise ValueError(f"Invalid application_id: {document_data.get('application_id')}")
            else:
                raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to create document: {str(e)}")
    
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            Document instance if found, None otherwise
            
        Raises:
            Exception: For database errors
        """
        try:
            return self.session.query(Document).filter(Document.id == document_id).first()
        except Exception as e:
            raise Exception(f"Failed to retrieve document {document_id}: {str(e)}")
    
    def get_by_application_id(self, application_id: str) -> List[Document]:
        """
        Get all documents for a specific application.
        
        Args:
            application_id: Unique application identifier
            
        Returns:
            List of Document instances ordered by upload date (newest first)
            
        Raises:
            Exception: For database errors
        """
        try:
            return self.session.query(Document).filter(
                Document.application_id == application_id
            ).order_by(desc(Document.uploaded_at)).all()
        except Exception as e:
            raise Exception(f"Failed to retrieve documents for application {application_id}: {str(e)}")
    
    def delete(self, document_id: str) -> bool:
        """
        Delete a document record by ID.
        
        Note: This only deletes the database record. The caller is responsible
        for deleting the actual file from the filesystem using FileStorageService.
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            Exception: For database errors
        """
        try:
            document = self.get_by_id(document_id)
            if document is None:
                return False
            
            self.session.delete(document)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to delete document {document_id}: {str(e)}")
