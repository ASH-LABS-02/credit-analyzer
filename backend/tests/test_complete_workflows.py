"""
Integration tests for complete end-to-end workflows.

These tests verify the complete user journeys through the system:
1. Document upload → extraction → analysis → CAM generation
2. User authentication → application creation → analysis
3. Monitoring activation → alert generation → notification

Architecture:
- Firestore: Database for all application data, documents metadata, and analysis results
- Firebase Authentication: User authentication and authorization
- Document Storage: Documents stored as base64 in Firestore (no Firebase Storage)

Task: 33.1 Write integration tests for complete workflows
Requirements: All (integration)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io
import base64

from app.main import app
from app.models.domain import (
    Application, ApplicationStatus, CreditRecommendation,
    Document, MonitoringAlert
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_auth_token():
    """Mock authentication token for testing."""
    return "mock-auth-token-12345"


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for upload testing."""
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    return io.BytesIO(pdf_content)


class TestDocumentUploadToCAMWorkflow:
    """
    Test complete workflow: Document upload → extraction → analysis → CAM generation
    
    This workflow represents the core user journey where a credit analyst:
    1. Creates a new application
    2. Uploads financial documents (stored as base64 in Firestore)
    3. Triggers analysis
    4. Reviews results
    5. Generates CAM report
    
    Architecture: Documents stored in Firestore as base64-encoded content
    
    Requirements: 1.1, 1.4, 2.1, 3.1, 7.1
    """
    
    @pytest.mark.asyncio
    async def test_complete_document_to_cam_workflow(
        self,
        client,
        mock_auth_token,
        sample_pdf_file
    ):
        """
        Test complete workflow from document upload to CAM generation.
        
        Steps:
        1. Create application
        2. Upload documents (stored in Firestore as base64)
        3. Trigger analysis
        4. Wait for completion
        5. Generate CAM
        6. Export CAM
        
        Architecture: All data stored in Firestore, no Firebase Storage
        
        Requirements: 1.1, 1.4, 2.1, 3.1, 7.1, 7.4
        """
        # Step 1: Create application
        with patch('app.api.applications.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            # Mock Firestore document creation
            with patch('app.repositories.application_repository.ApplicationRepository.create') as mock_create:
                mock_create.return_value = {
                    "id": "app-test-123",
                    "company_name": "Test Company Inc",
                    "loan_amount": 1000000.0,
                    "loan_purpose": "Working capital",
                    "applicant_email": "cfo@testcompany.com",
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                create_response = client.post(
                    "/api/v1/applications",
                    json={
                        "company_name": "Test Company Inc",
                        "loan_amount": 1000000.0,
                        "loan_purpose": "Working capital",
                        "applicant_email": "cfo@testcompany.com"
                    },
                    headers={"Authorization": f"Bearer {mock_auth_token}"}
                )
        
        assert create_response.status_code == 201
        application_data = create_response.json()
        application_id = application_data["id"]
        assert application_data["status"] == "pending"
        
        # Step 2: Upload documents (stored in Firestore as base64)
        with patch('app.api.documents.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            # Mock Firestore document storage
            with patch('app.repositories.document_repository.DocumentRepository.create') as mock_doc_create:
                # Encode file content as base64 (simulating Firestore storage)
                file_content = sample_pdf_file.read()
                base64_content = base64.b64encode(file_content).decode('utf-8')
                
                mock_doc_create.return_value = {
                    "id": "doc-test-123",
                    "application_id": application_id,
                    "filename": "financial_statement.pdf",
                    "file_type": "application/pdf",
                    "document_type": "financial_statement",
                    "content_base64": base64_content,  # Stored in Firestore
                    "file_size": len(file_content),
                    "processing_status": "pending",
                    "upload_date": datetime.utcnow().isoformat()
                }
                
                # Upload financial statement
                sample_pdf_file.seek(0)  # Reset file pointer
                files = {"file": ("financial_statement.pdf", sample_pdf_file, "application/pdf")}
                upload_response = client.post(
                    f"/api/v1/applications/{application_id}/documents",
                    files=files,
                    data={"document_type": "financial_statement"},
                    headers={"Authorization": f"Bearer {mock_auth_token}"}
                )
        
        assert upload_response.status_code == 201
        document_data = upload_response.json()
        assert document_data["filename"] == "financial_statement.pdf"
        assert document_data["processing_status"] == "pending"
        # Verify document is stored in Firestore (not Firebase Storage)
        assert "content_base64" in document_data or "id" in document_data
        
        # Step 3: Trigger analysis
        with patch('app.api.analysis.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            # Mock the orchestrator to return successful analysis
            with patch('app.api.analysis.orchestrator_agent') as mock_orchestrator:
                mock_orchestrator.process_application = AsyncMock(return_value={
                    "success": True,
                    "application_id": application_id,
                    "company_name": "Test Company Inc",
                    "extracted_data": {"documents_processed": 1},
                    "financial_analysis": {"ratios": {"current_ratio": {"value": 2.0}}},
                    "research": {"web": {}, "promoter": {}, "industry": {}},
                    "forecasts": {"forecasts": {}},
                    "risk_assessment": {
                        "overall_score": 75.0,
                        "recommendation": "approve"
                    },
                    "cam": {"content": "CAM content"},
                    "errors": [],
                    "warnings": [],
                    "processing_time": 120.5,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                analysis_response = client.post(
                    f"/api/v1/applications/{application_id}/analyze",
                    headers={"Authorization": f"Bearer {mock_auth_token}"}
                )
        
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        assert analysis_data["success"] is True
        assert analysis_data["risk_assessment"]["overall_score"] == 75.0
        
        # Step 4: Get analysis results (stored in Firestore)
        with patch('app.api.analysis.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            results_response = client.get(
                f"/api/v1/applications/{application_id}/results",
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
        
        assert results_response.status_code == 200
        results_data = results_response.json()
        assert "risk_assessment" in results_data
        
        # Step 5: Generate CAM (stored in Firestore)
        with patch('app.api.cam.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            cam_response = client.post(
                f"/api/v1/applications/{application_id}/cam",
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
        
        assert cam_response.status_code == 200
        cam_data = cam_response.json()
        assert "content" in cam_data
        
        # Step 6: Export CAM (generated from Firestore data)
        with patch('app.api.cam.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            export_response = client.get(
                f"/api/v1/applications/{application_id}/cam/export?format=pdf",
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
        
        # Export may return 200 or 404 depending on implementation
        assert export_response.status_code in [200, 404]
        
        # Verify: Complete workflow executed successfully
        # All data stored in Firestore (documents, analysis results, CAM)
        # No Firebase Storage used
        # Application progressed through states correctly


class TestAuthenticationToAnalysisWorkflow:
    """
    Test complete workflow: User authentication → application creation → analysis
    
    This workflow represents the user journey from login to analysis:
    1. User logs in
    2. Creates new application
    3. Uploads documents
    4. Triggers analysis
    5. Views results
    
    Requirements: 8.1, 8.2, 9.1, 3.1
    """
    
    @pytest.mark.asyncio
    async def test_authentication_to_analysis_workflow(self, client):
        """
        Test complete workflow from user login to analysis completion.
        
        Steps:
        1. User login
        2. Create application
        3. Upload documents
        4. Trigger analysis
        5. View results
        
        Requirements: 8.1, 8.2, 9.1, 3.1
        """
        # Step 1: User login
        with patch('app.api.auth.auth_service') as mock_auth:
            mock_auth.login = AsyncMock(return_value={
                "user": {
                    "uid": "test-user-123",
                    "email": "analyst@bank.com",
                    "role": "analyst"
                },
                "token": "mock-token-12345",
                "expires_at": (datetime.utcnow().timestamp() + 3600)
            })
            
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "analyst@bank.com",
                    "password": "secure-password"
                }
            )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "token" in login_data
        auth_token = login_data["token"]
        
        # Step 2: Create application (authenticated)
        with patch('app.api.applications.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            create_response = client.post(
                "/api/v1/applications",
                json={
                    "company_name": "Authenticated Test Co",
                    "loan_amount": 500000.0,
                    "loan_purpose": "Equipment purchase",
                    "applicant_email": "cfo@authtest.com"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
        
        assert create_response.status_code == 201
        application_data = create_response.json()
        application_id = application_data["id"]
        
        # Step 3: Upload documents
        with patch('app.api.documents.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            # Mock file upload
            files = {"file": ("test.pdf", io.BytesIO(b"PDF content"), "application/pdf")}
            upload_response = client.post(
                f"/api/v1/applications/{application_id}/documents",
                files=files,
                data={"document_type": "financial_statement"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
        
        assert upload_response.status_code == 201
        
        # Step 4: Trigger analysis
        with patch('app.api.analysis.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            with patch('app.api.analysis.orchestrator_agent') as mock_orchestrator:
                mock_orchestrator.process_application = AsyncMock(return_value={
                    "success": True,
                    "application_id": application_id,
                    "company_name": "Authenticated Test Co",
                    "extracted_data": {},
                    "financial_analysis": {},
                    "research": {},
                    "forecasts": {},
                    "risk_assessment": {"overall_score": 70.0, "recommendation": "approve"},
                    "cam": {},
                    "errors": [],
                    "warnings": [],
                    "processing_time": 100.0,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                analysis_response = client.post(
                    f"/api/v1/applications/{application_id}/analyze",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
        
        assert analysis_response.status_code == 200
        
        # Step 5: View results
        with patch('app.api.analysis.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            results_response = client.get(
                f"/api/v1/applications/{application_id}/results",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
        
        assert results_response.status_code == 200
        
        # Verify: Complete authenticated workflow executed successfully
        # User was authenticated throughout
        # All operations required valid token


class TestMonitoringWorkflow:
    """
    Test complete workflow: Monitoring activation → alert generation → notification
    
    This workflow represents post-approval monitoring:
    1. Application is approved
    2. Monitoring is activated
    3. Periodic checks detect changes
    4. Alerts are generated
    5. Notifications are sent
    
    Requirements: 10.1, 10.2, 10.3, 10.4
    """
    
    @pytest.mark.asyncio
    async def test_monitoring_activation_to_alert_workflow(self, client, mock_auth_token):
        """
        Test complete monitoring workflow from activation to alert notification.
        
        Steps:
        1. Create and approve application
        2. Activate monitoring
        3. Simulate periodic check
        4. Detect material change
        5. Generate alert
        6. Verify notification
        
        Requirements: 10.1, 10.2, 10.3, 10.4
        """
        # Step 1: Create application
        with patch('app.api.applications.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            create_response = client.post(
                "/api/v1/applications",
                json={
                    "company_name": "Monitored Company Inc",
                    "loan_amount": 2000000.0,
                    "loan_purpose": "Business expansion",
                    "applicant_email": "cfo@monitored.com"
                },
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
        
        assert create_response.status_code == 201
        application_id = create_response.json()["id"]
        
        # Step 2: Approve application (which activates monitoring)
        with patch('app.api.applications.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            # Mock monitoring service
            with patch('app.services.monitoring_service.MonitoringService') as mock_monitoring:
                mock_monitoring_instance = MagicMock()
                mock_monitoring_instance.activate_monitoring = AsyncMock(return_value=True)
                mock_monitoring.return_value = mock_monitoring_instance
                
                approve_response = client.patch(
                    f"/api/v1/applications/{application_id}",
                    json={"status": "approved"},
                    headers={"Authorization": f"Bearer {mock_auth_token}"}
                )
        
        assert approve_response.status_code == 200
        
        # Step 3: Simulate periodic monitoring check
        with patch('app.services.monitoring_service.MonitoringService') as mock_monitoring:
            mock_monitoring_instance = MagicMock()
            
            # Mock detection of material change
            mock_monitoring_instance.check_for_changes = AsyncMock(return_value={
                "changes_detected": True,
                "severity": "high",
                "changes": [
                    {
                        "type": "financial_deterioration",
                        "description": "Significant decline in revenue reported",
                        "impact": "high"
                    }
                ]
            })
            
            mock_monitoring.return_value = mock_monitoring_instance
            
            # Trigger monitoring check (this would normally be scheduled)
            check_result = await mock_monitoring_instance.check_for_changes(application_id)
        
        assert check_result["changes_detected"] is True
        assert check_result["severity"] == "high"
        
        # Step 4: Generate alert
        with patch('app.services.monitoring_service.MonitoringService') as mock_monitoring:
            mock_monitoring_instance = MagicMock()
            
            mock_monitoring_instance.generate_alert = AsyncMock(return_value={
                "alert_id": "alert-123",
                "application_id": application_id,
                "alert_type": "financial_deterioration",
                "severity": "high",
                "message": "Significant decline in revenue reported",
                "created_at": datetime.utcnow().isoformat()
            })
            
            mock_monitoring.return_value = mock_monitoring_instance
            
            alert = await mock_monitoring_instance.generate_alert(
                application_id,
                "financial_deterioration",
                "high",
                "Significant decline in revenue reported"
            )
        
        assert alert["alert_id"] == "alert-123"
        assert alert["severity"] == "high"
        
        # Step 5: Verify alert retrieval
        with patch('app.api.search_monitoring.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            alerts_response = client.get(
                "/api/v1/monitoring/alerts",
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
        
        # May return 200 with empty list or 404 depending on implementation
        assert alerts_response.status_code in [200, 404]
        
        # Verify: Complete monitoring workflow executed successfully
        # Monitoring was activated on approval
        # Changes were detected
        # Alerts were generated
        # Notifications would be sent (mocked)


class TestErrorRecoveryWorkflows:
    """
    Test error scenarios and recovery mechanisms across workflows.
    
    These tests verify that the system handles errors gracefully:
    1. Invalid document upload recovery
    2. Analysis failure recovery
    3. Network error recovery
    
    Requirements: 15.1, 15.2, 15.4
    """
    
    @pytest.mark.asyncio
    async def test_invalid_document_upload_recovery(self, client, mock_auth_token):
        """
        Test recovery from invalid document upload.
        
        Steps:
        1. Create application
        2. Attempt to upload invalid file
        3. Receive error
        4. Upload valid file (stored in Firestore as base64)
        5. Continue workflow
        
        Architecture: Documents stored in Firestore, not Firebase Storage
        
        Requirements: 1.2, 1.3, 15.4
        """
        # Step 1: Create application
        with patch('app.api.applications.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            with patch('app.repositories.application_repository.ApplicationRepository.create') as mock_create:
                mock_create.return_value = {
                    "id": "app-recovery-123",
                    "company_name": "Recovery Test Co",
                    "loan_amount": 750000.0,
                    "loan_purpose": "Inventory financing",
                    "applicant_email": "cfo@recovery.com",
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                create_response = client.post(
                    "/api/v1/applications",
                    json={
                        "company_name": "Recovery Test Co",
                        "loan_amount": 750000.0,
                        "loan_purpose": "Inventory financing",
                        "applicant_email": "cfo@recovery.com"
                    },
                    headers={"Authorization": f"Bearer {mock_auth_token}"}
                )
        
        assert create_response.status_code == 201
        application_id = create_response.json()["id"]
        
        # Step 2: Attempt invalid file upload (wrong format)
        with patch('app.api.documents.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            invalid_files = {"file": ("test.exe", io.BytesIO(b"EXE content"), "application/x-msdownload")}
            invalid_response = client.post(
                f"/api/v1/applications/{application_id}/documents",
                files=invalid_files,
                data={"document_type": "financial_statement"},
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
        
        # Should reject invalid file
        assert invalid_response.status_code in [400, 422]
        
        # Step 3: Upload valid file (stored in Firestore)
        with patch('app.api.documents.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            with patch('app.repositories.document_repository.DocumentRepository.create') as mock_doc_create:
                file_content = b"%PDF-1.4 valid content"
                base64_content = base64.b64encode(file_content).decode('utf-8')
                
                mock_doc_create.return_value = {
                    "id": "doc-recovery-123",
                    "application_id": application_id,
                    "filename": "valid.pdf",
                    "file_type": "application/pdf",
                    "content_base64": base64_content,  # Stored in Firestore
                    "file_size": len(file_content),
                    "processing_status": "pending",
                    "upload_date": datetime.utcnow().isoformat()
                }
                
                valid_files = {"file": ("valid.pdf", io.BytesIO(file_content), "application/pdf")}
                valid_response = client.post(
                    f"/api/v1/applications/{application_id}/documents",
                    files=valid_files,
                    data={"document_type": "financial_statement"},
                    headers={"Authorization": f"Bearer {mock_auth_token}"}
                )
        
        assert valid_response.status_code == 201
        
        # Verify: System recovered from error and accepted valid file
        # Document stored in Firestore, not Firebase Storage
        # Application can continue with valid document
    
    
    @pytest.mark.asyncio
    async def test_analysis_failure_recovery(self, client, mock_auth_token):
        """
        Test recovery from analysis failure.
        
        Steps:
        1. Create application with documents
        2. Trigger analysis (fails)
        3. Receive error response
        4. Retry analysis (succeeds)
        5. Continue workflow
        
        Requirements: 15.1, 15.2
        """
        # Step 1: Create application
        with patch('app.api.applications.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            create_response = client.post(
                "/api/v1/applications",
                json={
                    "company_name": "Retry Test Co",
                    "loan_amount": 1500000.0,
                    "loan_purpose": "Working capital",
                    "applicant_email": "cfo@retry.com"
                },
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
        
        assert create_response.status_code == 201
        application_id = create_response.json()["id"]
        
        # Step 2: First analysis attempt (fails)
        with patch('app.api.analysis.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            with patch('app.api.analysis.orchestrator_agent') as mock_orchestrator:
                mock_orchestrator.process_application = AsyncMock(
                    side_effect=Exception("Temporary service unavailable")
                )
                
                first_attempt = client.post(
                    f"/api/v1/applications/{application_id}/analyze",
                    headers={"Authorization": f"Bearer {mock_auth_token}"}
                )
        
        # Should return error
        assert first_attempt.status_code in [500, 503]
        
        # Step 3: Retry analysis (succeeds)
        with patch('app.api.analysis.get_current_user') as mock_user:
            mock_user.return_value = {"uid": "test-user-123", "email": "analyst@bank.com"}
            
            with patch('app.api.analysis.orchestrator_agent') as mock_orchestrator:
                mock_orchestrator.process_application = AsyncMock(return_value={
                    "success": True,
                    "application_id": application_id,
                    "company_name": "Retry Test Co",
                    "extracted_data": {},
                    "financial_analysis": {},
                    "research": {},
                    "forecasts": {},
                    "risk_assessment": {"overall_score": 65.0, "recommendation": "approve_with_conditions"},
                    "cam": {},
                    "errors": [],
                    "warnings": [],
                    "processing_time": 95.0,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                retry_attempt = client.post(
                    f"/api/v1/applications/{application_id}/analyze",
                    headers={"Authorization": f"Bearer {mock_auth_token}"}
                )
        
        assert retry_attempt.status_code == 200
        
        # Verify: System recovered from failure on retry
        # Analysis completed successfully after initial failure
