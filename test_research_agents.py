"""
Quick test script to verify the PromoterIntelligenceAgent and IndustryIntelligenceAgent work correctly.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.agents.promoter_intelligence_agent import PromoterIntelligenceAgent
from app.agents.industry_intelligence_agent import IndustryIntelligenceAgent


async def test_promoter_agent():
    """Test PromoterIntelligenceAgent."""
    print("\n" + "="*60)
    print("Testing PromoterIntelligenceAgent")
    print("="*60)
    
    agent = PromoterIntelligenceAgent()
    
    # Test with a sample company
    result = await agent.analyze(
        company_name="TechCorp Industries",
        promoters=[
            {"name": "John Smith", "designation": "CEO", "tenure": "5 years"},
            {"name": "Jane Doe", "designation": "CFO", "tenure": "3 years"}
        ],
        additional_context={"industry": "Technology - Software"}
    )
    
    print(f"\nCompany: {result['company_name']}")
    print(f"Analysis Date: {result['analysis_date']}")
    print(f"\nPromoters Analyzed: {len(result['promoter_profiles'])}")
    
    for profile in result['promoter_profiles']:
        print(f"\n  - {profile['name']} ({profile['designation']})")
        print(f"    Experience: {profile.get('experience_years', 0)} years")
        print(f"    Education: {profile.get('education', 'N/A')}")
    
    print(f"\nTrack Record Rating: {result['track_record_analysis']['overall_rating']}")
    print(f"Red Flags: {len(result['red_flags'])}")
    print(f"Positive Indicators: {len(result['positive_indicators'])}")
    print(f"Conflicts of Interest: {len(result['conflicts_of_interest'])}")
    
    print(f"\nOverall Assessment:")
    print(f"  Rating: {result['overall_assessment']['rating']}")
    print(f"  Score: {result['overall_assessment']['score']}/100")
    print(f"  Recommendation: {result['overall_assessment']['recommendation']}")
    
    print(f"\nSummary:")
    print(f"  {result['summary'][:200]}...")
    
    print("\n✓ PromoterIntelligenceAgent test completed successfully!")
    return True


async def test_industry_agent():
    """Test IndustryIntelligenceAgent."""
    print("\n" + "="*60)
    print("Testing IndustryIntelligenceAgent")
    print("="*60)
    
    agent = IndustryIntelligenceAgent()
    
    # Test with a sample company
    result = await agent.analyze(
        company_name="TechCorp Industries",
        industry="Technology - Software",
        additional_context={"location": "United States"}
    )
    
    print(f"\nCompany: {result['company_name']}")
    print(f"Industry: {result['industry']}")
    print(f"Analysis Date: {result['analysis_date']}")
    
    print(f"\nSector Trends:")
    print(f"  Current State: {result['sector_trends']['current_state']}")
    print(f"  Outlook: {result['sector_trends']['outlook']}")
    print(f"  Economic Sensitivity: {result['sector_trends']['economic_sensitivity']}")
    print(f"  Key Trends: {len(result['sector_trends']['key_trends'])} identified")
    
    print(f"\nCompetitive Landscape:")
    print(f"  Market Structure: {result['competitive_landscape']['market_structure']}")
    print(f"  Competitive Intensity: {result['competitive_landscape']['competitive_intensity']}")
    print(f"  Barriers to Entry: {result['competitive_landscape']['barriers_to_entry']}")
    print(f"  Pricing Power: {result['competitive_landscape']['pricing_power']}")
    
    print(f"\nGrowth Outlook:")
    print(f"  Short-term: {result['growth_outlook']['short_term_growth']}")
    print(f"  Medium-term: {result['growth_outlook']['medium_term_growth']}")
    print(f"  Growth Quality: {result['growth_outlook']['growth_quality']}")
    print(f"  Confidence: {result['growth_outlook']['confidence_level']}")
    
    print(f"\nRisks & Opportunities:")
    print(f"  Industry Risks: {len(result['industry_risks'])} identified")
    print(f"  Market Opportunities: {len(result['market_opportunities'])} identified")
    
    print(f"\nOverall Assessment:")
    print(f"  Rating: {result['overall_assessment']['rating']}")
    print(f"  Score: {result['overall_assessment']['score']}/100")
    print(f"  Credit Implications: {result['overall_assessment']['credit_implications'][:100]}...")
    
    print(f"\nSummary:")
    print(f"  {result['summary'][:200]}...")
    
    print("\n✓ IndustryIntelligenceAgent test completed successfully!")
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Research Agents Test Suite")
    print("="*60)
    
    try:
        # Test PromoterIntelligenceAgent
        promoter_success = await test_promoter_agent()
        
        # Test IndustryIntelligenceAgent
        industry_success = await test_industry_agent()
        
        # Summary
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        print(f"PromoterIntelligenceAgent: {'✓ PASS' if promoter_success else '✗ FAIL'}")
        print(f"IndustryIntelligenceAgent: {'✓ PASS' if industry_success else '✗ FAIL'}")
        
        if promoter_success and industry_success:
            print("\n✓ All tests passed!")
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
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
