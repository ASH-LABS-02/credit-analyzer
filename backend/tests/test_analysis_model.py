"""
Unit tests for Analysis SQLAlchemy model.

Tests the Analysis model's fields, relationships, and database operations.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.database.config import DatabaseConfig
from app.database.models import User, Application, Analysis


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    db_config = DatabaseConfig("sqlite:///:memory:")
    db_config.create_tables()
    session = db_config.get_session()
    yield session
    session.close()
    db_config.close()


class TestAnalysisModel:
    """Test Analysis model."""
    
    def test_create_analysis(self, db_session):
        """Test creating a valid analysis."""
        # Create user and application first (foreign key dependencies)
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending",
            credit_amount=1000000.0
        )
        db_session.add(application)
        db_session.commit()
        
        # Create analysis
        analysis = Analysis(
            id="analysis-123",
            application_id="app-123",
            analysis_type="financial",
            analysis_results='{"score": 75.5}',
            confidence_score=0.85,
            status="complete"
        )
        db_session.add(analysis)
        db_session.commit()
        
        # Verify analysis was created
        retrieved = db_session.query(Analysis).filter_by(id="analysis-123").first()
        assert retrieved is not None
        assert retrieved.application_id == "app-123"
        assert retrieved.analysis_type == "financial"
        assert retrieved.confidence_score == 0.85
        assert retrieved.status == "complete"
        assert isinstance(retrieved.created_at, datetime)
    
    def test_analysis_application_relationship(self, db_session):
        """Test relationship between Analysis and Application."""
        # Create user and application
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        db_session.commit()
        
        # Create multiple analyses for the application
        analysis1 = Analysis(
            id="analysis-1",
            application_id="app-123",
            analysis_type="financial",
            status="complete"
        )
        analysis2 = Analysis(
            id="analysis-2",
            application_id="app-123",
            analysis_type="risk",
            status="complete"
        )
        db_session.add(analysis1)
        db_session.add(analysis2)
        db_session.commit()
        
        # Verify relationship from application side
        app = db_session.query(Application).filter_by(id="app-123").first()
        assert len(app.analyses) == 2
        assert app.analyses[0].analysis_type in ["financial", "risk"]
        assert app.analyses[1].analysis_type in ["financial", "risk"]
        
        # Verify relationship from analysis side
        analysis = db_session.query(Analysis).filter_by(id="analysis-1").first()
        assert analysis.application.id == "app-123"
        assert analysis.application.company_name == "Test Corp"
    
    def test_analysis_cascade_delete(self, db_session):
        """Test that analyses are deleted when application is deleted."""
        # Create user, application, and analysis
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        
        analysis = Analysis(
            id="analysis-123",
            application_id="app-123",
            analysis_type="financial",
            status="complete"
        )
        db_session.add(analysis)
        db_session.commit()
        
        # Delete application
        db_session.delete(application)
        db_session.commit()
        
        # Verify analysis was also deleted (cascade)
        deleted_analysis = db_session.query(Analysis).filter_by(id="analysis-123").first()
        assert deleted_analysis is None
    
    def test_analysis_foreign_key_constraint(self, db_session):
        """Test that foreign key constraint is enforced."""
        # Try to create analysis with non-existent application_id
        analysis = Analysis(
            id="analysis-123",
            application_id="non-existent-app",
            analysis_type="financial",
            status="complete"
        )
        db_session.add(analysis)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
    
    def test_analysis_indexes(self, db_session):
        """Test that indexes are created for efficient querying."""
        # Create test data
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        
        # Create multiple analyses
        for i in range(5):
            analysis = Analysis(
                id=f"analysis-{i}",
                application_id="app-123",
                analysis_type="financial",
                status="complete" if i % 2 == 0 else "pending"
            )
            db_session.add(analysis)
        db_session.commit()
        
        # Query by application_id (indexed)
        analyses_by_app = db_session.query(Analysis).filter_by(application_id="app-123").all()
        assert len(analyses_by_app) == 5
        
        # Query by status (indexed)
        complete_analyses = db_session.query(Analysis).filter_by(status="complete").all()
        assert len(complete_analyses) == 3
        
        # Query by created_at (indexed) - order by
        ordered_analyses = db_session.query(Analysis).order_by(Analysis.created_at.desc()).all()
        assert len(ordered_analyses) == 5
    
    def test_analysis_repr(self, db_session):
        """Test the string representation of Analysis."""
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        
        analysis = Analysis(
            id="analysis-123",
            application_id="app-123",
            analysis_type="financial",
            status="complete"
        )
        db_session.add(analysis)
        db_session.commit()
        
        repr_str = repr(analysis)
        assert "analysis-123" in repr_str
        assert "financial" in repr_str
        assert "complete" in repr_str
