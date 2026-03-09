"""
Application Repository for SQLAlchemy operations.

Handles CRUD operations for Application entities using SQLite3 database.
Replaces Firebase Firestore with local database storage.

Requirements: 2.1, 2.4, 2.5, 2.7
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

from app.database.models import Application


class ApplicationRepository:
    """Repository for Application entity operations using SQLAlchemy."""
    
    def __init__(self, session: Session):
        """
        Initialize the repository with a SQLAlchemy session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, application_data: dict) -> Application:
        """
        Create a new application in the database.
        
        Args:
            application_data: Dictionary containing application fields
            
        Returns:
            Created Application instance
            
        Raises:
            ValueError: If application with same ID already exists
            Exception: For other database errors
        """
        try:
            application = Application(**application_data)
            self.session.add(application)
            self.session.commit()
            self.session.refresh(application)
            return application
        except IntegrityError as e:
            self.session.rollback()
            if 'PRIMARY KEY' in str(e) or 'UNIQUE constraint failed: applications.id' in str(e):
                raise ValueError(f"Application with ID {application_data.get('id')} already exists")
            elif 'FOREIGN KEY constraint failed' in str(e):
                raise ValueError(f"Invalid user_id: {application_data.get('user_id')}")
            else:
                raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to create application: {str(e)}")
    
    def get_by_id(self, application_id: str) -> Optional[Application]:
        """
        Retrieve an application by ID.
        
        Args:
            application_id: Unique application identifier
            
        Returns:
            Application instance if found, None otherwise
            
        Raises:
            Exception: For database errors
        """
        try:
            return self.session.query(Application).filter(Application.id == application_id).first()
        except Exception as e:
            raise Exception(f"Failed to retrieve application {application_id}: {str(e)}")
    
    def get_by_user_id(self, user_id: str) -> List[Application]:
        """
        Get all applications for a specific user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of Application instances
            
        Raises:
            Exception: For database errors
        """
        try:
            return self.session.query(Application).filter(Application.user_id == user_id).order_by(desc(Application.created_at)).all()
        except Exception as e:
            raise Exception(f"Failed to retrieve applications for user {user_id}: {str(e)}")
    
    def update(self, application_id: str, update_data: dict) -> Optional[Application]:
        """
        Update an application with partial data.
        
        Args:
            application_id: Unique application identifier
            update_data: Dictionary of fields to update
            
        Returns:
            Updated Application instance if found, None otherwise
            
        Raises:
            ValueError: If update violates constraints
            Exception: For other database errors
        """
        try:
            application = self.get_by_id(application_id)
            if application is None:
                return None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(application, key):
                    setattr(application, key, value)
            
            # Update timestamp
            application.updated_at = datetime.utcnow()
            
            self.session.commit()
            self.session.refresh(application)
            return application
        except IntegrityError as e:
            self.session.rollback()
            if 'FOREIGN KEY constraint failed' in str(e):
                raise ValueError(f"Invalid foreign key in update data")
            else:
                raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to update application {application_id}: {str(e)}")
    
    def delete(self, application_id: str) -> bool:
        """
        Delete an application by ID.
        
        Args:
            application_id: Unique application identifier
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            Exception: For database errors
        """
        try:
            application = self.get_by_id(application_id)
            if application is None:
                return False
            
            self.session.delete(application)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to delete application {application_id}: {str(e)}")
    
    def list_with_filters(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Application]:
        """
        List applications with optional filters, sorting, and pagination.
        
        Args:
            filters: Dictionary of filters to apply (e.g., {'status': 'pending', 'user_id': '123'})
            limit: Maximum number of applications to return
            offset: Number of applications to skip (for pagination)
            
        Returns:
            List of Application instances
            
        Raises:
            Exception: For database errors
        """
        try:
            query = self.session.query(Application)
            
            # Apply filters if provided
            if filters:
                if 'status' in filters:
                    query = query.filter(Application.status == filters['status'])
                if 'user_id' in filters:
                    query = query.filter(Application.user_id == filters['user_id'])
                if 'company_name' in filters:
                    query = query.filter(Application.company_name.like(f"%{filters['company_name']}%"))
            
            # Order by created_at descending (newest first)
            query = query.order_by(desc(Application.created_at))
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            return query.all()
        except Exception as e:
            raise Exception(f"Failed to list applications: {str(e)}")

