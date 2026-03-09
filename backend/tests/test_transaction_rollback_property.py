"""
Property-based tests for Transaction Manager.

Feature: intelli-credit-platform
Property 32: Database Transaction Rollback

Validates: Requirements 15.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.core.transaction_manager import TransactionManager


# Test data strategies
application_id_strategy = st.text(min_size=10, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
))
operation_name_strategy = st.text(min_size=5, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), whitelist_characters='-_'
))
error_message_strategy = st.text(min_size=10, max_size=100)


def create_mock_firestore():
    """Create a mock Firestore client with transaction logging support."""
    mock_db = MagicMock()
    mock_transaction = MagicMock()
    mock_db.transaction.return_value = mock_transaction
    
    # Mock collections
    mock_logs_collection = MagicMock()
    mock_log_doc_ref = MagicMock()
    
    def collection_side_effect(name):
        if name == "transaction_logs":
            return mock_logs_collection
        return MagicMock()
    
    mock_db.collection.side_effect = collection_side_effect
    mock_logs_collection.document.return_value = mock_log_doc_ref
    
    return mock_db, mock_transaction, mock_log_doc_ref


class TestProperty32TransactionLogging:
    """
    Property: Transaction Logging Completeness
    
    **Validates: Requirements 15.3**
    
    For any transaction (successful or failed), the system should log
    the transaction with appropriate status and details.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        app_id=application_id_strategy,
        operation_name=operation_name_strategy
    )
    async def test_transaction_start_is_logged(
        self,
        app_id: str,
        operation_name: str
    ):
        """
        Property: All transactions are logged when they start.
        
        For any transaction, a log entry with 'started' status should be created.
        """
        assume(len(app_id.strip()) > 0)
        assume(len(operation_name.strip()) > 0)
        
        mock_db, mock_transaction, mock_log_doc_ref = create_mock_firestore()
        
        with patch('app.core.transaction_manager.get_firestore_client', return_value=mock_db):
            transaction_manager = TransactionManager()
            
            # Execute successful transaction
            async with transaction_manager.transaction(
                operation_name,
                {'application_id': app_id}
            ):
                # Simple operation
                pass
            
            # Verify transaction log was created (set called for start)
            assert mock_log_doc_ref.set.called, "Transaction start was not logged"
            
            # Get the set call arguments
            set_call_args = mock_log_doc_ref.set.call_args[0][0]
            
            # Verify log entry contains required fields
            assert 'transaction_id' in set_call_args
            assert 'operation_name' in set_call_args
            assert set_call_args['operation_name'] == operation_name
            assert 'status' in set_call_args
            assert set_call_args['status'] == 'started'
            assert 'started_at' in set_call_args
            assert 'context' in set_call_args
            assert set_call_args['context']['application_id'] == app_id
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        app_id=application_id_strategy,
        operation_name=operation_name_strategy
    )
    async def test_successful_transaction_completion_is_logged(
        self,
        app_id: str,
        operation_name: str
    ):
        """
        Property: Successful transactions are logged with 'completed' status.
        """
        assume(len(app_id.strip()) > 0)
        assume(len(operation_name.strip()) > 0)
        
        mock_db, mock_transaction, mock_log_doc_ref = create_mock_firestore()
        
        with patch('app.core.transaction_manager.get_firestore_client', return_value=mock_db):
            transaction_manager = TransactionManager()
            
            # Execute successful transaction
            async with transaction_manager.transaction(
                operation_name,
                {'application_id': app_id}
            ):
                pass
            
            # Verify transaction log was updated (update called for completion)
            assert mock_log_doc_ref.update.called, "Transaction completion was not logged"
            
            # Get the update call arguments
            update_call_args = mock_log_doc_ref.update.call_args[0][0]
            
            # Verify completion was logged
            assert 'status' in update_call_args
            assert update_call_args['status'] == 'completed'
            assert 'completed_at' in update_call_args
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        app_id=application_id_strategy,
        operation_name=operation_name_strategy,
        error_message=error_message_strategy
    )
    async def test_failed_transaction_rollback_is_logged(
        self,
        app_id: str,
        operation_name: str,
        error_message: str
    ):
        """
        Property: Failed transactions are logged with 'rolled_back' status
        and error information.
        """
        assume(len(app_id.strip()) > 0)
        assume(len(operation_name.strip()) > 0)
        assume(len(error_message.strip()) > 0)
        
        mock_db, mock_transaction, mock_log_doc_ref = create_mock_firestore()
        
        with patch('app.core.transaction_manager.get_firestore_client', return_value=mock_db):
            transaction_manager = TransactionManager()
            
            # Execute failing transaction
            with pytest.raises(Exception):
                async with transaction_manager.transaction(
                    operation_name,
                    {'application_id': app_id}
                ):
                    raise ValueError(error_message)
            
            # Verify transaction log was created
            assert mock_log_doc_ref.set.called, "Transaction start was not logged"
            
            # Verify transaction log was updated with rollback status
            assert mock_log_doc_ref.update.called, "Transaction rollback was not logged"
            
            # Get the update call arguments
            update_call_args = mock_log_doc_ref.update.call_args[0][0]
            
            # Verify rollback was logged with error information
            assert 'status' in update_call_args
            assert update_call_args['status'] == 'rolled_back'
            assert 'rolled_back_at' in update_call_args
            assert 'error_type' in update_call_args
            assert update_call_args['error_type'] == 'ValueError'
            assert 'error_message' in update_call_args
            assert error_message in update_call_args['error_message']


class TestProperty32TransactionLogRetrieval:
    """
    Property: Transaction Log Retrieval
    
    **Validates: Requirements 15.3**
    
    Transaction logs should be retrievable by transaction ID for debugging
    and monitoring purposes.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=50, deadline=None)
    @given(
        transaction_id=st.uuids()
    )
    async def test_get_transaction_log_returns_data(
        self,
        transaction_id
    ):
        """
        Property: Transaction logs can be retrieved by ID.
        """
        mock_db, _, _ = create_mock_firestore()
        
        # Mock the get operation
        mock_doc_ref = MagicMock()
        mock_snapshot = MagicMock()
        mock_snapshot.exists = True
        mock_snapshot.to_dict.return_value = {
            'transaction_id': str(transaction_id),
            'status': 'completed',
            'operation_name': 'test_operation'
        }
        mock_doc_ref.get.return_value = mock_snapshot
        
        mock_logs_collection = MagicMock()
        mock_logs_collection.document.return_value = mock_doc_ref
        
        def collection_side_effect(name):
            if name == "transaction_logs":
                return mock_logs_collection
            return MagicMock()
        
        mock_db.collection.side_effect = collection_side_effect
        
        with patch('app.core.transaction_manager.get_firestore_client', return_value=mock_db):
            transaction_manager = TransactionManager()
            
            # Retrieve transaction log
            log = await transaction_manager.get_transaction_log(str(transaction_id))
            
            # Verify log was retrieved
            assert log is not None
            assert log['transaction_id'] == str(transaction_id)
            assert 'status' in log
            assert 'operation_name' in log
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=50, deadline=None)
    @given(
        transaction_id=st.uuids()
    )
    async def test_get_nonexistent_transaction_log_returns_none(
        self,
        transaction_id
    ):
        """
        Property: Retrieving a non-existent transaction log returns None.
        """
        mock_db, _, _ = create_mock_firestore()
        
        # Mock the get operation for non-existent document
        mock_doc_ref = MagicMock()
        mock_snapshot = MagicMock()
        mock_snapshot.exists = False
        mock_doc_ref.get.return_value = mock_snapshot
        
        mock_logs_collection = MagicMock()
        mock_logs_collection.document.return_value = mock_doc_ref
        
        def collection_side_effect(name):
            if name == "transaction_logs":
                return mock_logs_collection
            return MagicMock()
        
        mock_db.collection.side_effect = collection_side_effect
        
        with patch('app.core.transaction_manager.get_firestore_client', return_value=mock_db):
            transaction_manager = TransactionManager()
            
            # Retrieve non-existent transaction log
            log = await transaction_manager.get_transaction_log(str(transaction_id))
            
            # Verify None is returned
            assert log is None
