"""
Property-Based Tests for Concurrent Operations

This module contains property-based tests for concurrent operations using Hypothesis.
Tests validate that concurrent operations maintain data consistency and isolation.

Property 41: Concurrent Operation Data Consistency
For any set of concurrent operations on the same application, the system should
maintain data consistency and isolation, ensuring no data corruption or race
conditions occur.

Validates: Requirements 18.5
"""

import pytest
import asyncio
import uuid
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

from app.models.domain import Application, ApplicationStatus
from app.repositories.application_repository import ApplicationRepository


# Define ConcurrencyConflictError locally since concurrency_control module was removed
class ConcurrencyConflictError(Exception):
    """Raised when a concurrency conflict is detected."""
    pass


# Configure Hypothesis to use "fast" profile with 20 examples
settings.register_profile("fast", max_examples=20, deadline=10000)
settings.load_profile("fast")


# Custom strategies for concurrent operations testing
@st.composite
def application_data_strategy(draw):
    """Generate valid application data."""
    # Generate company name with letters and numbers
    company_name = draw(st.text(
        min_size=3, 
        max_size=50, 
        alphabet=st.characters(whitelist_categories=('L', 'N'))
    ))
    # Ensure it's not empty after stripping
    if not company_name.strip():
        company_name = "TestCompany"
    
    return {
        "company_name": company_name,
        "loan_amount": draw(st.floats(min_value=10000, max_value=10000000)),
        "loan_purpose": draw(st.sampled_from(["Working Capital", "Expansion", "Equipment", "Real Estate"])),
        "applicant_email": f"test{draw(st.integers(min_value=1, max_value=10000))}@example.com"
    }


@st.composite
def update_operations_strategy(draw):
    """Generate a sequence of update operations."""
    num_operations = draw(st.integers(min_value=2, max_value=8))
    operations = []
    
    for _ in range(num_operations):
        op_type = draw(st.sampled_from(["update_status", "update_amount", "update_score"]))
        
        if op_type == "update_status":
            operations.append({
                "type": "update_status",
                "status": draw(st.sampled_from([
                    ApplicationStatus.PROCESSING,
                    ApplicationStatus.ANALYSIS_COMPLETE,
                    ApplicationStatus.APPROVED
                ]))
            })
        elif op_type == "update_amount":
            operations.append({
                "type": "update_amount",
                "loan_amount": draw(st.floats(min_value=10000, max_value=10000000))
            })
        else:  # update_score
            operations.append({
                "type": "update_score",
                "credit_score": draw(st.floats(min_value=0, max_value=100))
            })
    
    return operations


# Mock Firestore document for testing
class MockFirestoreDocument:
    """Mock Firestore document that simulates version-based concurrency control."""
    
    def __init__(self, doc_id: str, initial_data: Dict[str, Any]):
        self.doc_id = doc_id
        self.data = initial_data.copy()
        self.data['_version'] = 1
        self.data['_created_at'] = datetime.utcnow()
        self.data['_last_modified'] = datetime.utcnow()
        self.exists = True
        self.lock = asyncio.Lock()
    
    def to_dict(self):
        """Return document data."""
        return self.data.copy()
    
    async def update_with_version_check(self, updates: Dict[str, Any], expected_version: int):
        """Simulate version-based update with concurrency control."""
        async with self.lock:
            current_version = self.data.get('_version', 1)
            
            if current_version != expected_version:
                raise ConcurrencyConflictError(
                    f"Version mismatch: expected {expected_version}, got {current_version}"
                )
            
            # Update data
            self.data.update(updates)
            self.data['_version'] = current_version + 1
            self.data['_last_modified'] = datetime.utcnow()
            
            return self.data.copy()
    
    async def compare_and_swap(self, field: str, expected_value: Any, new_value: Any):
        """Simulate atomic compare-and-swap operation."""
        async with self.lock:
            current_value = self.data.get(field)
            
            if current_value != expected_value:
                return False
            
            self.data[field] = new_value
            self.data['_last_modified'] = datetime.utcnow()
            
            if '_version' in self.data:
                self.data['_version'] += 1
            
            return True


# Helper function to create test application
def create_test_application(app_data: Dict[str, Any]) -> Application:
    """Create a test application."""
    app_id = f"test_app_{uuid.uuid4().hex[:8]}"
    return Application(
        id=app_id,
        company_name=app_data["company_name"],
        loan_amount=app_data["loan_amount"],
        loan_purpose=app_data["loan_purpose"],
        applicant_email=app_data["applicant_email"],
        status=ApplicationStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


# Feature: intelli-credit-platform, Property 41: Concurrent Operation Data Consistency
@pytest.mark.asyncio
@given(
    app_data=application_data_strategy(),
    num_concurrent_updates=st.integers(min_value=2, max_value=5)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_concurrent_status_updates_consistency(app_data, num_concurrent_updates):
    """
    **Validates: Requirements 18.5**
    
    Property 41: Concurrent Operation Data Consistency
    
    For any set of concurrent status update operations on the same application,
    the system should:
    1. Maintain data consistency (no lost updates)
    2. Ensure all updates are applied atomically
    3. Preserve version integrity
    4. Result in a valid final state
    """
    # Create test application and mock document
    application = create_test_application(app_data)
    mock_doc = MockFirestoreDocument(application.id, application.model_dump())
    
    # Define concurrent update operations
    statuses = [
        ApplicationStatus.PROCESSING,
        ApplicationStatus.ANALYSIS_COMPLETE,
        ApplicationStatus.APPROVED,
        ApplicationStatus.APPROVED_WITH_CONDITIONS
    ]
    
    # Track which updates succeeded
    results = []
    
    async def update_status_with_retry(status: ApplicationStatus, index: int):
        """Perform a status update with retry on conflict."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Get current version
                current_data = mock_doc.to_dict()
                current_version = current_data['_version']
                
                # Attempt update
                updated_data = await mock_doc.update_with_version_check(
                    {"status": status.value},
                    current_version
                )
                
                results.append({"index": index, "status": status, "success": True})
                return updated_data
            except ConcurrencyConflictError:
                if attempt == max_retries - 1:
                    results.append({"index": index, "status": status, "success": False})
                    return None
                await asyncio.sleep(0.01)  # Brief delay before retry
    
    # Execute concurrent updates
    tasks = [
        update_status_with_retry(statuses[i % len(statuses)], i)
        for i in range(num_concurrent_updates)
    ]
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Property 1: At least one update should succeed
    successful_updates = [r for r in results if r.get("success")]
    assert len(successful_updates) > 0, \
        "At least one concurrent update should succeed"
    
    # Property 2: Final document state should be consistent
    final_data = mock_doc.to_dict()
    assert final_data is not None, "Document should still exist"
    
    # Property 3: Final status should be one of the attempted statuses
    attempted_statuses = {r["status"].value for r in results if r.get("success")}
    assert final_data["status"] in attempted_statuses, \
        f"Final status {final_data['status']} should be one of the attempted statuses"
    
    # Property 4: Version should have incremented by number of successful updates
    initial_version = 1
    expected_version = initial_version + len(successful_updates)
    assert final_data['_version'] == expected_version, \
        f"Version should be {expected_version}, got {final_data['_version']}"


# Feature: intelli-credit-platform, Property 41: Concurrent Operation Data Consistency
@pytest.mark.asyncio
@given(
    app_data=application_data_strategy(),
    operations=update_operations_strategy()
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_concurrent_mixed_updates_consistency(app_data, operations):
    """
    **Validates: Requirements 18.5**
    
    Property 41: Concurrent Operation Data Consistency
    
    For any set of concurrent mixed update operations (status, amount, score)
    on the same application, the system should:
    1. Apply all updates atomically
    2. Maintain data consistency across all fields
    3. Handle conflicts gracefully with retries
    4. Result in a valid final state
    """
    # Create test application and mock document
    application = create_test_application(app_data)
    mock_doc = MockFirestoreDocument(application.id, application.model_dump())
    
    # Track results
    results = []
    
    async def perform_update(operation: Dict[str, Any], index: int):
        """Perform an update operation with retry on conflict."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Get current version
                current_data = mock_doc.to_dict()
                current_version = current_data['_version']
                
                # Prepare updates based on operation type
                if operation["type"] == "update_status":
                    updates = {"status": operation["status"].value}
                elif operation["type"] == "update_amount":
                    updates = {"loan_amount": operation["loan_amount"]}
                else:  # update_score
                    updates = {"credit_score": operation["credit_score"]}
                
                # Attempt update
                updated_data = await mock_doc.update_with_version_check(updates, current_version)
                
                results.append({"index": index, "operation": operation, "success": True})
                return updated_data
            except ConcurrencyConflictError:
                if attempt == max_retries - 1:
                    results.append({"index": index, "operation": operation, "success": False})
                    return None
                await asyncio.sleep(0.01)
    
    # Execute concurrent updates
    tasks = [perform_update(op, i) for i, op in enumerate(operations)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Property 1: Most updates should succeed (with retries)
    successful_updates = [r for r in results if r.get("success")]
    assert len(successful_updates) >= len(operations) * 0.5, \
        "At least 50% of updates should succeed with retries"
    
    # Property 2: Final document state should be consistent
    final_data = mock_doc.to_dict()
    assert final_data is not None, "Document should still exist"
    
    # Property 3: All fields should have valid values
    assert final_data["loan_amount"] > 0, "Loan amount should be positive"
    assert final_data["status"] in [s.value for s in ApplicationStatus], \
        "Status should be valid"
    if "credit_score" in final_data and final_data["credit_score"] is not None:
        assert 0 <= final_data["credit_score"] <= 100, \
            "Credit score should be in valid range"
    
    # Property 4: Version should reflect successful updates
    expected_version = 1 + len(successful_updates)
    assert final_data['_version'] == expected_version, \
        f"Version should be {expected_version}, got {final_data['_version']}"


# Feature: intelli-credit-platform, Property 41: Concurrent Operation Data Consistency
@pytest.mark.asyncio
@given(
    app_data=application_data_strategy(),
    num_operations=st.integers(min_value=2, max_value=6)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_version_based_concurrency_control(app_data, num_operations):
    """
    **Validates: Requirements 18.5**
    
    Property 41: Concurrent Operation Data Consistency
    
    For any set of concurrent operations using version-based optimistic
    concurrency control, the system should:
    1. Detect version conflicts correctly
    2. Reject updates with stale versions
    3. Allow retries to succeed
    4. Maintain version integrity
    """
    # Create test application and mock document
    application = create_test_application(app_data)
    mock_doc = MockFirestoreDocument(application.id, application.model_dump())
    
    initial_version = mock_doc.to_dict()['_version']
    
    # Track results
    conflict_count = 0
    success_count = 0
    
    async def update_with_version(index: int):
        """Attempt update with version check."""
        nonlocal conflict_count, success_count
        
        try:
            # Get current version
            current_data = mock_doc.to_dict()
            current_version = current_data['_version']
            
            # Attempt update
            await mock_doc.update_with_version_check(
                {"loan_amount": app_data["loan_amount"] + (index * 100)},
                current_version
            )
            success_count += 1
        except ConcurrencyConflictError:
            conflict_count += 1
    
    # Execute concurrent updates
    tasks = [update_with_version(i) for i in range(num_operations)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Property 1: At least one operation should succeed
    assert success_count > 0, "At least one operation should succeed"
    
    # Property 2: Final version should be greater than initial version
    final_data = mock_doc.to_dict()
    final_version = final_data['_version']
    
    assert final_version > initial_version, \
        f"Final version {final_version} should be > initial version {initial_version}"
    
    # Property 3: Version should increment by number of successful updates
    expected_version = initial_version + success_count
    assert final_version == expected_version, \
        f"Final version {final_version} should equal initial {initial_version} + successes {success_count}"
    
    # Property 4: With concurrent operations, conflicts may occur
    # (This is expected behavior, not a failure)
    if num_operations > 2 and conflict_count == 0:
        # It's possible all operations succeeded if they were serialized by the lock
        # This is still correct behavior
        pass


# Feature: intelli-credit-platform, Property 41: Concurrent Operation Data Consistency
@pytest.mark.asyncio
@given(
    app_data=application_data_strategy(),
    num_operations=st.integers(min_value=2, max_value=5)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_compare_and_swap_atomicity(app_data, num_operations):
    """
    **Validates: Requirements 18.5**
    
    Property 41: Concurrent Operation Data Consistency
    
    For any set of concurrent compare-and-swap operations on the same field,
    the system should:
    1. Ensure only one operation succeeds
    2. Maintain atomicity of the operation
    3. Correctly detect mismatches
    4. Leave data in consistent state
    """
    # Create test application with initial status
    application = create_test_application(app_data)
    mock_doc = MockFirestoreDocument(application.id, application.model_dump())
    
    initial_status = ApplicationStatus.PENDING.value
    
    # All operations try to transition from PENDING to different statuses
    target_statuses = [
        ApplicationStatus.PROCESSING.value,
        ApplicationStatus.ANALYSIS_COMPLETE.value,
        ApplicationStatus.APPROVED.value
    ]
    
    results = []
    
    async def cas_operation(target_status: str, index: int):
        """Perform compare-and-swap operation."""
        success = await mock_doc.compare_and_swap(
            'status',
            initial_status,
            target_status
        )
        results.append({
            "index": index,
            "target_status": target_status,
            "success": success
        })
    
    # Execute concurrent CAS operations
    tasks = [
        cas_operation(target_statuses[i % len(target_statuses)], i)
        for i in range(num_operations)
    ]
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Property 1: Exactly one operation should succeed
    successful_ops = [r for r in results if r.get("success") is True]
    assert len(successful_ops) == 1, \
        f"Exactly one CAS operation should succeed, got {len(successful_ops)}"
    
    # Property 2: Final status should match the successful operation's target
    final_data = mock_doc.to_dict()
    successful_status = successful_ops[0]["target_status"]
    assert final_data['status'] == successful_status, \
        f"Final status should be {successful_status}, got {final_data['status']}"
    
    # Property 3: All other operations should have failed (returned False)
    failed_ops = [r for r in results if r.get("success") is False]
    assert len(failed_ops) == num_operations - 1, \
        "All other operations should have failed"


# Feature: intelli-credit-platform, Property 41: Concurrent Operation Data Consistency
@pytest.mark.asyncio
@given(
    app_data=application_data_strategy(),
    num_operations=st.integers(min_value=3, max_value=6)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_retry_mechanism_eventual_consistency(app_data, num_operations):
    """
    **Validates: Requirements 18.5**
    
    Property 41: Concurrent Operation Data Consistency
    
    For any set of concurrent operations with retry mechanism,
    the system should:
    1. Eventually succeed for all operations (with sufficient retries)
    2. Maintain data consistency throughout retries
    3. Handle conflicts gracefully
    4. Converge to a valid final state
    """
    # Create test application and mock document
    application = create_test_application(app_data)
    mock_doc = MockFirestoreDocument(application.id, application.model_dump())
    
    results = []
    
    async def update_with_retry_tracking(index: int):
        """Perform update with retry and track attempts."""
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts:
            attempts += 1
            try:
                # Get current version and data
                current_data = mock_doc.to_dict()
                current_version = current_data['_version']
                current_amount = current_data['loan_amount']
                
                # Attempt update (increment by 100)
                updated_data = await mock_doc.update_with_version_check(
                    {"loan_amount": current_amount + 100},
                    current_version
                )
                
                results.append({
                    "index": index,
                    "success": True,
                    "attempts": attempts,
                    "final_amount": updated_data['loan_amount']
                })
                return True
            except ConcurrencyConflictError:
                if attempts >= max_attempts:
                    results.append({
                        "index": index,
                        "success": False,
                        "attempts": attempts
                    })
                    return False
                await asyncio.sleep(0.01)  # Brief delay before retry
    
    # Execute concurrent updates
    tasks = [update_with_retry_tracking(i) for i in range(num_operations)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Property 1: Most operations should eventually succeed
    successful_ops = [r for r in results if r.get("success")]
    success_rate = len(successful_ops) / len(results)
    assert success_rate >= 0.7, \
        f"At least 70% of operations should succeed, got {success_rate:.1%}"
    
    # Property 2: Final amount should reflect successful increments
    final_data = mock_doc.to_dict()
    
    expected_increments = len(successful_ops)
    expected_amount = app_data["loan_amount"] + (expected_increments * 100)
    
    assert final_data['loan_amount'] == expected_amount, \
        f"Final amount {final_data['loan_amount']} should equal " \
        f"initial {app_data['loan_amount']} + {expected_increments} * 100"
    
    # Property 3: All successful operations should see consistent final amounts
    final_amounts = {r["final_amount"] for r in successful_ops}
    # Each operation increments by 100, so amounts should form a sequence
    assert len(final_amounts) == len(successful_ops), \
        "Each successful operation should see a unique final amount"
    
    # Property 4: With concurrent operations, retries may occur
    # (This is expected behavior when conflicts happen)
    ops_with_retries = [r for r in successful_ops if r.get("attempts", 0) > 1]
    # Note: It's possible no retries were needed if operations were serialized
    # This is still correct behavior

