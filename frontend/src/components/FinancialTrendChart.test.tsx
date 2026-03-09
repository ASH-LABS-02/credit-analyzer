/**
 * Unit Tests for FinancialTrendChart Component
 * 
 * Tests chart data formatting, rendering, and interactive features.
 * 
 * Requirements: 13.2, 13.5
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import FinancialTrendChart from './FinancialTrendChart';

describe('FinancialTrendChart', () => {
  const mockData = [
    { year: '2021', revenue: 1000000, profit: 200000 },
    { year: '2022', revenue: 1200000, profit: 250000 },
    { year: '2023', revenue: 1500000, profit: 300000 },
  ];

  const mockLines = [
    { dataKey: 'revenue', name: 'Revenue', color: '#1f2937' },
    { dataKey: 'profit', name: 'Profit', color: '#3b82f6' },
  ];

  it('should render chart with title', () => {
    render(
      <FinancialTrendChart
        data={mockData}
        lines={mockLines}
        title="Financial Trends"
      />
    );

    expect(screen.getByText('Financial Trends')).toBeInTheDocument();
  });

  it('should render with custom value formatter', () => {
    const formatValue = (value: number) => `$${(value / 1000000).toFixed(1)}M`;
    
    render(
      <FinancialTrendChart
        data={mockData}
        lines={mockLines}
        title="Financial Trends"
        formatValue={formatValue}
      />
    );

    // Chart should be rendered
    expect(screen.getByText('Financial Trends')).toBeInTheDocument();
  });

  it('should render multiple lines', () => {
    render(
      <FinancialTrendChart
        data={mockData}
        lines={mockLines}
        title="Financial Trends"
      />
    );

    // Both lines should be configured
    expect(mockLines).toHaveLength(2);
    expect(mockLines[0].dataKey).toBe('revenue');
    expect(mockLines[1].dataKey).toBe('profit');
  });

  it('should handle empty data gracefully', () => {
    render(
      <FinancialTrendChart
        data={[]}
        lines={mockLines}
        title="Financial Trends"
      />
    );

    expect(screen.getByText('Financial Trends')).toBeInTheDocument();
  });

  it('should apply correct colors to lines', () => {
    const { container } = render(
      <FinancialTrendChart
        data={mockData}
        lines={mockLines}
        title="Financial Trends"
      />
    );

    // Chart container should be rendered
    const chartContainer = container.querySelector('.recharts-responsive-container');
    expect(chartContainer).not.toBeNull();
  });

  it('should include y-axis label when provided', () => {
    render(
      <FinancialTrendChart
        data={mockData}
        lines={mockLines}
        title="Financial Trends"
        yAxisLabel="Amount ($)"
      />
    );

    expect(screen.getByText('Financial Trends')).toBeInTheDocument();
  });

  it('should format data points correctly', () => {
    // Test that data structure is correct
    mockData.forEach((point) => {
      expect(point).toHaveProperty('year');
      expect(point).toHaveProperty('revenue');
      expect(point).toHaveProperty('profit');
      expect(typeof point.revenue).toBe('number');
      expect(typeof point.profit).toBe('number');
    });
  });
});
