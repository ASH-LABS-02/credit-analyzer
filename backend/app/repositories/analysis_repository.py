"""
Analysis Repository for SQLAlchemy operations.

Handles CRUD operations for Analysis entities using SQLite3 database.
Replaces Firebase Firestore with local database storage.

Requirements: 2.3, 2.4, 2.5, 2.7
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.models import Analysis


class AnalysisRepository:
    """Repository for Analysis entity operations using SQLAlchemy."""
    
    def __init__(self, session: Session):
        """
        Initialize the repository with a SQLAlchemy session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, analysis_data: dict) -> Analysis:
        """
        Create a new analysis in the database.
        
        Args:
            analysis_data: Dictionary containing analysis fields
            
        Returns:
            Created Analysis instance
            
        Raises:
            ValueError: If analysis with same ID already exists or invalid foreign key
            Exception: For other database errors
        """
        try:
            analysis = Analysis(**analysis_data)
            self.session.add(analysis)
            self.session.commit()
            self.session.refresh(analysis)
            return analysis
        except IntegrityError as e:
            self.session.rollback()
            if 'PRIMARY KEY' in str(e) or 'UNIQUE constraint failed: analyses.id' in str(e):
                raise ValueError(f"Analysis with ID {analysis_data.get('id')} already exists")
            elif 'FOREIGN KEY constraint failed' in str(e):
                raise ValueError(f"Invalid application_id: {analysis_data.get('application_id')}")
            else:
                raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to create analysis: {str(e)}")
    
    def get_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """
        Retrieve an analysis by ID.
        
        Args:
            analysis_id: Unique analysis identifier
            
        Returns:
            Analysis instance if found, None otherwise
            
        Raises:
            Exception: For database errors
        """
        try:
            return self.session.query(Analysis).filter(Analysis.id == analysis_id).first()
        except Exception as e:
            raise Exception(f"Failed to retrieve analysis {analysis_id}: {str(e)}")
    
    def get_by_application_id(self, application_id: str) -> List[Analysis]:
        """
        Get all analyses for a specific application.
        
        Args:
            application_id: Unique application identifier
            
        Returns:
            List of Analysis instances
            
        Raises:
            Exception: For database errors
        """
        try:
            return self.session.query(Analysis).filter(
                Analysis.application_id == application_id
            ).order_by(Analysis.created_at.desc()).all()
        except Exception as e:
            raise Exception(f"Failed to retrieve analyses for application {application_id}: {str(e)}")
    
    def update(self, analysis_id: str, update_data: dict) -> Optional[Analysis]:
        """
        Update an analysis with partial data.
        
        Args:
            analysis_id: Unique analysis identifier
            update_data: Dictionary of fields to update
            
        Returns:
            Updated Analysis instance if found, None otherwise
            
        Raises:
            ValueError: If update violates constraints
            Exception: For other database errors
        """
        try:
            analysis = self.get_by_id(analysis_id)
            if analysis is None:
                return None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(analysis, key):
                    setattr(analysis, key, value)
            
            self.session.commit()
            self.session.refresh(analysis)
            return analysis
        except IntegrityError as e:
            self.session.rollback()
            if 'FOREIGN KEY constraint failed' in str(e):
                raise ValueError(f"Invalid foreign key in update data")
            else:
                raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to update analysis {analysis_id}: {str(e)}")
