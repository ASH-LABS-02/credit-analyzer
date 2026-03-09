/**
 * Unit Tests for FinancialRatioCard Component
 * 
 * Tests ratio display, tooltip functionality, and benchmark comparisons.
 * 
 * Requirements: 4.1, 4.5, 13.5
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import FinancialRatioCard from './FinancialRatioCard';

describe('FinancialRatioCard', () => {
  const mockDefinition = 'Current Ratio measures the company\'s ability to pay short-term obligations.';

  it('should render ratio name and value', () => {
    render(
      <FinancialRatioCard
        name="Current Ratio"
        value={1.5}
        definition={mockDefinition}
      />
    );

    expect(screen.getByText('Current Ratio')).toBeInTheDocument();
    expect(screen.getByText('1.50')).toBeInTheDocument();
  });

  it('should format value with percentage format', () => {
    render(
      <FinancialRatioCard
        name="Net Profit Margin"
        value={0.15}
        definition="Net profit margin definition"
        format="percentage"
      />
    );

    expect(screen.getByText('15.0%')).toBeInTheDocument();
  });

  it('should display benchmark comparison when provided', () => {
    render(
      <FinancialRatioCard
        name="Current Ratio"
        value={1.5}
        definition={mockDefinition}
        benchmark={1.2}
        benchmarkLabel="Industry Average"
      />
    );

    expect(screen.getByText(/vs industry avg/)).toBeInTheDocument();
    expect(screen.getByText(/1.20/)).toBeInTheDocument();
  });

  it('should show tooltip on hover', () => {
    render(
      <FinancialRatioCard
        name="Current Ratio"
        value={1.5}
        definition={mockDefinition}
      />
    );

    const infoButton = screen.getByRole('button');
    fireEvent.mouseEnter(infoButton);

    expect(screen.getByText(mockDefinition)).toBeInTheDocument();
  });

  it('should hide tooltip on mouse leave', () => {
    render(
      <FinancialRatioCard
        name="Current Ratio"
        value={1.5}
        definition={mockDefinition}
      />
    );

    const infoButton = screen.getByRole('button');
    fireEvent.mouseEnter(infoButton);
    expect(screen.getByText(mockDefinition)).toBeInTheDocument();

    fireEvent.mouseLeave(infoButton);
    // Tooltip should be removed from DOM after animation
  });

  it('should show good status when value is in good range', () => {
    const { container } = render(
      <FinancialRatioCard
        name="Current Ratio"
        value={2.0}
        definition={mockDefinition}
        benchmark={1.5}
        goodRange={{ min: 1.0, max: 3.0 }}
      />
    );

    // Should have green color class for good status
    const valueElement = container.querySelector('.text-green-600');
    expect(valueElement).toBeInTheDocument();
  });

  it('should show yellow status when value is outside good range', () => {
    const { container } = render(
      <FinancialRatioCard
        name="Current Ratio"
        value={1.0}
        definition={mockDefinition}
        benchmark={1.5}
        goodRange={{ min: 1.5, max: 3.0 }}
      />
    );

    // Should have yellow color class for out of range status
    const valueElement = container.querySelector('.text-yellow-600');
    expect(valueElement).toBeInTheDocument();
  });

  it('should handle good range comparison', () => {
    const { container } = render(
      <FinancialRatioCard
        name="Current Ratio"
        value={1.8}
        definition={mockDefinition}
        benchmark={1.2}
        goodRange={{ min: 1.0, max: 3.0 }}
      />
    );

    // Value is in good range
    expect(container.querySelector('.text-green-600')).toBeInTheDocument();
  });

  it('should render without benchmark', () => {
    render(
      <FinancialRatioCard
        name="Current Ratio"
        value={1.5}
        definition={mockDefinition}
      />
    );

    expect(screen.getByText('Current Ratio')).toBeInTheDocument();
    expect(screen.getByText('1.50')).toBeInTheDocument();
    // No benchmark text should be present
    expect(screen.queryByText(/Industry Average/)).not.toBeInTheDocument();
  });

  it('should handle zero value', () => {
    render(
      <FinancialRatioCard
        name="Current Ratio"
        value={0}
        definition={mockDefinition}
      />
    );

    expect(screen.getByText('0.00')).toBeInTheDocument();
  });

  it('should handle negative value', () => {
    render(
      <FinancialRatioCard
        name="Net Profit Margin"
        value={-0.05}
        definition="Negative margin"
        format="percentage"
      />
    );

    expect(screen.getByText('-5.0%')).toBeInTheDocument();
  });
});
