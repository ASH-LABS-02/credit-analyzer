/**
 * Tests for Risk Assessment, CAM, Monitoring, and Progress components
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import RiskAssessmentTab from '../components/RiskAssessmentTab';
import CAMTab from '../components/CAMTab';
import ProgressIndicator from '../components/ProgressIndicator';

describe('RiskAssessmentTab', () => {
  it('renders loading state', () => {
    const { container } = render(<RiskAssessmentTab application={null} analysisResults={null} loading={true} />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('renders credit score', () => {
    const app = { credit_score: 78, recommendation: 'approve' };
    render(<RiskAssessmentTab application={app} analysisResults={{}} loading={false} />);
    expect(screen.getByText('78')).toBeInTheDocument();
  });
});

describe('CAMTab', () => {
  it('renders CAM sections', () => {
    render(<CAMTab applicationId="test-123" />);
    expect(screen.getByText('Credit Appraisal Memo')).toBeInTheDocument();
    expect(screen.getByText('Executive Summary')).toBeInTheDocument();
  });
});

describe('ProgressIndicator', () => {
  it('renders progress bar', () => {
    render(<ProgressIndicator stage="Financial Analysis" progress={50} />);
    expect(screen.getAllByText('Financial Analysis')[0]).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });
});
