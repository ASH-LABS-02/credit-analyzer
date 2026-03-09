"""
User Repository for SQLAlchemy operations.

Handles CRUD operations for User entities using SQLite3 database.
Replaces Firebase Authentication with local database storage.

Requirements: 2.1, 2.4, 2.5, 2.7
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.models import User


class UserRepository:
    """Repository for User entity operations using SQLAlchemy."""
    
    def __init__(self, session: Session):
        """
        Initialize the repository with a SQLAlchemy session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, user_data: dict) -> User:
        """
        Create a new user in the database.
        
        Args:
            user_data: Dictionary containing user fields (id, email, hashed_password, etc.)
            
        Returns:
            Created User instance
            
        Raises:
            ValueError: If user with same ID or email already exists
            Exception: For other database errors
        """
        try:
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
        except IntegrityError as e:
            self.session.rollback()
            if 'UNIQUE constraint failed: users.email' in str(e):
                raise ValueError(f"User with email {user_data.get('email')} already exists")
            elif 'UNIQUE constraint failed: users.id' in str(e) or 'PRIMARY KEY' in str(e):
                raise ValueError(f"User with ID {user_data.get('id')} already exists")
            else:
                raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to create user: {str(e)}")
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User instance if found, None otherwise
            
        Raises:
            Exception: For database errors
        """
        try:
            return self.session.query(User).filter(User.id == user_id).first()
        except Exception as e:
            raise Exception(f"Failed to retrieve user {user_id}: {str(e)}")
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User instance if found, None otherwise
            
        Raises:
            Exception: For database errors
        """
        try:
            return self.session.query(User).filter(User.email == email).first()
        except Exception as e:
            raise Exception(f"Failed to retrieve user by email {email}: {str(e)}")
    
    def update(self, user_id: str, update_data: dict) -> Optional[User]:
        """
        Update a user with partial data.
        
        Args:
            user_id: Unique user identifier
            update_data: Dictionary of fields to update
            
        Returns:
            Updated User instance if found, None otherwise
            
        Raises:
            ValueError: If email update violates uniqueness constraint
            Exception: For other database errors
        """
        try:
            user = self.get_by_id(user_id)
            if user is None:
                return None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            self.session.commit()
            self.session.refresh(user)
            return user
        except IntegrityError as e:
            self.session.rollback()
            if 'UNIQUE constraint failed: users.email' in str(e):
                raise ValueError(f"User with email {update_data.get('email')} already exists")
            else:
                raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to update user {user_id}: {str(e)}")
