"""
SQLAlchemy ORM models for SQLite3 database.

These models define the database schema and relationships for the IntelliCredit platform.
They are separate from the Pydantic domain models in app/models/domain.py which are used
for API validation and serialization.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Float, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.database.config import Base


class User(Base):
    """
    User model for authentication and authorization.
    
    Stores user credentials and metadata. Passwords are stored as bcrypt hashes.
    Related to applications and audit logs (relationships will be added when those models are created).
    """
    __tablename__ = 'users'
    
    # Primary key
    id = Column(String, primary_key=True)
    
    # Authentication fields
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    
    # User metadata
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = relationship("Application", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Application(Base):
    """
    Application model for credit applications.
    
    Stores credit application data including company information, status, and application details.
    Related to users (owner), documents, and analyses.
    """
    __tablename__ = 'applications'
    
    # Primary key
    id = Column(String, primary_key=True)
    
    # Foreign key to users table
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    
    # Application fields
    company_name = Column(String, nullable=False)
    loan_amount = Column(Float, nullable=False)
    loan_purpose = Column(String, nullable=False)
    applicant_email = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    credit_score = Column(Float, nullable=True)
    recommendation = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="application", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Application(id={self.id}, company_name={self.company_name}, status={self.status})>"


class Document(Base):
    """
    Document model for uploaded files.
    
    Stores metadata about documents uploaded for credit applications.
    The actual file content is stored in the local filesystem, and this model
    stores the file path and metadata.
    """
    __tablename__ = 'documents'
    
    # Primary key
    id = Column(String, primary_key=True)
    
    # Foreign key to applications table
    application_id = Column(String, ForeignKey('applications.id'), nullable=False, index=True)
    
    # File metadata
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    content_type = Column(String)
    document_type = Column(String, index=True)
    
    # Timestamp
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, document_type={self.document_type})>"


class Analysis(Base):
    """
    Analysis model for financial analysis results.
    
    Stores the results of financial analyses performed on credit applications.
    Each analysis is associated with a specific application and contains
    analysis results, confidence scores, and status information.
    """
    __tablename__ = 'analyses'
    
    # Primary key
    id = Column(String, primary_key=True)
    
    # Foreign key to applications table
    application_id = Column(String, ForeignKey('applications.id'), nullable=False, index=True)
    
    # Analysis fields
    analysis_type = Column(String, nullable=False)
    analysis_results = Column(Text)  # JSON string for analysis results
    confidence_score = Column(Float)
    status = Column(String, index=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    application = relationship("Application", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, analysis_type={self.analysis_type}, status={self.status})>"


class AuditLog(Base):
    """
    AuditLog model for tracking user actions and system events.
    
    Stores audit trail information including user actions, resource changes,
    and timestamps. Used for compliance, security monitoring, and debugging.
    """
    __tablename__ = 'audit_logs'
    
    # Primary key (auto-incrementing integer)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to users table (nullable - some actions may not have a user)
    user_id = Column(String, ForeignKey('users.id', ondelete='SET NULL'), index=True)
    
    # Action details
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String)
    resource_id = Column(String)
    details = Column(Text)  # JSON string for additional details
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id}, timestamp={self.timestamp})>"


class MonitoringData(Base):
    """
    MonitoringData model for system metrics and monitoring.
    
    Stores time-series monitoring data including metrics, values, and metadata.
    Used for tracking system performance, usage statistics, and operational metrics.
    """
    __tablename__ = 'monitoring_data'
    
    # Primary key (auto-incrementing integer)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Metric fields
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String)
    tags = Column(Text)  # JSON string for additional tags/metadata
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<MonitoringData(id={self.id}, metric_name={self.metric_name}, metric_value={self.metric_value}, timestamp={self.timestamp})>"


class ErrorLog(Base):
    """
    ErrorLog model for centralized error logging.
    
    Stores structured error information including stack traces, context data,
    and severity levels for debugging and monitoring purposes.
    """
    __tablename__ = 'error_logs'
    
    # Primary key
    id = Column(String, primary_key=True)  # UUID
    
    # Error information
    error_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    severity = Column(String, nullable=False, index=True)  # debug, info, warning, error, critical
    
    # Context and associations
    context = Column(Text)  # JSON string for additional context
    user_id = Column(String, index=True)
    application_id = Column(String, index=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, error_type={self.error_type}, severity={self.severity}, timestamp={self.timestamp})>"
