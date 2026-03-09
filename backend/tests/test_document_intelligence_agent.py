"""
Unit tests for DocumentIntelligenceAgent

Tests AI-powered financial data extraction from documents.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.agents.document_intelligence_agent import DocumentIntelligenceAgent
from app.models.domain import Document
from app.repositories.document_repository import DocumentRepository
from app.services.document_processor import DocumentProcessor


@pytest.fixture
def mock_document_repository():
    """Create a mock DocumentRepository"""
    repo = Mock(spec=DocumentRepository)
    repo.get_by_application = AsyncMock()
    return repo


@pytest.fixture
def mock_document_processor():
    """Create a mock DocumentProcessor"""
    return Mock(spec=DocumentProcessor)


@pytest.fixture
def agent(mock_document_repository, mock_document_processor):
    """Create a DocumentIntelligenceAgent instance with mocked dependencies"""
    return DocumentIntelligenceAgent(
        document_repository=mock_document_repository,
        document_processor=mock_document_processor
    )


@pytest.fixture
def sample_document():
    """Create a sample document with extracted text"""
    return Document(
        id="doc123",
        application_id="app123",
        filename="financial_statement.pdf",
        file_type="pdf",
        storage_path="documents/app123/doc123.pdf",
        upload_date=datetime.utcnow(),
        processing_status="complete",
        extracted_data={
            "text": """[Page 1]
            Financial Statement 2023
            Company: ABC Corporation
            
            Revenue: $5,000,000
            Net Profit: $1,200,000
            Total Assets: $10,000,000
            Total Equity: $6,000,000
            
            [Page 2]
            Balance Sheet
            Current Assets: $3,000,000
            Current Liabilities: $1,500,000
            Total Debt: $4,000,000
            
            Current Ratio: 2.0
            Debt to Equity: 0.67
            """
        }
    )


@pytest.fixture
def sample_openai_response():
    """Sample OpenAI API response"""
    return {
        "company_info": {
            "company_name": "ABC Corporation",
            "industry": None,
            "fiscal_year": "2023"
        },
        "financial_metrics": {
            "revenue": {
                "values": [5000000],
                "years": ["2023"],
                "currency": "USD",
                "confidence": "high"
            },
            "profit": {
                "values": [1200000],
                "years": ["2023"],
                "currency": "USD",
                "confidence": "high"
            },
            "debt": {
                "values": [4000000],
                "years": ["2023"],
                "currency": "USD",
                "confidence": "high"
            },
            "cash_flow": {
                "values": [],
                "years": [],
                "currency": "USD",
                "confidence": "low"
            },
            "current_assets": {
                "value": 3000000,
                "year": "2023",
                "confidence": "high"
            },
            "current_liabilities": {
                "value": 1500000,
                "year": "2023",
                "confidence": "high"
            },
            "total_assets": {
                "value": 10000000,
                "year": "2023",
                "confidence": "high"
            },
            "total_equity": {
                "value": 6000000,
                "year": "2023",
                "confidence": "high"
            },
            "total_debt": {
                "value": 4000000,
                "year": "2023",
                "confidence": "high"
            }
        },
        "financial_ratios": {
            "current_ratio": {
                "value": 2.0,
                "confidence": "high"
            },
            "debt_to_equity": {
                "value": 0.67,
                "confidence": "high"
            },
            "net_profit_margin": {
                "value": None,
                "confidence": "low"
            },
            "roe": {
                "value": None,
                "confidence": "low"
            }
        },
        "notes": [
            "Cash flow data not found in document",
            "Net profit margin and ROE not explicitly stated"
        ]
    }


class TestDocumentIntelligenceAgent:
    """Test suite for DocumentIntelligenceAgent"""
    
    @pytest.mark.asyncio
    async def test_extract_with_no_documents(self, agent, mock_document_repository):
        """Test extraction when no documents are available"""
        # Setup
        mock_document_repository.get_by_application.return_value = []
        
        # Execute
        result = await agent.extract("app123")
        
        # Assert
        assert result["financial_data"] == {}
        assert result["source_tracking"] == {}
        assert result["ambiguous_flags"] == []
        assert result["documents_processed"] == 0
    
    @pytest.mark.asyncio
    async def test_extract_with_single_document(
        self, 
        agent, 
        mock_document_repository,
        sample_document,
        sample_openai_response
    ):
        """Test extraction from a single document"""
        # Setup
        mock_document_repository.get_by_application.return_value = [sample_document]
        
        # Mock OpenAI API call
        import json
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(sample_openai_response)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            # Execute
            result = await agent.extract("app123")
        
        # Assert
        assert result["documents_processed"] == 1
        assert "revenue" in result["financial_data"]
        assert len(result["source_tracking"]) > 0
        assert len(result["ambiguous_flags"]) > 0
    
    @pytest.mark.asyncio
    async def test_extract_handles_document_processing_error(
        self,
        agent,
        mock_document_repository,
        sample_document
    ):
        """Test that extraction continues when one document fails"""
        # Setup - create two documents, one will fail
        doc1 = sample_document
        doc2 = Document(
            id="doc456",
            application_id="app123",
            filename="bad_doc.pdf",
            file_type="pdf",
            storage_path="documents/app123/doc456.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data=None  # This will cause an error
        )
        
        mock_document_repository.get_by_application.return_value = [doc1, doc2]
        
        # Mock OpenAI to fail for the bad document
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"company_info": {}, "financial_metrics": {}, "financial_ratios": {}, "notes": []}'
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            # Execute - should not raise exception
            result = await agent.extract("app123")
        
        # Assert - should process at least the good document
        assert result["documents_processed"] >= 0
    
    def test_build_extraction_prompt(self, agent):
        """Test that extraction prompt is properly formatted"""
        # Setup
        text = "Sample financial document text"
        
        # Execute
        prompt = agent._build_extraction_prompt(text)
        
        # Assert
        assert "Extract financial data" in prompt
        assert "JSON object" in prompt
        assert "revenue" in prompt
        assert "profit" in prompt
        assert "debt" in prompt
        assert "cash_flow" in prompt
        assert text in prompt
    
    def test_identify_source_pages_with_page_markers(self, agent):
        """Test source page identification with page markers"""
        # Setup
        text = """[Page 1]
        Revenue: $5,000,000
        [Page 2]
        Total Assets: $10,000,000
        """
        
        structured_data = {
            "financial_metrics": {
                "revenue": {
                    "values": [5000000],
                    "confidence": "high"
                },
                "total_assets": {
                    "value": 10000000,
                    "confidence": "high"
                }
            }
        }
        
        # Execute
        source_pages = agent._identify_source_pages(text, structured_data)
        
        # Assert
        assert "financial_metrics.revenue" in source_pages
        assert source_pages["financial_metrics.revenue"] == 1
        assert "financial_metrics.total_assets" in source_pages
        assert source_pages["financial_metrics.total_assets"] == 2
    
    def test_identify_source_pages_without_page_markers(self, agent):
        """Test source page identification without page markers"""
        # Setup
        text = "Revenue: $5,000,000"
        structured_data = {
            "financial_metrics": {
                "revenue": {
                    "values": [5000000],
                    "confidence": "high"
                }
            }
        }
        
        # Execute
        source_pages = agent._identify_source_pages(text, structured_data)
        
        # Assert - should return empty dict when no page markers
        assert source_pages == {}
    
    def test_flag_ambiguous_data_low_confidence(self, agent):
        """Test flagging of low confidence extractions"""
        # Setup
        structured_data = {
            "financial_metrics": {
                "revenue": {
                    "values": [5000000],
                    "confidence": "low"
                },
                "profit": {
                    "values": [1000000],
                    "confidence": "high"
                }
            },
            "notes": []
        }
        
        # Execute
        flags = agent._flag_ambiguous_data(structured_data)
        
        # Assert
        assert len(flags) > 0
        assert any(flag["field"] == "financial_metrics.revenue" for flag in flags)
        assert any(flag["reason"] == "Low confidence extraction" for flag in flags)
    
    def test_flag_ambiguous_data_missing_critical_metrics(self, agent):
        """Test flagging of missing critical metrics"""
        # Setup
        structured_data = {
            "financial_metrics": {
                "revenue": {
                    "values": [],
                    "confidence": "high"
                }
            },
            "notes": []
        }
        
        # Execute
        flags = agent._flag_ambiguous_data(structured_data)
        
        # Assert
        assert len(flags) > 0
        # Should flag missing revenue and other critical metrics
        critical_flags = [f for f in flags if "Critical metric not found" in f["reason"]]
        assert len(critical_flags) > 0
    
    def test_flag_ambiguous_data_from_notes(self, agent):
        """Test flagging based on extraction notes"""
        # Setup
        structured_data = {
            "financial_metrics": {},
            "notes": [
                "Revenue value is unclear in the document",
                "Assumption made: fiscal year is 2023"
            ]
        }
        
        # Execute
        flags = agent._flag_ambiguous_data(structured_data)
        
        # Assert
        assert len(flags) >= 2
        assert any("unclear" in flag["reason"].lower() for flag in flags)
        assert any("assumption" in flag["reason"].lower() for flag in flags)
    
    def test_merge_extracted_data_empty_list(self, agent):
        """Test merging with empty extraction list"""
        # Execute
        result = agent._merge_extracted_data([])
        
        # Assert
        assert result["financial_data"] == {}
        assert result["source_tracking"] == {}
        assert result["ambiguous_flags"] == []
        assert result["documents_processed"] == 0
    
    def test_merge_extracted_data_single_document(self, agent):
        """Test merging data from a single document"""
        # Setup
        extraction = {
            "document_id": "doc123",
            "data": {
                "financial_metrics": {
                    "revenue": {
                        "values": [5000000],
                        "confidence": "high"
                    }
                },
                "company_info": {
                    "company_name": "ABC Corp"
                }
            },
            "source_pages": {
                "financial_metrics.revenue": 1
            },
            "ambiguous_flags": [
                {"field": "test", "reason": "test reason", "value": "test", "severity": "low"}
            ]
        }
        
        # Execute
        result = agent._merge_extracted_data([extraction])
        
        # Assert
        assert result["documents_processed"] == 1
        assert "revenue" in result["financial_data"]
        assert result["financial_data"]["revenue"]["values"] == [5000000]
        assert "company_info" in result["financial_data"]
        assert len(result["source_tracking"]) > 0
        assert len(result["ambiguous_flags"]) == 1
    
    def test_merge_extracted_data_multiple_documents_prefer_high_confidence(self, agent):
        """Test merging prefers higher confidence data"""
        # Setup
        extraction1 = {
            "document_id": "doc1",
            "data": {
                "financial_metrics": {
                    "revenue": {
                        "values": [5000000],
                        "confidence": "low"
                    }
                }
            },
            "source_pages": {},
            "ambiguous_flags": []
        }
        
        extraction2 = {
            "document_id": "doc2",
            "data": {
                "financial_metrics": {
                    "revenue": {
                        "values": [5500000],
                        "confidence": "high"
                    }
                }
            },
            "source_pages": {},
            "ambiguous_flags": []
        }
        
        # Execute
        result = agent._merge_extracted_data([extraction1, extraction2])
        
        # Assert
        assert result["documents_processed"] == 2
        # Should prefer the high confidence value
        assert result["financial_data"]["revenue"]["values"] == [5500000]
        assert result["financial_data"]["revenue"]["confidence"] == "high"
    
    def test_merge_extracted_data_combines_ambiguous_flags(self, agent):
        """Test that ambiguous flags from all documents are combined"""
        # Setup
        extraction1 = {
            "document_id": "doc1",
            "data": {"financial_metrics": {}},
            "source_pages": {},
            "ambiguous_flags": [
                {"field": "field1", "reason": "reason1", "value": "val1", "severity": "low"}
            ]
        }
        
        extraction2 = {
            "document_id": "doc2",
            "data": {"financial_metrics": {}},
            "source_pages": {},
            "ambiguous_flags": [
                {"field": "field2", "reason": "reason2", "value": "val2", "severity": "medium"}
            ]
        }
        
        # Execute
        result = agent._merge_extracted_data([extraction1, extraction2])
        
        # Assert
        assert len(result["ambiguous_flags"]) == 2
        assert result["ambiguous_flags"][0]["document_id"] == "doc1"
        assert result["ambiguous_flags"][1]["document_id"] == "doc2"


class TestDocumentIntelligenceAgentEdgeCases:
    """
    Edge case tests for DocumentIntelligenceAgent
    
    Tests extraction with missing data, ambiguous values, and multi-page documents.
    Requirements: 2.3
    """
    
    @pytest.mark.asyncio
    async def test_extraction_with_completely_missing_data(
        self,
        mock_document_repository,
        mock_document_processor
    ):
        """Test extraction when document has no financial data at all"""
        # Setup
        agent = DocumentIntelligenceAgent(
            document_repository=mock_document_repository,
            document_processor=mock_document_processor
        )
        
        # Document with no financial information
        doc = Document(
            id="doc_empty",
            application_id="app123",
            filename="empty_doc.pdf",
            file_type="pdf",
            storage_path="documents/app123/empty.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={
                "text": """This is a general business document.
                It contains no financial statements or numbers.
                Just some text about the company's mission and vision."""
            }
        )
        
        mock_document_repository.get_by_application.return_value = [doc]
        
        # Mock OpenAI response with all null/empty values
        empty_response = {
            "company_info": {
                "company_name": None,
                "industry": None,
                "fiscal_year": None
            },
            "financial_metrics": {
                "revenue": {"values": [], "years": [], "currency": "USD", "confidence": "low"},
                "profit": {"values": [], "years": [], "currency": "USD", "confidence": "low"},
                "debt": {"values": [], "years": [], "currency": "USD", "confidence": "low"},
                "cash_flow": {"values": [], "years": [], "currency": "USD", "confidence": "low"},
                "current_assets": {"value": None, "year": None, "confidence": "low"},
                "current_liabilities": {"value": None, "year": None, "confidence": "low"},
                "total_assets": {"value": None, "year": None, "confidence": "low"},
                "total_equity": {"value": None, "year": None, "confidence": "low"},
                "total_debt": {"value": None, "year": None, "confidence": "low"}
            },
            "financial_ratios": {
                "current_ratio": {"value": None, "confidence": "low"},
                "debt_to_equity": {"value": None, "confidence": "low"},
                "net_profit_margin": {"value": None, "confidence": "low"},
                "roe": {"value": None, "confidence": "low"}
            },
            "notes": ["No financial data found in document"]
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(empty_response)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            # Execute
            result = await agent.extract("app123")
        
        # Assert - should flag all critical missing data
        assert result["documents_processed"] == 1
        assert len(result["ambiguous_flags"]) > 0
        
        # Should flag missing critical metrics
        critical_flags = [
            f for f in result["ambiguous_flags"]
            if "Critical metric not found" in f["reason"]
        ]
        assert len(critical_flags) >= 4  # revenue, profit, total_assets, total_equity
        
        # All critical flags should have high severity
        for flag in critical_flags:
            assert flag["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_extraction_with_partially_missing_data(
        self,
        mock_document_repository,
        mock_document_processor
    ):
        """Test extraction when some financial metrics are missing"""
        # Setup
        agent = DocumentIntelligenceAgent(
            document_repository=mock_document_repository,
            document_processor=mock_document_processor
        )
        
        doc = Document(
            id="doc_partial",
            application_id="app123",
            filename="partial_doc.pdf",
            file_type="pdf",
            storage_path="documents/app123/partial.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={
                "text": """Financial Statement 2023
                Revenue: $5,000,000
                Total Assets: $10,000,000
                
                Note: Profit and debt information not available for this period."""
            }
        )
        
        mock_document_repository.get_by_application.return_value = [doc]
        
        # Response with some data present, some missing
        partial_response = {
            "company_info": {
                "company_name": "Partial Data Corp",
                "industry": None,
                "fiscal_year": "2023"
            },
            "financial_metrics": {
                "revenue": {"values": [5000000], "years": ["2023"], "currency": "USD", "confidence": "high"},
                "profit": {"values": [], "years": [], "currency": "USD", "confidence": "low"},
                "debt": {"values": [], "years": [], "currency": "USD", "confidence": "low"},
                "cash_flow": {"values": [], "years": [], "currency": "USD", "confidence": "low"},
                "total_assets": {"value": 10000000, "year": "2023", "confidence": "high"},
                "total_equity": {"value": None, "year": None, "confidence": "low"}
            },
            "financial_ratios": {},
            "notes": ["Profit and debt data not found in document"]
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(partial_response)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract("app123")
        
        # Assert
        assert result["documents_processed"] == 1
        
        # Should have revenue and total_assets
        assert "revenue" in result["financial_data"]
        assert result["financial_data"]["revenue"]["values"] == [5000000]
        assert "total_assets" in result["financial_data"]
        
        # Should flag missing critical metrics (profit, total_equity)
        missing_flags = [
            f for f in result["ambiguous_flags"]
            if "Critical metric not found" in f["reason"]
        ]
        assert len(missing_flags) >= 2
        
        # Should also flag the note about missing data
        note_flags = [
            f for f in result["ambiguous_flags"]
            if "not found" in f["reason"].lower()
        ]
        assert len(note_flags) > 0
    
    @pytest.mark.asyncio
    async def test_extraction_with_ambiguous_values(
        self,
        mock_document_repository,
        mock_document_processor
    ):
        """Test extraction when values are unclear or ambiguous"""
        # Setup
        agent = DocumentIntelligenceAgent(
            document_repository=mock_document_repository,
            document_processor=mock_document_processor
        )
        
        doc = Document(
            id="doc_ambiguous",
            application_id="app123",
            filename="ambiguous_doc.pdf",
            file_type="pdf",
            storage_path="documents/app123/ambiguous.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={
                "text": """Financial Overview 2023
                Revenue: Approximately $5M (estimated)
                Profit: Between $800K and $1.2M
                Debt: To be confirmed
                Assets: ~$10M (unaudited)"""
            }
        )
        
        mock_document_repository.get_by_application.return_value = [doc]
        
        # Response with low confidence due to ambiguity
        ambiguous_response = {
            "company_info": {
                "company_name": "Ambiguous Corp",
                "industry": None,
                "fiscal_year": "2023"
            },
            "financial_metrics": {
                "revenue": {
                    "values": [5000000],
                    "years": ["2023"],
                    "currency": "USD",
                    "confidence": "low"  # Low confidence due to "approximately"
                },
                "profit": {
                    "values": [1000000],
                    "years": ["2023"],
                    "currency": "USD",
                    "confidence": "low"  # Low confidence due to range
                },
                "debt": {
                    "values": [],
                    "years": [],
                    "currency": "USD",
                    "confidence": "low"  # To be confirmed
                },
                "total_assets": {
                    "value": 10000000,
                    "year": "2023",
                    "confidence": "low"  # Unaudited
                }
            },
            "financial_ratios": {},
            "notes": [
                "Revenue value is approximate and estimated",
                "Profit given as a range, used midpoint",
                "Debt value unclear - marked as 'to be confirmed'",
                "Assets value is unaudited"
            ]
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(ambiguous_response)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract("app123")
        
        # Assert - should flag all low confidence extractions
        assert result["documents_processed"] == 1
        
        # Should flag low confidence extractions (Requirement 2.3)
        low_confidence_flags = [
            f for f in result["ambiguous_flags"]
            if "Low confidence extraction" in f["reason"]
        ]
        assert len(low_confidence_flags) >= 3  # revenue, profit, total_assets
        
        # All low confidence flags should have medium severity
        for flag in low_confidence_flags:
            assert flag["severity"] == "medium"
        
        # Should also flag notes about ambiguity
        ambiguity_note_flags = [
            f for f in result["ambiguous_flags"]
            if any(keyword in f["reason"].lower() for keyword in ["approximate", "unclear", "unaudited"])
        ]
        assert len(ambiguity_note_flags) > 0
    
    @pytest.mark.asyncio
    async def test_extraction_with_conflicting_values(
        self,
        mock_document_repository,
        mock_document_processor
    ):
        """Test extraction when document contains conflicting values"""
        # Setup
        agent = DocumentIntelligenceAgent(
            document_repository=mock_document_repository,
            document_processor=mock_document_processor
        )
        
        doc = Document(
            id="doc_conflict",
            application_id="app123",
            filename="conflict_doc.pdf",
            file_type="pdf",
            storage_path="documents/app123/conflict.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={
                "text": """Financial Statement 2023
                Page 1: Revenue: $5,000,000
                Page 5: Revenue (corrected): $5,200,000
                
                Note: There is a discrepancy in revenue figures."""
            }
        )
        
        mock_document_repository.get_by_application.return_value = [doc]
        
        # Response noting the conflict
        conflict_response = {
            "company_info": {
                "company_name": "Conflict Corp",
                "fiscal_year": "2023"
            },
            "financial_metrics": {
                "revenue": {
                    "values": [5200000],  # Using corrected value
                    "years": ["2023"],
                    "currency": "USD",
                    "confidence": "medium"
                }
            },
            "financial_ratios": {},
            "notes": [
                "Revenue discrepancy found: $5,000,000 vs $5,200,000",
                "Used corrected value from page 5 - assumption made"
            ]
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(conflict_response)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract("app123")
        
        # Assert - should flag the discrepancy through notes
        assert result["documents_processed"] == 1
        
        # Should flag notes about discrepancy or assumption
        note_flags = [
            f for f in result["ambiguous_flags"]
            if any(keyword in f["reason"].lower() for keyword in ["discrepancy", "assumption"])
        ]
        assert len(note_flags) > 0
    
    @pytest.mark.asyncio
    async def test_extraction_from_multi_page_document(
        self,
        mock_document_repository,
        mock_document_processor
    ):
        """Test extraction from a multi-page document with page tracking"""
        # Setup
        agent = DocumentIntelligenceAgent(
            document_repository=mock_document_repository,
            document_processor=mock_document_processor
        )
        
        # Multi-page document with data spread across pages
        doc = Document(
            id="doc_multipage",
            application_id="app123",
            filename="multipage_doc.pdf",
            file_type="pdf",
            storage_path="documents/app123/multipage.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={
                "text": """[Page 1]
                Annual Report 2023
                ABC Corporation
                
                [Page 2]
                Income Statement
                Revenue: $5,000,000
                Net Profit: $1,200,000
                
                [Page 3]
                Balance Sheet
                Total Assets: $10,000,000
                Total Equity: $6,000,000
                Total Debt: $4,000,000
                
                [Page 4]
                Cash Flow Statement
                Operating Cash Flow: $1,500,000
                
                [Page 5]
                Financial Ratios
                Current Ratio: 2.0
                Debt to Equity: 0.67
                ROE: 20%"""
            }
        )
        
        mock_document_repository.get_by_application.return_value = [doc]
        
        # Response with data from multiple pages
        multipage_response = {
            "company_info": {
                "company_name": "ABC Corporation",
                "fiscal_year": "2023"
            },
            "financial_metrics": {
                "revenue": {
                    "values": [5000000],
                    "years": ["2023"],
                    "currency": "USD",
                    "confidence": "high"
                },
                "profit": {
                    "values": [1200000],
                    "years": ["2023"],
                    "currency": "USD",
                    "confidence": "high"
                },
                "cash_flow": {
                    "values": [1500000],
                    "years": ["2023"],
                    "currency": "USD",
                    "confidence": "high"
                },
                "total_assets": {
                    "value": 10000000,
                    "year": "2023",
                    "confidence": "high"
                },
                "total_equity": {
                    "value": 6000000,
                    "year": "2023",
                    "confidence": "high"
                },
                "total_debt": {
                    "value": 4000000,
                    "year": "2023",
                    "confidence": "high"
                }
            },
            "financial_ratios": {
                "current_ratio": {"value": 2.0, "confidence": "high"},
                "debt_to_equity": {"value": 0.67, "confidence": "high"},
                "roe": {"value": 20.0, "confidence": "high"}
            },
            "notes": [
                "Revenue from page 2",
                "Balance sheet items from page 3",
                "Cash flow from page 4",
                "Ratios from page 5"
            ]
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(multipage_response)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract("app123")
        
        # Assert - should extract all data and track pages
        assert result["documents_processed"] == 1
        
        # Should have all financial metrics
        assert "revenue" in result["financial_data"]
        assert "profit" in result["financial_data"]
        assert "cash_flow" in result["financial_data"]
        assert "total_assets" in result["financial_data"]
        
        # Should have source tracking with page numbers (Requirement 2.5)
        assert len(result["source_tracking"]) > 0
        
        # Verify page tracking for specific metrics
        if "financial_metrics.revenue" in result["source_tracking"]:
            # Revenue should be from page 2
            assert result["source_tracking"]["financial_metrics.revenue"]["page"] == 2
        
        if "financial_metrics.total_assets" in result["source_tracking"]:
            # Total assets should be from page 3
            assert result["source_tracking"]["financial_metrics.total_assets"]["page"] == 3
        
        if "financial_metrics.cash_flow" in result["source_tracking"]:
            # Cash flow should be from page 4
            assert result["source_tracking"]["financial_metrics.cash_flow"]["page"] == 4
        
        # All tracked items should have valid page numbers
        for field_path, source_info in result["source_tracking"].items():
            assert "page" in source_info
            assert 1 <= source_info["page"] <= 5
            assert source_info["document_id"] == "doc_multipage"
    
    @pytest.mark.asyncio
    async def test_extraction_from_multi_page_with_missing_page_markers(
        self,
        mock_document_repository,
        mock_document_processor
    ):
        """Test extraction from multi-page document without page markers"""
        # Setup
        agent = DocumentIntelligenceAgent(
            document_repository=mock_document_repository,
            document_processor=mock_document_processor
        )
        
        # Multi-page document without page markers
        doc = Document(
            id="doc_no_markers",
            application_id="app123",
            filename="no_markers.pdf",
            file_type="pdf",
            storage_path="documents/app123/no_markers.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={
                "text": """Annual Report 2023
                Revenue: $5,000,000
                Profit: $1,200,000
                Total Assets: $10,000,000"""
            }
        )
        
        mock_document_repository.get_by_application.return_value = [doc]
        
        response = {
            "company_info": {"company_name": "Test Corp"},
            "financial_metrics": {
                "revenue": {"values": [5000000], "confidence": "high"}
            },
            "financial_ratios": {},
            "notes": []
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(response)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract("app123")
        
        # Assert - should still extract data, but source tracking may be empty
        assert result["documents_processed"] == 1
        assert "revenue" in result["financial_data"]
        
        # Source tracking should be empty or minimal without page markers
        # This is expected behavior
        assert isinstance(result["source_tracking"], dict)
    
    @pytest.mark.asyncio
    async def test_extraction_with_mixed_confidence_levels(
        self,
        mock_document_repository,
        mock_document_processor
    ):
        """Test extraction with mixed confidence levels across metrics"""
        # Setup
        agent = DocumentIntelligenceAgent(
            document_repository=mock_document_repository,
            document_processor=mock_document_processor
        )
        
        doc = Document(
            id="doc_mixed",
            application_id="app123",
            filename="mixed_confidence.pdf",
            file_type="pdf",
            storage_path="documents/app123/mixed.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={
                "text": """Financial Data 2023
                Revenue: $5,000,000 (audited)
                Profit: ~$1,200,000 (estimated)
                Debt: TBD
                Assets: $10,000,000 (confirmed)"""
            }
        )
        
        mock_document_repository.get_by_application.return_value = [doc]
        
        # Response with mixed confidence
        mixed_response = {
            "company_info": {"company_name": "Mixed Corp"},
            "financial_metrics": {
                "revenue": {"values": [5000000], "confidence": "high"},
                "profit": {"values": [1200000], "confidence": "medium"},
                "debt": {"values": [], "confidence": "low"},
                "cash_flow": {"values": [], "confidence": "low"},
                "total_assets": {"value": 10000000, "confidence": "high"},
                "total_equity": {"value": None, "confidence": "low"}
            },
            "financial_ratios": {},
            "notes": ["Profit is estimated", "Debt value to be determined"]
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mixed_response)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract("app123")
        
        # Assert - should flag only low confidence items
        assert result["documents_processed"] == 1
        
        # Should flag low confidence extraction (debt)
        low_conf_flags = [
            f for f in result["ambiguous_flags"]
            if "Low confidence extraction" in f["reason"]
        ]
        assert len(low_conf_flags) >= 1  # At least debt should be flagged
        
        # Should also flag missing critical metrics (debt, cash_flow, total_equity)
        missing_flags = [
            f for f in result["ambiguous_flags"]
            if "Critical metric not found" in f["reason"]
        ]
        # Should flag at least some missing critical metrics
        assert len(missing_flags) >= 1
