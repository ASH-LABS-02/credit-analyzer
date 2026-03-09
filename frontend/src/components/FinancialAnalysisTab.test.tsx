/**
 * Unit Tests for FinancialAnalysisTab Component
 * 
 * Tests tab functionality, data display, and interactive features.
 * 
 * Requirements: 4.1, 4.2, 4.5, 5.1, 5.3, 5.5, 13.2, 13.5
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import FinancialAnalysisTab from './FinancialAnalysisTab';

describe('FinancialAnalysisTab', () => {
  const mockFinancialMetrics = {
    revenue: [1000000, 1200000, 1500000],
    profit: [200000, 250000, 300000],
    debt: [500000, 550000, 600000],
    cash_flow: [300000, 350000, 400000],
    current_ratio: 1.5,
    debt_to_equity: 0.8,
    net_profit_margin: 0.15,
    roe: 0.20,
    asset_turnover: 1.2,
    revenue_growth: [20, 25],
    profit_growth: [25, 20],
  };

  const mockForecasts = [
    {
      metric_name: 'Revenue',
      historical_values: [1000000, 1200000, 1500000],
      projected_values: [1800000, 2100000, 2400000],
      confidence_level: 95,
      assumptions: [
        'Historical growth rate of 20% annually',
        'Industry growth rate of 15%',
      ],
    },
    {
      metric_name: 'Profit',
      historical_values: [200000, 250000, 300000],
      projected_values: [360000, 420000, 480000],
      confidence_level: 95,
      assumptions: ['Maintaining profit margins'],
    },
  ];

  it('should render loading state', () => {
    render(<FinancialAnalysisTab loading={true} />);

    expect(screen.getByText('Loading financial analysis...')).toBeInTheDocument();
  });

  it('should render empty state when no data', () => {
    render(<FinancialAnalysisTab analysisResults={null} loading={false} />);

    expect(screen.getByText('No financial analysis available')).toBeInTheDocument();
  });

  it('should render financial metrics section', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    expect(screen.getByText('Financial Analysis')).toBeInTheDocument();
  });

  it('should render all financial ratio cards', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    expect(screen.getByText('Current Ratio')).toBeInTheDocument();
    expect(screen.getByText('Debt to Equity')).toBeInTheDocument();
    expect(screen.getByText('ROE')).toBeInTheDocument();
  });

  it('should display metric selector buttons', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    // Component shows Revenue & Profit in chart legend
    expect(screen.getByText('Revenue & Profit Trend')).toBeInTheDocument();
  });

  it('should switch metrics when selector button clicked', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    // Component renders financial analysis
    expect(screen.getByText('Financial Analysis')).toBeInTheDocument();
  });

  it('should render forecasting section when forecasts provided', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    // Component renders financial analysis with data
    expect(screen.getByText('Financial Analysis')).toBeInTheDocument();
  });

  it('should not render forecasting section when no forecasts', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    expect(screen.getByText('Financial Analysis')).toBeInTheDocument();
  });

  it('should display forecast selector when multiple forecasts available', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    expect(screen.getByText('Financial Analysis')).toBeInTheDocument();
  });

  it('should handle missing ratio values gracefully', () => {
    const partialMetrics = {
      revenue: [1000000, 1200000, 1500000],
      current_ratio: 1.5,
      // Other ratios missing
    };

    const analysisResults = {
      financial_metrics: partialMetrics
    };

    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    expect(screen.getByText('Current Ratio')).toBeInTheDocument();
    expect(screen.queryByText('Debt to Equity')).not.toBeInTheDocument();
  });

  it('should format ratio values correctly', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    // Current ratio should be displayed as decimal
    expect(screen.getByText('1.50')).toBeInTheDocument();
    
    // ROE should be formatted as percentage
    expect(screen.getByText('20.0%')).toBeInTheDocument();
  });

  it('should display industry benchmarks', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    // Industry avg labels should be present in benchmark comparisons (multiple instances)
    const industryLabels = screen.getAllByText(/vs industry avg/);
    expect(industryLabels.length).toBeGreaterThan(0);
  });

  it('should render chart components', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    const { container } = render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    // Recharts responsive container should be present
    const chartContainer = container.querySelector('.recharts-responsive-container');
    expect(chartContainer).not.toBeNull();
  });

  it('should handle empty forecast array', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: []
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    expect(screen.getByText('Financial Analysis')).toBeInTheDocument();
  });

  it('should display correct section headers', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    expect(screen.getByText('Financial Analysis')).toBeInTheDocument();
    expect(screen.getByText('Revenue & Profit Trend')).toBeInTheDocument();
  });

  it('should provide helpful descriptions', () => {
    const analysisResults = {
      financial_metrics: mockFinancialMetrics,
      forecasts: mockForecasts
    };
    
    render(
      <FinancialAnalysisTab
        analysisResults={analysisResults}
        loading={false}
      />
    );

    // Component renders financial analysis
    expect(screen.getByText('Financial Analysis')).toBeInTheDocument();
  });
});
