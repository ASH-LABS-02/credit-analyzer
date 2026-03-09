"""
Property-based tests for CAMGeneratorAgent

Feature: intelli-credit-platform
Property 15: CAM Document Structure Completeness

Validates: Requirements 7.1, 7.2, 7.5
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.cam_generator_agent import CAMGeneratorAgent
from app.models.domain import CAM


# Strategy for generating valid loan amounts
loan_amount_strategy = st.floats(
    min_value=100000.0,
    max_value=100000000.0,
    allow_nan=False,
    allow_infinity=False
)

# Strategy for generating credit scores (0-100)
credit_score_strategy = st.floats(
    min_value=0.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False
)

# Strategy for generating version numbers
version_strategy = st.integers(min_value=1, max_value=100)

# Strategy for generating company names
company_name_strategy = st.text(
    min_size=3,
    max_size=50,
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' &-.')
).filter(lambda x: x.strip() and not x.isspace())

# Strategy for generating loan purposes
loan_purpose_strategy = st.sampled_from([
    'Working capital',
    'Business expansion',
    'Equipment purchase',
    'Real estate acquisition',
    'Debt refinancing',
    'Inventory financing',
    'Technology upgrade',
    'Market expansion'
])

# Strategy for generating recommendations
recommendation_strategy = st.sampled_from(['approve', 'approve_with_conditions', 'reject'])


def create_analysis_data(
    application_id: str,
    company_name: str,
    loan_amount: float,
    loan_purpose: str,
    overall_score: float,
    recommendation: str,
    version: int
):
    """
    Helper function to create valid analysis data for CAM generation.
    
    This ensures we have properly structured data that the CAM generator expects.
    """
    return {
        'application_id': application_id,
        'company_name': company_name,
        'loan_amount': loan_amount,
        'loan_purpose': loan_purpose,
        'financial': {
            'ratios': {
                'current_ratio': {'value': 2.0, 'formatted_value': '2.00'},
                'debt_to_equity': {'value': 0.5, 'formatted_value': '0.50'},
                'roe': {'value': 0.15, 'formatted_value': '15.00%'},
                'net_profit_margin': {'value': 0.10, 'formatted_value': '10.00%'}
            },
            'benchmarks': {
                'current_ratio': {
                    'value': 2.0,
                    'benchmark_good': 1.5,
                    'performance': 'good'
                }
            },
            'trends': {
                'revenue': {
                    'trend_direction': 'increasing',
                    'cagr': 10.0,
                    'values': [1000000, 1100000, 1200000],
                    'interpretation': 'Positive growth trend'
                }
            },
            'summary': 'Financial analysis completed'
        },
        'forecasts': {
            'forecasts': {
                'revenue': {
                    'projected_values': [1300000, 1400000, 1500000],
                    'confidence_level': 0.75
                },
                'profit': {
                    'projected_values': [150000, 170000, 190000],
                    'confidence_level': 0.70
                }
            }
        },
        'risk': {
            'overall_score': overall_score,
            'recommendation': recommendation,
            'summary': f'Credit score: {overall_score:.1f}/100',
            'financial_health': {
                'score': overall_score,
                'weight': 0.35,
                'explanation': 'Financial health assessment',
                'key_findings': ['Strong ratios', 'Positive trends']
            },
            'cash_flow': {
                'score': overall_score,
                'weight': 0.25,
                'explanation': 'Cash flow assessment',
                'key_findings': ['Adequate liquidity']
            },
            'industry': {
                'score': overall_score,
                'weight': 0.15,
                'explanation': 'Industry assessment',
                'key_findings': ['Favorable outlook']
            },
            'promoter': {
                'score': overall_score,
                'weight': 0.15,
                'explanation': 'Promoter assessment',
                'key_findings': ['Experienced management']
            },
            'external_intelligence': {
                'score': overall_score,
                'weight': 0.10,
                'explanation': 'External intelligence assessment',
                'key_findings': ['Positive sentiment']
            }
        },
        'research': {
            'web': {
                'news_summary': 'Recent positive coverage',
                'market_sentiment': 'Positive'
            },
            'promoter': {
                'background': 'Experienced management team'
            },
            'industry': {
                'sector_outlook': 'Positive growth expected'
            }
        },
        'version': version
    }


class TestProperty15CAMDocumentStructureCompleteness:
    """
    Property 15: CAM Document Structure Completeness
    
    For any generated CAM, the document should include all required sections
    (executive summary, company overview, financial analysis, risk assessment,
    credit recommendation) with generation timestamp and version tracking.
    
    Validates: Requirements 7.1, 7.2, 7.5
    """
    
    @pytest.fixture(autouse=True)
    def setup_mock_openai(self):
        """Automatically mock OpenAI for all tests in this class."""
        with patch('app.agents.cam_generator_agent.AsyncOpenAI') as mock_client:
            # Create mock response object
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            
            # Set up the response chain
            mock_message.content = "Generated content from OpenAI"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            
            # Mock the async create method
            mock_create = AsyncMock(return_value=mock_response)
            mock_client.return_value.chat.completions.create = mock_create
            
            yield mock_client
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy,
        loan_purpose=loan_purpose_strategy,
        overall_score=credit_score_strategy,
        recommendation=recommendation_strategy,
        version=version_strategy
    )
    async def test_cam_has_all_required_sections(
        self,
        company_name: str,
        loan_amount: float,
        loan_purpose: str,
        overall_score: float,
        recommendation: str,
        version: int
    ):
        """
        Property: Every generated CAM must contain all five required sections
        
        For any valid analysis data, the generated CAM should include:
        - executive_summary
        - company_overview
        - financial_analysis
        - risk_assessment
        - recommendation
        
        All sections must be non-empty strings.
        """
        agent = CAMGeneratorAgent()
        
        # Create analysis data with the generated parameters
        analysis_data = create_analysis_data(
            application_id=f'test-app-{version}',
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            overall_score=overall_score,
            recommendation=recommendation,
            version=version
        )
        
        # Generate CAM
        result = await agent.generate(analysis_data)
        
        # Verify result is a CAM object
        assert isinstance(result, CAM), \
            f"Expected CAM object, got {type(result)}"
        
        # Verify all required sections exist
        required_sections = [
            'executive_summary',
            'company_overview',
            'financial_analysis',
            'risk_assessment',
            'recommendation'
        ]
        
        for section_name in required_sections:
            assert section_name in result.sections, \
                f"Missing required section: {section_name}"
            
            section_content = result.sections[section_name]
            assert isinstance(section_content, str), \
                f"Section {section_name} should be a string, got {type(section_content)}"
            
            assert len(section_content) > 0, \
                f"Section {section_name} is empty"
            
            # Verify section content is not just whitespace
            assert section_content.strip(), \
                f"Section {section_name} contains only whitespace"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy,
        loan_purpose=loan_purpose_strategy,
        overall_score=credit_score_strategy,
        recommendation=recommendation_strategy,
        version=version_strategy
    )
    async def test_cam_has_generation_timestamp(
        self,
        company_name: str,
        loan_amount: float,
        loan_purpose: str,
        overall_score: float,
        recommendation: str,
        version: int
    ):
        """
        Property: Every generated CAM must have a generation timestamp
        
        For any generated CAM, the generated_at field should:
        - Be a datetime object
        - Be close to the current time (within 1 minute)
        - Be included in the CAM content
        """
        agent = CAMGeneratorAgent()
        
        # Record time before generation
        time_before = datetime.utcnow()
        
        # Create analysis data
        analysis_data = create_analysis_data(
            application_id=f'test-app-{version}',
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            overall_score=overall_score,
            recommendation=recommendation,
            version=version
        )
        
        # Generate CAM
        result = await agent.generate(analysis_data)
        
        # Record time after generation
        time_after = datetime.utcnow()
        
        # Verify generated_at exists and is a datetime
        assert hasattr(result, 'generated_at'), \
            "CAM missing generated_at attribute"
        assert isinstance(result.generated_at, datetime), \
            f"generated_at should be datetime, got {type(result.generated_at)}"
        
        # Verify timestamp is reasonable (within 1 minute of generation)
        time_diff = (time_after - result.generated_at).total_seconds()
        assert -60 <= time_diff <= 60, \
            f"Timestamp {result.generated_at} is not close to current time (diff: {time_diff}s)"
        
        # Verify timestamp is included in content
        assert 'Generated:' in result.content or 'generated:' in result.content.lower(), \
            "CAM content should include generation timestamp"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy,
        loan_purpose=loan_purpose_strategy,
        overall_score=credit_score_strategy,
        recommendation=recommendation_strategy,
        version=version_strategy
    )
    async def test_cam_has_version_tracking(
        self,
        company_name: str,
        loan_amount: float,
        loan_purpose: str,
        overall_score: float,
        recommendation: str,
        version: int
    ):
        """
        Property: Every generated CAM must have version tracking
        
        For any generated CAM, the version field should:
        - Match the input version number
        - Be a positive integer
        - Be included in the CAM content
        """
        agent = CAMGeneratorAgent()
        
        # Create analysis data
        analysis_data = create_analysis_data(
            application_id=f'test-app-{version}',
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            overall_score=overall_score,
            recommendation=recommendation,
            version=version
        )
        
        # Generate CAM
        result = await agent.generate(analysis_data)
        
        # Verify version exists and matches input
        assert hasattr(result, 'version'), \
            "CAM missing version attribute"
        assert result.version == version, \
            f"CAM version {result.version} doesn't match input version {version}"
        
        # Verify version is a positive integer
        assert isinstance(result.version, int), \
            f"Version should be int, got {type(result.version)}"
        assert result.version > 0, \
            f"Version should be positive, got {result.version}"
        
        # Verify version is included in content
        version_str = str(version)
        assert f'Version: {version_str}' in result.content or \
               f'version: {version_str}' in result.content.lower() or \
               f'Version {version_str}' in result.content or \
               f'version {version_str}' in result.content.lower(), \
            f"CAM content should include version number {version}"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy,
        loan_purpose=loan_purpose_strategy,
        overall_score=credit_score_strategy,
        recommendation=recommendation_strategy,
        version=version_strategy
    )
    async def test_cam_content_includes_key_information(
        self,
        company_name: str,
        loan_amount: float,
        loan_purpose: str,
        overall_score: float,
        recommendation: str,
        version: int
    ):
        """
        Property: CAM content must include key application information
        
        For any generated CAM, the content should include:
        - Company name
        - Loan amount
        - Credit score
        - Recommendation
        """
        agent = CAMGeneratorAgent()
        
        # Create analysis data
        analysis_data = create_analysis_data(
            application_id=f'test-app-{version}',
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            overall_score=overall_score,
            recommendation=recommendation,
            version=version
        )
        
        # Generate CAM
        result = await agent.generate(analysis_data)
        
        # Verify company name is in content
        assert company_name in result.content, \
            f"CAM content should include company name '{company_name}'"
        
        # Verify loan amount is in content (formatted with commas or as number)
        # The loan amount might be formatted in various ways, so check for the base number
        loan_amount_int = int(loan_amount)
        loan_amount_formatted = f"{loan_amount:,.2f}"
        loan_amount_no_decimal = f"{loan_amount_int:,}"
        
        # Check if any reasonable representation of the loan amount is in the content
        assert (
            str(loan_amount_int) in result.content or
            loan_amount_formatted in result.content or
            loan_amount_no_decimal in result.content or
            f"${loan_amount:,.2f}" in result.content or
            f"${loan_amount_int:,}" in result.content
        ), f"CAM content should include loan amount {loan_amount}"
        
        # Verify credit score is in content
        score_str = f"{overall_score:.1f}"
        score_int = f"{int(overall_score)}"
        assert score_str in result.content or score_int in result.content, \
            f"CAM content should include credit score {overall_score}"
        
        # Verify recommendation is in content
        rec_variations = [
            recommendation,
            recommendation.replace('_', ' '),
            recommendation.upper(),
            recommendation.replace('_', ' ').upper(),
            recommendation.replace('_', ' ').title()
        ]
        assert any(rec in result.content for rec in rec_variations), \
            f"CAM content should include recommendation '{recommendation}'"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy,
        loan_purpose=loan_purpose_strategy,
        overall_score=credit_score_strategy,
        recommendation=recommendation_strategy,
        version=version_strategy
    )
    async def test_cam_application_id_matches(
        self,
        company_name: str,
        loan_amount: float,
        loan_purpose: str,
        overall_score: float,
        recommendation: str,
        version: int
    ):
        """
        Property: CAM application_id must match input application_id
        
        For any generated CAM, the application_id field should exactly match
        the application_id provided in the analysis data.
        """
        agent = CAMGeneratorAgent()
        
        # Create unique application ID
        application_id = f'test-app-{version}-{int(loan_amount)}'
        
        # Create analysis data
        analysis_data = create_analysis_data(
            application_id=application_id,
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            overall_score=overall_score,
            recommendation=recommendation,
            version=version
        )
        
        # Generate CAM
        result = await agent.generate(analysis_data)
        
        # Verify application_id matches
        assert hasattr(result, 'application_id'), \
            "CAM missing application_id attribute"
        assert result.application_id == application_id, \
            f"CAM application_id '{result.application_id}' doesn't match input '{application_id}'"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy,
        loan_purpose=loan_purpose_strategy,
        overall_score=credit_score_strategy,
        recommendation=recommendation_strategy,
        version=version_strategy
    )
    async def test_cam_sections_dictionary_completeness(
        self,
        company_name: str,
        loan_amount: float,
        loan_purpose: str,
        overall_score: float,
        recommendation: str,
        version: int
    ):
        """
        Property: CAM sections dictionary must be complete and accessible
        
        For any generated CAM, the sections dictionary should:
        - Contain exactly 5 sections
        - Have all required section keys
        - Allow direct access to each section
        """
        agent = CAMGeneratorAgent()
        
        # Create analysis data
        analysis_data = create_analysis_data(
            application_id=f'test-app-{version}',
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            overall_score=overall_score,
            recommendation=recommendation,
            version=version
        )
        
        # Generate CAM
        result = await agent.generate(analysis_data)
        
        # Verify sections is a dictionary
        assert isinstance(result.sections, dict), \
            f"sections should be a dict, got {type(result.sections)}"
        
        # Verify exactly 5 sections
        assert len(result.sections) == 5, \
            f"Expected 5 sections, got {len(result.sections)}"
        
        # Verify all required keys exist
        required_keys = {
            'executive_summary',
            'company_overview',
            'financial_analysis',
            'risk_assessment',
            'recommendation'
        }
        actual_keys = set(result.sections.keys())
        assert actual_keys == required_keys, \
            f"Section keys mismatch. Expected {required_keys}, got {actual_keys}"
        
        # Verify each section is directly accessible
        for key in required_keys:
            section_content = result.sections[key]
            assert section_content is not None, \
                f"Section '{key}' is None"
            assert isinstance(section_content, str), \
                f"Section '{key}' should be string, got {type(section_content)}"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=10)
    @given(
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy,
        loan_purpose=loan_purpose_strategy,
        overall_score=credit_score_strategy,
        recommendation=recommendation_strategy,
        version=version_strategy
    )
    async def test_cam_content_is_complete_document(
        self,
        company_name: str,
        loan_amount: float,
        loan_purpose: str,
        overall_score: float,
        recommendation: str,
        version: int
    ):
        """
        Property: CAM content must be a complete, well-formed document
        
        For any generated CAM, the content field should:
        - Be a non-empty string
        - Include all section content
        - Be properly formatted (contain markdown headers)
        - Be substantially longer than any individual section
        """
        agent = CAMGeneratorAgent()
        
        # Create analysis data
        analysis_data = create_analysis_data(
            application_id=f'test-app-{version}',
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            overall_score=overall_score,
            recommendation=recommendation,
            version=version
        )
        
        # Generate CAM
        result = await agent.generate(analysis_data)
        
        # Verify content exists and is non-empty
        assert hasattr(result, 'content'), \
            "CAM missing content attribute"
        assert isinstance(result.content, str), \
            f"content should be string, got {type(result.content)}"
        assert len(result.content) > 0, \
            "CAM content is empty"
        assert result.content.strip(), \
            "CAM content contains only whitespace"
        
        # Verify content includes markdown headers (indicating structure)
        assert '#' in result.content, \
            "CAM content should include markdown headers"
        
        # Verify content is longer than any individual section
        # (indicating it's a compiled document, not just one section)
        max_section_length = max(len(section) for section in result.sections.values())
        assert len(result.content) > max_section_length, \
            "CAM content should be longer than any individual section"
        
        # Verify all sections are included in the content
        for section_name, section_content in result.sections.items():
            # Check if a substantial portion of the section is in the content
            # (allowing for some formatting differences)
            section_preview = section_content[:100].strip()
            if section_preview:
                # At least some part of each section should be in the content
                assert any(
                    phrase in result.content 
                    for phrase in section_preview.split()[:5]
                ), f"Section '{section_name}' content not found in CAM"
