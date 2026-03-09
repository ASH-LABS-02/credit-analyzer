/**
 * Unit Tests for Financial Analysis Components
 * Requirements: 13.2, 13.5
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import FinancialAnalysisTab from '../components/FinancialAnalysisTab';
import FinancialRatioCard from '../components/FinancialRatioCard';

describe('FinancialAnalysisTab', () => {
  const mockAnalysisResults = {
    financial_metrics: {
      current_ratio: 2.5,
      debt_to_equity: 0.8,
      roe: 0.15,
      historical_data: [
        { year: '2021', revenue: 4500000, profit: 450000 },
        { year: '2022', revenue: 5200000, profit: 580000 },
      ],
    },
  };

  it('renders loading state', () => {
    render(<FinancialAnalysisTab analysisResults={null} loading={true} />);
    expect(screen.getByText('Loading financial analysis...')).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    render(<FinancialAnalysisTab analysisResults={null} loading={false} />);
    expect(screen.getByText('No financial analysis available')).toBeInTheDocument();
  });

  it('renders financial ratios', () => {
    render(<FinancialAnalysisTab analysisResults={mockAnalysisResults} loading={false} />);
    expect(screen.getByText('Current Ratio')).toBeInTheDocument();
    expect(screen.getByText('2.50')).toBeInTheDocument();
  });
});

describe('FinancialRatioCard', () => {
  it('renders ratio name and value', () => {
    render(
      <FinancialRatioCard
        name="Current Ratio"
        value={2.5}
        definition="Test definition"
      />
    );
    expect(screen.getByText('Current Ratio')).toBeInTheDocument();
    expect(screen.getByText('2.50')).toBeInTheDocument();
  });

  it('formats percentage values', () => {
    render(
      <FinancialRatioCard
        name="ROE"
        value={0.15}
        definition="Test"
        format="percentage"
      />
    );
    expect(screen.getByText('15.0%')).toBeInTheDocument();
  });
});
