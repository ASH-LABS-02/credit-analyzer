# Implementation Plan: Firebase to SQLite3 Migration

## Overview

This implementation plan breaks down the migration from Firebase to SQLite3 into discrete, incremental steps. Each task builds on previous work, with testing integrated throughout to catch issues early. The approach prioritizes core functionality first, then adds comprehensive testing and migration utilities.

## Tasks

- [x] 1. Set up SQLite3 database infrastructure
  - Install required dependencies (sqlalchemy, python-jose, passlib, hypothesis)
  - Remove firebase-admin from dependencies
  - Create database configuration module with connection management
  - Define Base model class for SQLAlchemy
  - Implement database initialization function
  - _Requirements: 1.1, 1.2, 1.4, 6.1, 6.2_

- [x] 1.1 Write property test for database initialization
  - **Property: Database initialization creates tables**
  - **Validates: Requirements 1.4**

- [ ] 2. Define SQLAlchemy data models
  - [x] 2.1 Create User model with all fields and relationships
    - Define users table schema
    - Add email index and constraints
    - _Requirements: 7.1_
  
  - [x] 2.2 Create Application model with all fields and relationships
    - Define applications table schema
    - Add foreign key to users table
    - Add indexes for user_id, status, created_at
    - _Requirements: 7.2_
  
  - [x] 2.3 Create Document model with all fields and relationships
    - Define documents table schema
    - Add foreign key to applications table
    - Add indexes for application_id, document_type
    - _Requirements: 7.3_
  
  - [x] 2.4 Create Analysis model with all fields and relationships
    - Define analyses table schema
    - Add foreign key to applications table
    - Add indexes for application_id, status, created_at
    - _Requirements: 7.4_
  
  - [x] 2.5 Create AuditLog model with all fields and relationships
    - Define audit_logs table schema
    - Add foreign key to users table
    - Add indexes for user_id, action, timestamp
    - _Requirements: 7.5_
  
  - [x] 2.6 Create MonitoringData model with all fields
    - Define monitoring_data table schema
    - Add indexes for metric_name, timestamp
    - _Requirements: 7.6_

- [ ] 2.7 Write property test for foreign key constraints
  - **Property 11: Foreign Key Integrity**
  - **Validates: Requirements 7.7**

- [ ] 3. Implement file storage service
  - [x] 3.1 Create FileStorageService class with local filesystem operations
    - Implement save_file method with unique filename generation
    - Implement read_file method with path validation
    - Implement delete_file method
    - Implement path sanitization and security checks
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 3.2 Write property test for document storage round-trip
  - **Property 2: Document Storage Round-Trip**
  - **Validates: Requirements 3.2, 3.3**

- [ ] 3.3 Write property test for filename uniqueness
  - **Property 4: Filename Uniqueness**
  - **Validates: Requirements 3.6**

- [ ] 3.4 Write property test for path traversal prevention
  - **Property 5: Path Traversal Prevention**
  - **Validates: Requirements 3.7**

- [ ] 3.5 Write unit tests for file deletion
  - Test document deletion removes both file and database record
  - _Requirements: 3.4_

- [ ] 4. Implement JWT authentication service
  - [x] 4.1 Create AuthService class with JWT and password handling
    - Implement password hashing with bcrypt
    - Implement password verification
    - Implement JWT token creation with expiration
    - Implement JWT token decoding and validation
    - Implement user authentication method
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [ ] 4.2 Write property test for password hashing security
  - **Property 6: Password Hashing Security**
  - **Validates: Requirements 4.4**

- [ ] 4.3 Write property test for authentication token round-trip
  - **Property 7: Authentication Token Round-Trip**
  - **Validates: Requirements 4.5, 4.7**

- [ ] 4.4 Write unit tests for token expiration
  - Test expired tokens are rejected
  - _Requirements: 4.8_

- [ ] 5. Checkpoint - Ensure core infrastructure tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Refactor repository layer to use SQLAlchemy
  - [x] 6.1 Implement UserRepository with SQLAlchemy
    - Implement create, get_by_id, get_by_email, update methods
    - Replace Firebase calls with SQLAlchemy queries
    - _Requirements: 2.1, 2.4, 2.5, 2.7_
  
  - [x] 6.2 Implement ApplicationRepository with SQLAlchemy
    - Implement create, get_by_id, get_by_user_id, update, delete methods
    - Implement list_with_filters for querying with filters and sorting
    - Replace Firebase calls with SQLAlchemy queries
    - _Requirements: 2.1, 2.4, 2.5, 2.7_
  
  - [x] 6.3 Implement DocumentRepository with SQLAlchemy
    - Implement create, get_by_id, get_by_application_id, delete methods
    - Replace Firebase calls with SQLAlchemy queries
    - _Requirements: 2.2, 2.4, 2.5, 2.7_
  
  - [x] 6.4 Implement AnalysisRepository with SQLAlchemy
    - Implement create, get_by_id, get_by_application_id, update methods
    - Replace Firebase calls with SQLAlchemy queries
    - _Requirements: 2.3, 2.4, 2.5, 2.7_

- [ ] 6.5 Write property test for repository operation equivalence
  - **Property 1: Repository Operation Equivalence**
  - **Validates: Requirements 2.4, 2.7**

- [ ] 6.6 Write unit tests for repository CRUD operations
  - Test create, read, update, delete for each repository
  - Test query filtering and sorting
  - _Requirements: 2.4, 2.7_

- [ ] 7. Update API endpoints to use new authentication
  - [x] 7.1 Create authentication middleware and dependencies
    - Implement get_current_user dependency for FastAPI
    - Implement OAuth2 password bearer scheme
    - Update all protected endpoints to use get_current_user
    - _Requirements: 4.6_
  
  - [ ] 7.2 Create user registration endpoint
    - Implement POST /auth/register endpoint
    - Hash passwords before storing
    - _Requirements: 4.4_
  
  - [ ] 7.3 Create user login endpoint
    - Implement POST /auth/login endpoint
    - Validate credentials and return JWT token
    - _Requirements: 4.5_

- [ ] 7.4 Write property test for protected endpoint authentication
  - **Property 8: Protected Endpoint Authentication**
  - **Validates: Requirements 4.6**

- [ ] 7.5 Write unit tests for authentication endpoints
  - Test registration with valid/invalid data
  - Test login with valid/invalid credentials
  - Test protected endpoints with/without tokens
  - _Requirements: 4.4, 4.5, 4.6_

- [ ] 8. Update API endpoints to use SQLite3 repositories
  - [x] 8.1 Update application endpoints
    - Update POST /applications to use ApplicationRepository
    - Update GET /applications/{id} to use ApplicationRepository
    - Update GET /applications to use ApplicationRepository with filters
    - Update PUT /applications/{id} to use ApplicationRepository
    - Update DELETE /applications/{id} to use ApplicationRepository
    - Maintain same request/response formats
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 8.2 Update document endpoints
    - Update POST /applications/{app_id}/documents to use DocumentRepository and FileStorageService
    - Update GET /applications/{app_id}/documents to use DocumentRepository
    - Update GET /documents/{id} to use DocumentRepository
    - Update DELETE /documents/{id} to use DocumentRepository and FileStorageService
    - Converted all endpoints from async to sync with database session injection
    - Integrated FileStorageService for local filesystem storage
    - Maintain same request/response formats
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 8.3 Update analysis endpoints
    - Update POST /analyses to use AnalysisRepository
    - Update GET /analyses/{id} to use AnalysisRepository
    - Update GET /applications/{id}/analyses to use AnalysisRepository
    - Maintain same request/response formats
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 8.4 Write property test for API request compatibility
  - **Property 9: API Request Compatibility**
  - **Validates: Requirements 5.2, 5.3, 5.4**

- [ ] 8.5 Write property test for API error response compatibility
  - **Property 10: API Error Response Compatibility**
  - **Validates: Requirements 5.5**

- [ ] 8.6 Write integration tests for all API endpoints
  - Test complete workflows: create application, upload documents, run analysis
  - Test error scenarios and edge cases
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 9. Checkpoint - Ensure all API tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Update configuration and environment
  - [x] 10.1 Update configuration files
    - Remove Firebase configuration parameters
    - Add SQLite3 database URL configuration
    - Add file storage root directory configuration
    - Add JWT secret key and expiration configuration
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 10.2 Add configuration validation at startup
    - Validate all required configuration parameters exist
    - Fail fast with clear error messages if config is missing
    - _Requirements: 6.5_
  
  - [x] 10.3 Remove Firebase Admin SDK imports
    - Search and remove all firebase_admin imports
    - Remove Firebase initialization code
    - _Requirements: 6.6_

- [ ] 10.4 Write unit test for configuration validation
  - Test startup fails with missing required configuration
  - _Requirements: 6.5_

- [ ] 11. Create data migration utilities
  - [ ] 11.1 Create Firestore export script
    - Export all collections (users, applications, documents, analyses, audit_logs, monitoring_data)
    - Save exported data to JSON files
    - Handle pagination for large collections
    - _Requirements: 9.1_
  
  - [ ] 11.2 Create Firebase Storage download script
    - Download all files from Firebase Storage
    - Organize files by application ID
    - Preserve file metadata
    - _Requirements: 9.4_
  
  - [ ] 11.3 Create SQLite3 import script
    - Read exported JSON files
    - Insert data into SQLite3 database
    - Handle foreign key relationships correctly
    - Use transactions for data consistency
    - _Requirements: 9.2, 9.3_
  
  - [ ] 11.4 Create migration orchestration script
    - Run export, download, and import in sequence
    - Validate data integrity after migration
    - Provide rollback on failure
    - Log progress and errors
    - _Requirements: 9.3, 9.4, 9.6, 9.7_

- [ ] 11.5 Write property test for data migration preservation
  - **Property 12: Data Migration Preservation**
  - **Validates: Requirements 9.3**

- [ ] 11.6 Write property test for file migration completeness
  - **Property 13: File Migration Completeness**
  - **Validates: Requirements 9.4**

- [ ] 11.7 Write integration tests for migration scripts
  - Test export from test Firestore data
  - Test import into test SQLite database
  - Test file download and storage
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 12. Update existing tests to work with SQLite3
  - [ ] 12.1 Update test fixtures and setup
    - Create in-memory SQLite database fixtures
    - Update test data factories for SQLAlchemy models
    - Create test database setup and teardown utilities
    - _Requirements: 8.1, 8.5_
  
  - [ ] 12.2 Update repository tests
    - Update all repository tests to use SQLAlchemy and SQLite3
    - Ensure tests use in-memory databases
    - _Requirements: 8.2_
  
  - [ ] 12.3 Update API endpoint tests
    - Update authentication in tests to use JWT tokens
    - Update test data creation to use SQLAlchemy
    - _Requirements: 8.3_
  
  - [ ] 12.4 Update file storage tests
    - Update tests to use local filesystem storage
    - Use temporary directories for test files
    - _Requirements: 8.4_

- [ ] 13. Final checkpoint - Run full test suite
  - Run all unit tests and property tests
  - Verify test coverage meets goals (80% overall, 100% critical paths)
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 8.6_

- [ ] 14. Create deployment documentation
  - Document migration procedure step-by-step
  - Document new configuration requirements
  - Document rollback procedure
  - Create troubleshooting guide for common issues

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout the migration
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples, edge cases, and error conditions
- Migration utilities are created last since they depend on the new system being functional
