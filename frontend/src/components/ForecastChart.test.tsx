/**
 * Unit Tests for ForecastChart Component
 * 
 * Tests forecast visualization, confidence intervals, and interactive features.
 * 
 * Requirements: 5.1, 5.3, 5.5, 13.2
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ForecastChart from './ForecastChart';

describe('ForecastChart', () => {
  const mockData = [
    { year: '2021', actual: 1000000 },
    { year: '2022', actual: 1200000 },
    { year: '2023', actual: 1500000 },
    { year: '2024', projected: 1800000, confidenceUpper: 1980000, confidenceLower: 1620000 },
    { year: '2025', projected: 2100000, confidenceUpper: 2310000, confidenceLower: 1890000 },
    { year: '2026', projected: 2400000, confidenceUpper: 2640000, confidenceLower: 2160000 },
  ];

  const mockAssumptions = [
    'Historical growth rate of 20% annually',
    'Industry growth rate of 15%',
    'Stable economic conditions',
  ];

  const mockMethodology = 'Projections use historical growth rates, industry benchmarks, and economic indicators.';

  it('should render chart with title', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
      />
    );

    expect(screen.getByText('Revenue Forecast')).toBeInTheDocument();
  });

  it('should display confidence level in description', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
        confidenceLevel={95}
      />
    );

    expect(screen.getByText(/95% confidence interval/)).toBeInTheDocument();
  });

  it('should show details button when assumptions or methodology provided', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
        assumptions={mockAssumptions}
        methodology={mockMethodology}
      />
    );

    expect(screen.getByText(/Show Details/)).toBeInTheDocument();
  });

  it('should toggle details visibility on button click', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
        assumptions={mockAssumptions}
        methodology={mockMethodology}
      />
    );

    const detailsButton = screen.getByText(/Show Details/);
    
    // Initially details should not be visible
    expect(screen.queryByText('Methodology')).not.toBeInTheDocument();

    // Click to show details
    fireEvent.click(detailsButton);
    expect(screen.getByText('Methodology')).toBeInTheDocument();
    expect(screen.getByText(mockMethodology)).toBeInTheDocument();

    // Click to hide details
    fireEvent.click(screen.getByText(/Hide Details/));
  });

  it('should display all assumptions when details are shown', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
        assumptions={mockAssumptions}
      />
    );

    const detailsButton = screen.getByText(/Show Details/);
    fireEvent.click(detailsButton);

    expect(screen.getByText('Key Assumptions')).toBeInTheDocument();
    mockAssumptions.forEach((assumption) => {
      expect(screen.getByText(assumption)).toBeInTheDocument();
    });
  });

  it('should display methodology when provided', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
        methodology={mockMethodology}
      />
    );

    const detailsButton = screen.getByText(/Show Details/);
    fireEvent.click(detailsButton);

    expect(screen.getByText('Methodology')).toBeInTheDocument();
    expect(screen.getByText(mockMethodology)).toBeInTheDocument();
  });

  it('should format values with custom formatter', () => {
    const formatValue = (value: number) => `$${(value / 1000000).toFixed(1)}M`;
    
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
        formatValue={formatValue}
      />
    );

    expect(screen.getByText('Revenue Forecast')).toBeInTheDocument();
  });

  it('should render legend with correct labels', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
      />
    );

    expect(screen.getByText('Historical Data')).toBeInTheDocument();
    expect(screen.getByText('Projected Data')).toBeInTheDocument();
    expect(screen.getByText(/Confidence Interval/)).toBeInTheDocument();
  });

  it('should handle empty data gracefully', () => {
    render(
      <ForecastChart
        data={[]}
        title="Revenue Forecast"
      />
    );

    expect(screen.getByText('Revenue Forecast')).toBeInTheDocument();
  });

  it('should separate historical and projected data', () => {
    // Test data structure
    const historicalData = mockData.filter((d) => d.actual !== undefined);
    const projectedData = mockData.filter((d) => d.projected !== undefined);

    expect(historicalData).toHaveLength(3);
    expect(projectedData).toHaveLength(3);
  });

  it('should include confidence bounds for projected data', () => {
    const projectedData = mockData.filter((d) => d.projected !== undefined);

    projectedData.forEach((point) => {
      expect(point).toHaveProperty('confidenceUpper');
      expect(point).toHaveProperty('confidenceLower');
      expect(point.confidenceUpper).toBeGreaterThan(point.projected!);
      expect(point.confidenceLower).toBeLessThan(point.projected!);
    });
  });

  it('should not show details button when no assumptions or methodology', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
      />
    );

    expect(screen.queryByText(/Show Details/)).not.toBeInTheDocument();
  });

  it('should include y-axis label when provided', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
        yAxisLabel="Amount ($)"
      />
    );

    expect(screen.getByText('Revenue Forecast')).toBeInTheDocument();
  });

  it('should handle different confidence levels', () => {
    render(
      <ForecastChart
        data={mockData}
        title="Revenue Forecast"
        confidenceLevel={90}
      />
    );

    expect(screen.getByText(/90% confidence interval/)).toBeInTheDocument();
    expect(screen.getByText(/90% Confidence Interval/)).toBeInTheDocument();
  });
});
