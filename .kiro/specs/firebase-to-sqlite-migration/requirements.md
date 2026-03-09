# Requirements Document

## Introduction

This document specifies the requirements for migrating the IntelliCredit AI-Powered Corporate Credit Decisioning Platform from Firebase (Firestore, Storage, Authentication) to SQLite3 with local file storage and JWT-based authentication. The migration aims to eliminate cloud dependencies while maintaining all existing functionality and API contracts.

## Glossary

- **System**: The IntelliCredit backend application
- **Firestore**: Firebase's NoSQL cloud document database (being replaced)
- **SQLite3**: A lightweight relational SQL database engine (replacement)
- **Firebase_Storage**: Firebase's cloud file storage service (being replaced)
- **Local_Storage**: Local filesystem-based file storage (replacement)
- **Firebase_Auth**: Firebase's authentication service (being replaced)
- **JWT_Auth**: JSON Web Token-based authentication system (replacement)
- **Repository**: Data access layer classes (ApplicationRepository, DocumentRepository, AnalysisRepository)
- **SQLAlchemy**: Python SQL toolkit and Object-Relational Mapping (ORM) library
- **Migration_Script**: Database schema initialization and version management scripts
- **API_Contract**: The interface specification for API endpoints (request/response formats)
- **Admin_SDK**: Firebase Admin SDK for Python (being removed)

## Requirements

### Requirement 1: Database Migration

**User Story:** As a system administrator, I want to migrate from Firestore to SQLite3, so that the application no longer depends on cloud database services.

#### Acceptance Criteria

1. THE System SHALL use SQLite3 as the primary database for all data storage
2. THE System SHALL use SQLAlchemy ORM for database abstraction and operations
3. THE System SHALL define relational database schemas for applications, documents, analyses, users, audit logs, and monitoring data
4. WHEN the System starts, THE System SHALL initialize the SQLite3 database if it does not exist
5. THE System SHALL implement foreign key relationships between related tables
6. THE System SHALL support database transactions for data consistency
7. THE System SHALL provide migration scripts for schema versioning and updates

### Requirement 2: Repository Layer Refactoring

**User Story:** As a developer, I want all repository classes updated to use SQLite3, so that data access logic works with the new database.

#### Acceptance Criteria

1. THE ApplicationRepository SHALL perform all CRUD operations using SQLAlchemy with SQLite3
2. THE DocumentRepository SHALL perform all CRUD operations using SQLAlchemy with SQLite3
3. THE AnalysisRepository SHALL perform all CRUD operations using SQLAlchemy with SQLite3
4. WHEN a repository method is called, THE System SHALL execute the equivalent SQL operations that match the previous Firestore behavior
5. THE System SHALL maintain the same method signatures in all repository classes
6. THE System SHALL handle database errors and exceptions appropriately
7. THE System SHALL support querying, filtering, and sorting operations equivalent to Firestore queries

### Requirement 3: File Storage Migration

**User Story:** As a system administrator, I want to replace Firebase Storage with local filesystem storage, so that document uploads are stored locally.

#### Acceptance Criteria

1. THE System SHALL store uploaded files in a designated local directory structure
2. WHEN a document is uploaded, THE System SHALL save the file to the local filesystem and store the file path in SQLite3
3. WHEN a document is retrieved, THE System SHALL read the file from the local filesystem using the stored path
4. WHEN a document is deleted, THE System SHALL remove the file from the local filesystem and delete the database record
5. THE System SHALL organize files in a logical directory structure (e.g., by application ID or date)
6. THE System SHALL handle file naming conflicts and generate unique filenames when necessary
7. THE System SHALL validate file paths and prevent directory traversal vulnerabilities

### Requirement 4: Authentication System Replacement

**User Story:** As a developer, I want to replace Firebase Authentication with JWT-based authentication, so that user authentication works without Firebase dependencies.

#### Acceptance Criteria

1. THE System SHALL use JWT tokens for user authentication and authorization
2. THE System SHALL use python-jose library for JWT token generation and validation
3. THE System SHALL use passlib library for password hashing and verification
4. WHEN a user registers, THE System SHALL hash the password using bcrypt and store user credentials in SQLite3
5. WHEN a user logs in with valid credentials, THE System SHALL generate and return a JWT access token
6. WHEN an API endpoint requires authentication, THE System SHALL validate the JWT token from the request header
7. THE System SHALL include user identity information in JWT token claims
8. WHEN a JWT token expires, THE System SHALL reject authentication and return an appropriate error
9. THE System SHALL support token refresh mechanisms for extended sessions

### Requirement 5: API Contract Preservation

**User Story:** As a frontend developer, I want all existing API endpoints to maintain their contracts, so that the frontend application continues to work without modifications.

#### Acceptance Criteria

1. THE System SHALL maintain all existing API endpoint paths and HTTP methods
2. THE System SHALL accept the same request body formats and query parameters as before migration
3. THE System SHALL return the same response body formats and status codes as before migration
4. WHEN an API endpoint is called, THE System SHALL produce functionally equivalent results using SQLite3 backend
5. THE System SHALL maintain the same error response formats and error codes

### Requirement 6: Configuration Management

**User Story:** As a system administrator, I want Firebase dependencies removed from configuration, so that the application uses only SQLite3 and local storage settings.

#### Acceptance Criteria

1. THE System SHALL remove all Firebase configuration parameters from environment variables and config files
2. THE System SHALL add SQLite3 database file path configuration
3. THE System SHALL add local file storage directory path configuration
4. THE System SHALL add JWT secret key and token expiration configuration
5. THE System SHALL validate all required configuration parameters at startup
6. WHEN Firebase Admin SDK imports exist in code, THE System SHALL remove or replace them with SQLite3 equivalents

### Requirement 7: Database Schema Design

**User Story:** As a database administrator, I want a well-designed relational schema, so that data is properly structured and relationships are maintained.

#### Acceptance Criteria

1. THE System SHALL define a users table with columns for user ID, email, hashed password, and metadata
2. THE System SHALL define an applications table with columns for application ID, user ID (foreign key), status, and application data
3. THE System SHALL define a documents table with columns for document ID, application ID (foreign key), file path, and metadata
4. THE System SHALL define an analyses table with columns for analysis ID, application ID (foreign key), analysis results, and timestamps
5. THE System SHALL define an audit_logs table with columns for log ID, user ID, action, timestamp, and details
6. THE System SHALL define a monitoring_data table with columns for metric ID, timestamp, metric name, and metric value
7. THE System SHALL enforce foreign key constraints between related tables
8. THE System SHALL use appropriate data types for each column (INTEGER, TEXT, REAL, BLOB, TIMESTAMP)
9. THE System SHALL define primary keys and indexes for efficient querying

### Requirement 8: Testing Updates

**User Story:** As a developer, I want all tests updated to work with SQLite3, so that the test suite validates the migrated system.

#### Acceptance Criteria

1. THE System SHALL use in-memory SQLite3 databases for unit tests
2. THE System SHALL update all repository tests to work with SQLAlchemy and SQLite3
3. THE System SHALL update all API endpoint tests to work with JWT authentication
4. THE System SHALL update all file storage tests to work with local filesystem storage
5. WHEN tests run, THE System SHALL create and tear down test databases automatically
6. THE System SHALL maintain the same test coverage as before migration

### Requirement 9: Data Migration Utilities

**User Story:** As a system administrator, I want utilities to migrate existing Firebase data to SQLite3, so that historical data is preserved during migration.

#### Acceptance Criteria

1. THE System SHALL provide a migration script that exports data from Firestore
2. THE System SHALL provide a migration script that imports exported data into SQLite3
3. WHEN migrating data, THE System SHALL preserve all data fields and relationships
4. WHEN migrating files, THE System SHALL download files from Firebase Storage and save them to local filesystem
5. THE System SHALL validate data integrity after migration
6. THE System SHALL provide rollback capabilities in case of migration failures
7. THE System SHALL log migration progress and any errors encountered
