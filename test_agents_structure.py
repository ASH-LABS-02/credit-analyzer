"""
Structure test for PromoterIntelligenceAgent and IndustryIntelligenceAgent.
Tests that the classes are properly defined without making API calls.
"""

import sys
import os

# Set dummy environment variables before importing anything
os.environ['OPENAI_API_KEY'] = 'test-key-for-structure-test'
os.environ['FIREBASE_PROJECT_ID'] = 'test-project'
os.environ['FIREBASE_PRIVATE_KEY'] = 'test-key'
os.environ['FIREBASE_CLIENT_EMAIL'] = 'test@test.com'
os.environ['FIREBASE_STORAGE_BUCKET'] = 'test-bucket'

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_promoter_agent_structure():
    """Test PromoterIntelligenceAgent structure."""
    print("\n" + "="*60)
    print("Testing PromoterIntelligenceAgent Structure")
    print("="*60)
    
    from app.agents.promoter_intelligence_agent import PromoterIntelligenceAgent
    
    # Check class exists
    assert PromoterIntelligenceAgent is not None, "PromoterIntelligenceAgent class not found"
    print("✓ Class definition found")
    
    # Check class attributes
    assert hasattr(PromoterIntelligenceAgent, 'PROMOTER_RED_FLAGS'), "Missing PROMOTER_RED_FLAGS"
    assert hasattr(PromoterIntelligenceAgent, 'PROMOTER_POSITIVE_INDICATORS'), "Missing PROMOTER_POSITIVE_INDICATORS"
    print("✓ Class attributes defined")
    
    # Check required methods
    required_methods = [
        'analyze',
        '_identify_key_management',
        '_research_promoter_backgrounds',
        '_analyze_track_records',
        '_identify_conflicts_of_interest',
        '_identify_promoter_red_flags',
        '_identify_promoter_strengths',
        '_generate_overall_assessment',
        '_generate_promoter_summary',
        '_empty_analysis_result'
    ]
    
    for method in required_methods:
        assert hasattr(PromoterIntelligenceAgent, method), f"Missing method: {method}"
    print(f"✓ All {len(required_methods)} required methods defined")
    
    # Check docstring
    assert PromoterIntelligenceAgent.__doc__ is not None, "Missing class docstring"
    assert "Requirements: 3.3" in PromoterIntelligenceAgent.__doc__, "Missing requirements reference"
    print("✓ Documentation present")
    
    print("\n✓ PromoterIntelligenceAgent structure test PASSED!")
    return True


def test_industry_agent_structure():
    """Test IndustryIntelligenceAgent structure."""
    print("\n" + "="*60)
    print("Testing IndustryIntelligenceAgent Structure")
    print("="*60)
    
    from app.agents.industry_intelligence_agent import IndustryIntelligenceAgent
    
    # Check class exists
    assert IndustryIntelligenceAgent is not None, "IndustryIntelligenceAgent class not found"
    print("✓ Class definition found")
    
    # Check class attributes
    assert hasattr(IndustryIntelligenceAgent, 'INDUSTRY_RISK_KEYWORDS'), "Missing INDUSTRY_RISK_KEYWORDS"
    assert hasattr(IndustryIntelligenceAgent, 'INDUSTRY_POSITIVE_KEYWORDS'), "Missing INDUSTRY_POSITIVE_KEYWORDS"
    print("✓ Class attributes defined")
    
    # Check required methods
    required_methods = [
        'analyze',
        '_identify_industry',
        '_analyze_sector_trends',
        '_analyze_competitive_landscape',
        '_identify_industry_risks',
        '_identify_market_opportunities',
        '_assess_growth_outlook',
        '_generate_overall_assessment',
        '_generate_industry_summary',
        '_empty_analysis_result'
    ]
    
    for method in required_methods:
        assert hasattr(IndustryIntelligenceAgent, method), f"Missing method: {method}"
    print(f"✓ All {len(required_methods)} required methods defined")
    
    # Check docstring
    assert IndustryIntelligenceAgent.__doc__ is not None, "Missing class docstring"
    assert "Requirements: 3.4" in IndustryIntelligenceAgent.__doc__, "Missing requirements reference"
    print("✓ Documentation present")
    
    print("\n✓ IndustryIntelligenceAgent structure test PASSED!")
    return True


def test_agent_initialization():
    """Test that agents can be instantiated (without API calls)."""
    print("\n" + "="*60)
    print("Testing Agent Initialization")
    print("="*60)
    
    from app.agents.promoter_intelligence_agent import PromoterIntelligenceAgent
    from app.agents.industry_intelligence_agent import IndustryIntelligenceAgent
    
    # Test PromoterIntelligenceAgent initialization
    try:
        promoter_agent = PromoterIntelligenceAgent()
        assert promoter_agent is not None
        print("✓ PromoterIntelligenceAgent instantiated successfully")
    except Exception as e:
        print(f"✗ PromoterIntelligenceAgent initialization failed: {e}")
        return False
    
    # Test IndustryIntelligenceAgent initialization
    try:
        industry_agent = IndustryIntelligenceAgent()
        assert industry_agent is not None
        print("✓ IndustryIntelligenceAgent instantiated successfully")
    except Exception as e:
        print(f"✗ IndustryIntelligenceAgent initialization failed: {e}")
        return False
    
    print("\n✓ Agent initialization test PASSED!")
    return True


def main():
    """Run all structure tests."""
    print("\n" + "="*60)
    print("Research Agents Structure Test Suite")
    print("="*60)
    
    try:
        # Test PromoterIntelligenceAgent structure
        promoter_success = test_promoter_agent_structure()
        
        # Test IndustryIntelligenceAgent structure
        industry_success = test_industry_agent_structure()
        
        # Test agent initialization
        init_success = test_agent_initialization()
        
        # Summary
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        print(f"PromoterIntelligenceAgent Structure: {'✓ PASS' if promoter_success else '✗ FAIL'}")
        print(f"IndustryIntelligenceAgent Structure: {'✓ PASS' if industry_success else '✗ FAIL'}")
        print(f"Agent Initialization: {'✓ PASS' if init_success else '✗ FAIL'}")
        
        if promoter_success and industry_success and init_success:
            print("\n✓ All structure tests passed!")
            print("\nNote: Full functional tests require OpenAI API key configuration.")
            print("To run functional tests, configure .env file and run test_research_agents.py")
            return 0
        else:
            print("\n✗ Some tests failed")
            return 1
    
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
