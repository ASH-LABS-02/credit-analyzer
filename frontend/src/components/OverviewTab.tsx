/**
 * OverviewTab Component
 * Enhanced overview with detailed metrics and attractive visualizations
 */

import { motion } from 'framer-motion';
import { 
  AlertCircle, 
  TrendingUp, 
  TrendingDown,
  DollarSign,
  Calendar,
  Building2,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3,
  Percent,
  Activity
} from 'lucide-react';
import { Application } from '../services/api';

interface OverviewTabProps {
  application: Application;
  analysisResults: any;
  analysisLoading: boolean;
  onRunAnalysis: () => void;
}

const OverviewTab: React.FC<OverviewTabProps> = ({
  application,
  analysisResults,
  analysisLoading,
  onRunAnalysis,
}) => {
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `₹${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `₹${(value / 1000).toFixed(2)}K`;
    }
    return `₹${value.toFixed(2)}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatStatus = (status: string) => {
    return status
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getRecommendationColor = (recommendation?: string) => {
    switch (recommendation) {
      case 'approve':
        return 'text-green-600';
      case 'approve_with_conditions':
        return 'text-yellow-600';
      case 'reject':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getRecommendationBg = (recommendation?: string) => {
    switch (recommendation) {
      case 'approve':
        return 'bg-green-50 border-green-200';
      case 'approve_with_conditions':
        return 'bg-yellow-50 border-yellow-200';
      case 'reject':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getRecommendationIcon = (recommendation?: string) => {
    switch (recommendation) {
      case 'approve':
        return <CheckCircle className="w-12 h-12 text-green-600" />;
      case 'approve_with_conditions':
        return <Clock className="w-12 h-12 text-yellow-600" />;
      case 'reject':
        return <XCircle className="w-12 h-12 text-red-600" />;
      default:
        return <AlertCircle className="w-12 h-12 text-gray-400" />;
    }
  };

  if (analysisLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-black mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading analysis results...</p>
        </div>
      </div>
    );
  }

  const hasAnalysis = application.credit_score !== undefined && application.credit_score !== null;

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-black mb-6">Application Overview</h2>

      {!hasAnalysis ? (
        <div className="text-center py-16 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
          <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-xl font-bold text-gray-700 mb-2">Analysis Not Yet Complete</p>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Upload documents and trigger analysis to see comprehensive credit assessment results
          </p>
          <button
            onClick={onRunAnalysis}
            disabled={analysisLoading}
            className="bg-black text-white px-8 py-3 text-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 rounded-lg shadow-lg"
          >
            {analysisLoading ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      ) : (
        <>
          {/* Company Information Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="border-2 border-gray-300 p-6 rounded-lg shadow-md bg-gradient-to-br from-white to-gray-50"
          >
            <div className="flex items-start gap-4 mb-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Building2 className="w-8 h-8 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-black mb-2">{application.company_name}</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-gray-500" />
                    <div>
                      <p className="text-gray-600 text-xs">Loan Amount</p>
                      <p className="font-bold text-black">{formatCurrency(application.loan_amount)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <div>
                      <p className="text-gray-600 text-xs">Applied On</p>
                      <p className="font-bold text-black">{formatDate(application.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-gray-500" />
                    <div>
                      <p className="text-gray-600 text-xs">Application ID</p>
                      <p className="font-bold text-black text-xs">{application.id.slice(0, 8)}...</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-gray-500" />
                    <div>
                      <p className="text-gray-600 text-xs">Status</p>
                      <p className="font-bold text-black">{formatStatus(application.status)}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Credit Score and Recommendation */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Credit Score Card */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="border-2 border-gray-300 p-8 rounded-lg shadow-lg bg-white"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-purple-100 p-3 rounded-lg">
                  <BarChart3 className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold text-black">Credit Score</h3>
              </div>
              
              <div className="flex items-end gap-3 mb-6">
                <p className="text-6xl font-bold text-black">{application.credit_score}</p>
                <p className="text-3xl text-gray-400 mb-2">/100</p>
              </div>

              {/* Score visualization bar */}
              <div className="mb-4">
                <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${application.credit_score}%` }}
                    transition={{ duration: 1.5, ease: 'easeOut' }}
                    className={`h-full ${
                      application.credit_score >= 70
                        ? 'bg-gradient-to-r from-green-400 to-green-600'
                        : application.credit_score >= 40
                        ? 'bg-gradient-to-r from-yellow-400 to-yellow-600'
                        : 'bg-gradient-to-r from-red-400 to-red-600'
                    }`}
                  />
                </div>
              </div>

              {/* Score interpretation */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Risk Level:</span>
                <span className={`font-bold ${
                  application.credit_score >= 70 ? 'text-green-600' :
                  application.credit_score >= 40 ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {application.credit_score >= 70 ? 'Low Risk' :
                   application.credit_score >= 40 ? 'Medium Risk' :
                   'High Risk'}
                </span>
              </div>
            </motion.div>

            {/* Recommendation Card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className={`border-2 p-8 rounded-lg shadow-lg ${getRecommendationBg(application.recommendation)}`}
            >
              <div className="flex items-center gap-3 mb-6">
                {getRecommendationIcon(application.recommendation)}
                <h3 className="text-xl font-bold text-black">Credit Decision</h3>
              </div>
              
              <p className={`text-4xl font-bold capitalize mb-4 ${getRecommendationColor(application.recommendation)}`}>
                {application.recommendation ? formatStatus(application.recommendation) : 'Pending'}
              </p>

              <p className="text-base text-gray-700 leading-relaxed">
                {application.recommendation === 'approve' && '✓ Application meets all credit criteria with strong financial indicators. Recommended for approval.'}
                {application.recommendation === 'approve_with_conditions' && '⚠ Conditional approval recommended. Some areas need monitoring or additional conditions.'}
                {application.recommendation === 'reject' && '✗ Application does not meet minimum credit criteria. Not recommended for approval.'}
                {!application.recommendation && 'Analysis in progress. Decision pending.'}
              </p>
            </motion.div>
          </div>

          {/* Key Financial Metrics */}
          {analysisResults?.financial_metrics && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="border-2 border-gray-300 p-6 rounded-lg shadow-md bg-white"
            >
              <h3 className="text-2xl font-bold text-black mb-6 flex items-center gap-2">
                <Percent className="w-6 h-6" />
                Key Financial Metrics
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Current Ratio */}
                {analysisResults.financial_metrics.current_ratio !== undefined && (
                  <div className="border-2 border-gray-200 p-5 rounded-lg hover:border-blue-400 transition-colors bg-gradient-to-br from-white to-blue-50">
                    <p className="text-xs text-gray-600 mb-2 uppercase tracking-wide">Current Ratio</p>
                    <p className="text-3xl font-bold text-black mb-2">
                      {analysisResults.financial_metrics.current_ratio.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-600">Liquidity measure</p>
                    <div className="mt-3 flex items-center gap-1">
                      {analysisResults.financial_metrics.current_ratio > 1.5 ? (
                        <>
                          <TrendingUp className="w-4 h-4 text-green-600" />
                          <span className="text-xs text-green-600 font-medium">Healthy</span>
                        </>
                      ) : analysisResults.financial_metrics.current_ratio > 1.0 ? (
                        <>
                          <Activity className="w-4 h-4 text-yellow-600" />
                          <span className="text-xs text-yellow-600 font-medium">Adequate</span>
                        </>
                      ) : (
                        <>
                          <TrendingDown className="w-4 h-4 text-red-600" />
                          <span className="text-xs text-red-600 font-medium">Weak</span>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Debt to Equity */}
                {analysisResults.financial_metrics.debt_to_equity !== undefined && (
                  <div className="border-2 border-gray-200 p-5 rounded-lg hover:border-purple-400 transition-colors bg-gradient-to-br from-white to-purple-50">
                    <p className="text-xs text-gray-600 mb-2 uppercase tracking-wide">Debt to Equity</p>
                    <p className="text-3xl font-bold text-black mb-2">
                      {analysisResults.financial_metrics.debt_to_equity.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-600">Leverage ratio</p>
                    <div className="mt-3 flex items-center gap-1">
                      {analysisResults.financial_metrics.debt_to_equity < 0.5 ? (
                        <>
                          <TrendingUp className="w-4 h-4 text-green-600" />
                          <span className="text-xs text-green-600 font-medium">Conservative</span>
                        </>
                      ) : analysisResults.financial_metrics.debt_to_equity < 1.0 ? (
                        <>
                          <Activity className="w-4 h-4 text-yellow-600" />
                          <span className="text-xs text-yellow-600 font-medium">Moderate</span>
                        </>
                      ) : (
                        <>
                          <TrendingDown className="w-4 h-4 text-red-600" />
                          <span className="text-xs text-red-600 font-medium">High</span>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Profit Margin */}
                {analysisResults.financial_metrics.profit_margin !== undefined && (
                  <div className="border-2 border-gray-200 p-5 rounded-lg hover:border-green-400 transition-colors bg-gradient-to-br from-white to-green-50">
                    <p className="text-xs text-gray-600 mb-2 uppercase tracking-wide">Profit Margin</p>
                    <p className="text-3xl font-bold text-black mb-2">
                      {(analysisResults.financial_metrics.profit_margin * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-600">Profitability</p>
                    <div className="mt-3 flex items-center gap-1">
                      {analysisResults.financial_metrics.profit_margin > 0.10 ? (
                        <>
                          <TrendingUp className="w-4 h-4 text-green-600" />
                          <span className="text-xs text-green-600 font-medium">Strong</span>
                        </>
                      ) : analysisResults.financial_metrics.profit_margin > 0.05 ? (
                        <>
                          <Activity className="w-4 h-4 text-yellow-600" />
                          <span className="text-xs text-yellow-600 font-medium">Moderate</span>
                        </>
                      ) : (
                        <>
                          <TrendingDown className="w-4 h-4 text-red-600" />
                          <span className="text-xs text-red-600 font-medium">Low</span>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Revenue Growth */}
                {analysisResults.financial_metrics.revenue_growth && analysisResults.financial_metrics.revenue_growth.length > 0 && (
                  <div className="border-2 border-gray-200 p-5 rounded-lg hover:border-orange-400 transition-colors bg-gradient-to-br from-white to-orange-50">
                    <p className="text-xs text-gray-600 mb-2 uppercase tracking-wide">Revenue Growth</p>
                    <p className="text-3xl font-bold text-black mb-2">
                      {analysisResults.financial_metrics.revenue_growth[analysisResults.financial_metrics.revenue_growth.length - 1].toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-600">Latest YoY</p>
                    <div className="mt-3 flex items-center gap-1">
                      {analysisResults.financial_metrics.revenue_growth[analysisResults.financial_metrics.revenue_growth.length - 1] > 15 ? (
                        <>
                          <TrendingUp className="w-4 h-4 text-green-600" />
                          <span className="text-xs text-green-600 font-medium">Strong</span>
                        </>
                      ) : analysisResults.financial_metrics.revenue_growth[analysisResults.financial_metrics.revenue_growth.length - 1] > 5 ? (
                        <>
                          <Activity className="w-4 h-4 text-yellow-600" />
                          <span className="text-xs text-yellow-600 font-medium">Moderate</span>
                        </>
                      ) : analysisResults.financial_metrics.revenue_growth[analysisResults.financial_metrics.revenue_growth.length - 1] > 0 ? (
                        <>
                          <Activity className="w-4 h-4 text-gray-600" />
                          <span className="text-xs text-gray-600 font-medium">Slow</span>
                        </>
                      ) : (
                        <>
                          <TrendingDown className="w-4 h-4 text-red-600" />
                          <span className="text-xs text-red-600 font-medium">Declining</span>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Quick Insights */}
          {analysisResults?.risk_assessment && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              {/* Strengths */}
              {analysisResults.risk_assessment.key_strengths && analysisResults.risk_assessment.key_strengths.length > 0 && (
                <div className="border-2 border-green-200 bg-green-50 p-6 rounded-lg">
                  <h4 className="font-bold text-green-800 mb-4 text-lg flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    Key Strengths
                  </h4>
                  <ul className="space-y-2">
                    {analysisResults.risk_assessment.key_strengths.slice(0, 3).map((strength: string, index: number) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-green-700">
                        <span className="text-green-600 mt-0.5">✓</span>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Concerns */}
              {analysisResults.risk_assessment.key_concerns && analysisResults.risk_assessment.key_concerns.length > 0 && (
                <div className="border-2 border-yellow-200 bg-yellow-50 p-6 rounded-lg">
                  <h4 className="font-bold text-yellow-800 mb-4 text-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    Areas to Monitor
                  </h4>
                  <ul className="space-y-2">
                    {analysisResults.risk_assessment.key_concerns.slice(0, 3).map((concern: string, index: number) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-yellow-700">
                        <span className="text-yellow-600 mt-0.5">⚠</span>
                        <span>{concern}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </motion.div>
          )}
        </>
      )}
    </div>
  );
};

export default OverviewTab;
