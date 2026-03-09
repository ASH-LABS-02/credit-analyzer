"""
Integration tests for database infrastructure.

This test file verifies that the database infrastructure works end-to-end.
"""

import pytest
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.database.config import DatabaseConfig, Base


class User(Base):
    """Test user model."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")


class Post(Base):
    """Test post model with foreign key to user."""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    user = relationship("User", back_populates="posts")


@pytest.fixture
def db_with_models():
    """Create database with test models."""
    db_config = DatabaseConfig("sqlite:///:memory:")
    db_config.create_tables()
    yield db_config
    db_config.close()


def test_complete_crud_workflow(db_with_models):
    """Test complete CRUD workflow with relationships."""
    session = db_with_models.get_session()
    
    try:
        # Create
        user = User(id=1, email="test@example.com", name="Test User")
        session.add(user)
        session.commit()
        
        # Read
        retrieved_user = session.query(User).filter_by(email="test@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.name == "Test User"
        
        # Create related post
        post = Post(id=1, title="Test Post", user_id=user.id)
        session.add(post)
        session.commit()
        
        # Verify relationship
        user_with_posts = session.query(User).filter_by(id=1).first()
        assert len(user_with_posts.posts) == 1
        assert user_with_posts.posts[0].title == "Test Post"
        
        # Update
        user_with_posts.name = "Updated User"
        session.commit()
        
        updated_user = session.query(User).filter_by(id=1).first()
        assert updated_user.name == "Updated User"
        
        # Delete
        session.delete(user_with_posts)
        session.commit()
        
        deleted_user = session.query(User).filter_by(id=1).first()
        assert deleted_user is None
        
        # Verify cascade delete
        deleted_post = session.query(Post).filter_by(id=1).first()
        assert deleted_post is None
        
    finally:
        session.close()


def test_transaction_rollback(db_with_models):
    """Test that transactions can be rolled back."""
    session = db_with_models.get_session()
    
    try:
        # Add a user
        user = User(id=1, email="test@example.com", name="Test User")
        session.add(user)
        session.commit()
        
        # Start a new transaction that will be rolled back
        user.name = "Should Not Persist"
        session.rollback()
        
        # Verify rollback worked
        session.refresh(user)
        assert user.name == "Test User"
        
    finally:
        session.close()


def test_unique_constraint_enforcement(db_with_models):
    """Test that unique constraints are enforced."""
    from sqlalchemy.exc import IntegrityError
    
    session = db_with_models.get_session()
    
    try:
        # Add first user
        user1 = User(id=1, email="test@example.com", name="User 1")
        session.add(user1)
        session.commit()
        
        # Try to add second user with same email
        user2 = User(id=2, email="test@example.com", name="User 2")
        session.add(user2)
        
        with pytest.raises(IntegrityError):
            session.commit()
        
        session.rollback()
        
    finally:
        session.close()
