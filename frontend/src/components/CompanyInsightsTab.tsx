/**
 * CompanyInsightsTab Component - Premium Minimal Design
 * 
 * Displays company news, insights, and credit score factors
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Building2,
  Newspaper,
  AlertCircle,
  CheckCircle,
  Loader,
  Award,
  BarChart3,
  X,
  ExternalLink,
  Calendar,
  User
} from 'lucide-react';

interface CompanyInsightsTabProps {
  applicationId: string;
  companyName: string;
}

interface NewsItem {
  title: string;
  summary: string;
  full_description?: string;
  content?: string;
  date: string;
  source: string;
  url?: string;
  image_url?: string;
  author?: string;
  sentiment_score: number;
  sentiment_label?: string;
  sentiment_reasoning?: string;
}

const CompanyInsightsTab: React.FC<CompanyInsightsTabProps> = ({
  applicationId,
  companyName
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
  const [showNewsModal, setShowNewsModal] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [newsDetails, setNewsDetails] = useState<any>(null);
  const [legalCases, setLegalCases] = useState<any>(null);
  const [loadingLegalCases, setLoadingLegalCases] = useState(false);

  useEffect(() => {
    fetchInsights();
    fetchLegalCases();
  }, [applicationId]);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(
        `http://localhost:8000/api/v1/applications/${applicationId}/company-insights`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch company insights');
      }

      const data = await response.json();
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load insights');
    } finally {
      setLoading(false);
    }
  };

  const fetchLegalCases = async () => {
    try {
      setLoadingLegalCases(true);
      
      const response = await fetch(
        `http://localhost:8000/api/v1/applications/${applicationId}/legal-cases`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch legal cases');
      }

      const data = await response.json();
      setLegalCases(data.legal_cases);
    } catch (err) {
      console.error('Error fetching legal cases:', err);
      // Don't set error state, just log it
    } finally {
      setLoadingLegalCases(false);
    }
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.5) return 'text-green-600 bg-green-50 border-green-200';
    if (score > 0) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (score > -0.5) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'text-green-600 bg-green-50';
      case 'fair':
        return 'text-yellow-600 bg-yellow-50';
      case 'poor':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const handleNewsClick = async (news: NewsItem) => {
    setSelectedNews(news);
    setShowNewsModal(true);
    setLoadingDetails(true);
    setNewsDetails(null);
    
    // Fetch detailed analysis
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/applications/${applicationId}/news-details`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            news_url: news.url || '',
            news_title: news.title,
            news_description: news.full_description || news.summary,
            company_name: companyName
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch news details');
      }

      const data = await response.json();
      setNewsDetails(data);
    } catch (err) {
      console.error('Error fetching news details:', err);
      setNewsDetails({
        error: 'Unable to load detailed analysis'
      });
    } finally {
      setLoadingDetails(false);
    }
  };

  const closeNewsModal = () => {
    setShowNewsModal(false);
    setSelectedNews(null);
    setNewsDetails(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <Loader className="w-12 h-12 animate-spin text-black mx-auto mb-4" />
          <p className="text-gray-600">Loading company insights...</p>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center py-16"
      >
        <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-8 h-8 text-red-600" />
        </div>
        <p className="text-red-600 font-semibold mb-2">Error loading insights</p>
        <p className="text-gray-600 text-sm mb-6">{error}</p>
        <motion.button
          onClick={fetchInsights}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="bg-black text-white px-6 py-3 rounded-xl font-medium hover:bg-gray-800 transition-all duration-200"
        >
          Retry
        </motion.button>
      </motion.div>
    );
  }

  if (!insights) return null;

  return (
    <div className="space-y-8">
      {/* Company Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-black rounded-xl flex items-center justify-center">
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Company Profile</h2>
            <p className="text-gray-500 text-sm">Extracted from uploaded documents</p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-2">{insights.company_details.company_name}</h3>
          <p className="text-sm text-gray-600 mb-4">
            <span className="font-medium">Industry:</span> {insights.company_details.industry}
          </p>
          <p className="text-gray-700 leading-relaxed mb-6">{insights.company_details.description}</p>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Key Strengths */}
            {insights.company_details.key_strengths && insights.company_details.key_strengths.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <h4 className="font-semibold text-gray-900">Key Strengths</h4>
                </div>
                <ul className="space-y-2">
                  {insights.company_details.key_strengths.map((strength: string, index: number) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-start gap-2 text-sm text-gray-700"
                    >
                      <span className="text-green-600 mt-1">•</span>
                      <span>{strength}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
            )}

            {/* Potential Risks */}
            {insights.company_details.potential_risks && insights.company_details.potential_risks.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600" />
                  <h4 className="font-semibold text-gray-900">Potential Risks</h4>
                </div>
                <ul className="space-y-2">
                  {insights.company_details.potential_risks.map((risk: string, index: number) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-start gap-2 text-sm text-gray-700"
                    >
                      <span className="text-yellow-600 mt-1">•</span>
                      <span>{risk}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Credit Score Factors */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-black rounded-xl flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Credit Score Analysis</h2>
            <p className="text-gray-500 text-sm">Detailed breakdown of credit factors</p>
          </div>
        </div>

        {/* Overall Score Card */}
        <div className="bg-gradient-to-br from-black to-gray-800 rounded-2xl p-8 mb-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/70 text-sm mb-2">Overall Credit Score</p>
              <div className="flex items-baseline gap-3">
                <span className="text-6xl font-bold">{insights.credit_factors.overall_score}</span>
                <span className="text-2xl text-white/70">/100</span>
              </div>
              <p className="text-white/90 mt-3 capitalize">
                Recommendation: <span className="font-semibold">{insights.credit_factors.recommendation}</span>
              </p>
            </div>
            <div className="w-32 h-32 bg-white/10 rounded-2xl flex items-center justify-center">
              <Award className="w-16 h-16 text-white" />
            </div>
          </div>
        </div>

        {/* Credit Factors Grid */}
        <div className="grid md:grid-cols-2 gap-4">
          {Object.entries(insights.credit_factors.factors).map(([key, factor]: [string, any], index) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white rounded-xl border border-gray-200 p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-semibold text-gray-900 capitalize mb-1">
                    {key.replace(/_/g, ' ')}
                  </h4>
                  <p className="text-xs text-gray-500">{factor.description}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(factor.status)}`}>
                  {factor.status}
                </span>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${factor.score}%` }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="h-full bg-gradient-to-r from-black to-gray-600"
                    />
                  </div>
                </div>
                <span className="text-sm font-bold text-gray-900 min-w-[3rem] text-right">
                  {factor.score}/100
                </span>
              </div>
              
              <p className="text-xs text-gray-500 mt-2">
                Weight: {(factor.weight * 100).toFixed(0)}%
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Legal Cases Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-gradient-to-br from-red-600 to-rose-700 rounded-xl flex items-center justify-center shadow-lg">
            <AlertCircle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Legal & Compliance Status</h2>
            <p className="text-gray-500 text-sm">Court cases, litigation, and regulatory actions</p>
          </div>
        </div>

        {loadingLegalCases ? (
          <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
            <Loader className="w-8 h-8 animate-spin text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">Searching legal records...</p>
          </div>
        ) : legalCases ? (
          <div className="space-y-6">
            {/* Summary Card */}
            <div className={`rounded-2xl border-2 p-6 ${
              legalCases.risk_assessment?.overall_risk_level === 'low' || legalCases.risk_assessment?.overall_risk_level === 'unknown'
                ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-300'
                : legalCases.risk_assessment?.overall_risk_level === 'medium'
                ? 'bg-gradient-to-br from-yellow-50 to-amber-50 border-yellow-300'
                : 'bg-gradient-to-br from-red-50 to-rose-50 border-red-300'
            }`}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Legal Risk Assessment</h3>
                  <p className="text-gray-700 leading-relaxed">{legalCases.summary}</p>
                </div>
                <span className={`px-4 py-2 rounded-xl font-bold text-sm uppercase tracking-wide ${
                  legalCases.risk_assessment?.overall_risk_level === 'low' || legalCases.risk_assessment?.overall_risk_level === 'unknown'
                    ? 'bg-green-100 text-green-800'
                    : legalCases.risk_assessment?.overall_risk_level === 'medium'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {legalCases.risk_assessment?.overall_risk_level || 'Unknown'} Risk
                </span>
              </div>

              {/* Credit Impact */}
              {legalCases.risk_assessment?.credit_impact && (
                <div className="mt-4 pt-4 border-t-2 border-gray-200">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Credit Impact:</p>
                  <span className={`inline-block px-3 py-1 rounded-lg text-sm font-medium ${
                    legalCases.risk_assessment.credit_impact === 'positive'
                      ? 'bg-green-100 text-green-800'
                      : legalCases.risk_assessment.credit_impact === 'neutral'
                      ? 'bg-gray-100 text-gray-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {legalCases.risk_assessment.credit_impact}
                  </span>
                </div>
              )}
            </div>

            {/* Ongoing Cases */}
            {legalCases.ongoing_cases && legalCases.ongoing_cases.length > 0 && (
              <div className="bg-white rounded-2xl border-2 border-red-200 p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  Ongoing Legal Cases ({legalCases.ongoing_cases.length})
                </h3>
                <div className="space-y-4">
                  {legalCases.ongoing_cases.map((case_item: any, index: number) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-red-50 rounded-xl p-4 border border-red-200"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="px-3 py-1 bg-red-100 text-red-800 rounded-lg text-xs font-bold uppercase">
                          {case_item.case_type}
                        </span>
                        <span className={`px-3 py-1 rounded-lg text-xs font-bold ${
                          case_item.severity === 'critical'
                            ? 'bg-red-600 text-white'
                            : case_item.severity === 'high'
                            ? 'bg-red-500 text-white'
                            : case_item.severity === 'medium'
                            ? 'bg-yellow-500 text-white'
                            : 'bg-gray-500 text-white'
                        }`}>
                          {case_item.severity} Severity
                        </span>
                      </div>
                      <p className="text-gray-900 font-medium mb-2">{case_item.description}</p>
                      {case_item.financial_impact && (
                        <p className="text-sm text-gray-700 mb-2">
                          <span className="font-semibold">Financial Impact:</span> {case_item.financial_impact}
                        </p>
                      )}
                      {case_item.credit_risk_impact && (
                        <p className="text-sm text-gray-700">
                          <span className="font-semibold">Credit Risk:</span> {case_item.credit_risk_impact}
                        </p>
                      )}
                      {case_item.estimated_year && (
                        <p className="text-xs text-gray-600 mt-2">Year: {case_item.estimated_year}</p>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Past Cases */}
            {legalCases.past_cases && legalCases.past_cases.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-200 p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Past Legal Cases ({legalCases.past_cases.length})</h3>
                <div className="space-y-3">
                  {legalCases.past_cases.map((case_item: any, index: number) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="flex items-start justify-between mb-2">
                        <span className="px-3 py-1 bg-gray-200 text-gray-800 rounded-lg text-xs font-bold uppercase">
                          {case_item.case_type}
                        </span>
                        {case_item.year && (
                          <span className="text-xs text-gray-600">{case_item.year}</span>
                        )}
                      </div>
                      <p className="text-gray-800 text-sm mb-1">{case_item.description}</p>
                      {case_item.outcome && (
                        <p className="text-xs text-gray-600">Outcome: {case_item.outcome}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Regulatory Actions */}
            {legalCases.regulatory_actions && legalCases.regulatory_actions.length > 0 && (
              <div className="bg-white rounded-2xl border-2 border-orange-200 p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Regulatory Actions ({legalCases.regulatory_actions.length})</h3>
                <div className="space-y-3">
                  {legalCases.regulatory_actions.map((action: any, index: number) => (
                    <div key={index} className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                      <div className="flex items-start justify-between mb-2">
                        <span className="font-semibold text-gray-900">{action.authority}</span>
                        <span className={`px-3 py-1 rounded-lg text-xs font-bold ${
                          action.severity === 'high'
                            ? 'bg-red-500 text-white'
                            : action.severity === 'medium'
                            ? 'bg-yellow-500 text-white'
                            : 'bg-gray-500 text-white'
                        }`}>
                          {action.severity}
                        </span>
                      </div>
                      <p className="text-gray-800 text-sm mb-1">{action.action}</p>
                      {action.year && (
                        <p className="text-xs text-gray-600">Year: {action.year}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risk Assessment Details */}
            {legalCases.risk_assessment && (
              <div className="grid md:grid-cols-2 gap-6">
                {/* Key Concerns */}
                {legalCases.risk_assessment.key_concerns && legalCases.risk_assessment.key_concerns.length > 0 && (
                  <div className="bg-red-50 rounded-2xl border border-red-200 p-6">
                    <h4 className="font-bold text-red-900 mb-3 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5" />
                      Key Concerns
                    </h4>
                    <ul className="space-y-2">
                      {legalCases.risk_assessment.key_concerns.map((concern: string, index: number) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-red-900">
                          <span className="text-red-600 mt-0.5">⚠</span>
                          <span>{concern}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Mitigating Factors */}
                {legalCases.risk_assessment.mitigating_factors && legalCases.risk_assessment.mitigating_factors.length > 0 && (
                  <div className="bg-green-50 rounded-2xl border border-green-200 p-6">
                    <h4 className="font-bold text-green-900 mb-3 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Mitigating Factors
                    </h4>
                    <ul className="space-y-2">
                      {legalCases.risk_assessment.mitigating_factors.map((factor: string, index: number) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-green-900">
                          <span className="text-green-600 mt-0.5">✓</span>
                          <span>{factor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Recommendation */}
            {legalCases.risk_assessment?.recommendation && (
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border-2 border-indigo-200 p-6">
                <h4 className="font-bold text-indigo-900 mb-3">Recommendation for Lenders</h4>
                <p className="text-indigo-900 leading-relaxed">{legalCases.risk_assessment.recommendation}</p>
              </div>
            )}

            {/* Recommended Checks */}
            {legalCases.recommended_checks && legalCases.recommended_checks.length > 0 && (
              <div className="bg-blue-50 rounded-2xl border border-blue-200 p-6">
                <h4 className="font-bold text-blue-900 mb-3">Recommended Due Diligence</h4>
                <ul className="space-y-2">
                  {legalCases.recommended_checks.map((check: string, index: number) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-blue-900">
                      <span className="text-blue-600 mt-0.5">→</span>
                      <span>{check}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Data Quality Notice */}
            {legalCases.requires_manual_verification && (
              <div className="bg-yellow-50 rounded-xl border border-yellow-300 p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-yellow-900 mb-1">Manual Verification Required</p>
                    <p className="text-sm text-yellow-800">
                      This information is based on automated search. Please verify through official court records (eCourts, NCLT, etc.) for accurate legal status.
                    </p>
                    {legalCases.note && (
                      <p className="text-xs text-yellow-700 mt-2">{legalCases.note}</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">Legal case information not available</p>
          </div>
        )}
      </motion.div>

      {/* Company News */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-black rounded-xl flex items-center justify-center">
            <Newspaper className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Company News & Sentiment</h2>
            <p className="text-gray-500 text-sm">Recent positive and negative developments</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Positive News */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-gray-900">Positive News</h3>
              <span className="text-xs text-gray-500">({insights.news.positive.length})</span>
            </div>
            <div className="space-y-3">
              {insights.news.positive.map((item: NewsItem, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => handleNewsClick(item)}
                  className={`rounded-xl border p-4 ${getSentimentColor(item.sentiment_score)} hover:shadow-lg transition-all duration-200 cursor-pointer`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-sm flex-1">{item.title}</h4>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleNewsClick(item);
                      }}
                      className="text-xs text-blue-600 hover:text-blue-800 ml-2 flex items-center gap-1"
                    >
                      Details
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                  
                  <p className="text-xs text-gray-700 mb-3 leading-relaxed">
                    {item.full_description || item.summary}
                  </p>
                  
                  {item.sentiment_reasoning && (
                    <div className="mb-3 p-2 bg-white/50 rounded-lg">
                      <p className="text-xs text-gray-600 italic">
                        <span className="font-semibold">Analysis:</span> {item.sentiment_reasoning}
                      </p>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 font-medium">{item.source}</span>
                      {item.author && item.author !== "Unknown" && (
                        <>
                          <span className="text-gray-400">•</span>
                          <span className="text-gray-500">{item.author}</span>
                        </>
                      )}
                    </div>
                    <span className="text-gray-500">{new Date(item.date).toLocaleDateString()}</span>
                  </div>
                  
                  {item.sentiment_score && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-white/50 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-600"
                          style={{ width: `${Math.abs(item.sentiment_score) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-green-700">
                        +{(item.sentiment_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>

          {/* Negative News */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <TrendingDown className="w-5 h-5 text-red-600" />
              <h3 className="font-semibold text-gray-900">Negative News</h3>
              <span className="text-xs text-gray-500">({insights.news.negative.length})</span>
            </div>
            <div className="space-y-3">
              {insights.news.negative.map((item: NewsItem, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => handleNewsClick(item)}
                  className={`rounded-xl border p-4 ${getSentimentColor(item.sentiment_score)} hover:shadow-lg transition-all duration-200 cursor-pointer`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-sm flex-1">{item.title}</h4>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleNewsClick(item);
                      }}
                      className="text-xs text-blue-600 hover:text-blue-800 ml-2 flex items-center gap-1"
                    >
                      Details
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                  
                  <p className="text-xs text-gray-700 mb-3 leading-relaxed">
                    {item.full_description || item.summary}
                  </p>
                  
                  {item.sentiment_reasoning && (
                    <div className="mb-3 p-2 bg-white/50 rounded-lg">
                      <p className="text-xs text-gray-600 italic">
                        <span className="font-semibold">Analysis:</span> {item.sentiment_reasoning}
                      </p>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 font-medium">{item.source}</span>
                      {item.author && item.author !== "Unknown" && (
                        <>
                          <span className="text-gray-400">•</span>
                          <span className="text-gray-500">{item.author}</span>
                        </>
                      )}
                    </div>
                    <span className="text-gray-500">{new Date(item.date).toLocaleDateString()}</span>
                  </div>
                  
                  {item.sentiment_score && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-white/50 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-red-600"
                          style={{ width: `${Math.abs(item.sentiment_score) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-red-700">
                        {(item.sentiment_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
        
        {/* News Source Attribution */}
        <div className="mt-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
          <p className="text-xs text-gray-600 text-center">
            News powered by <span className="font-semibold">{insights.news.source || 'NewsAPI'}</span>
            {insights.news.api_status === 'fallback' && ' (AI Generated)'}
            {' • '}Last updated: {new Date(insights.news.last_updated).toLocaleString()}
          </p>
        </div>
      </motion.div>

      {/* Detailed News Modal */}
      {showNewsModal && selectedNews && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={closeNewsModal}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-2xl shadow-2xl border border-gray-200 max-w-3xl w-full max-h-[90vh] overflow-y-auto"
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 rounded-t-2xl">
              <div className="flex items-start justify-between">
                <div className="flex-1 pr-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      selectedNews.sentiment_score > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {selectedNews.sentiment_label || (selectedNews.sentiment_score > 0 ? 'Positive' : 'Negative')}
                    </span>
                    <span className="text-xs text-gray-500">{selectedNews.source}</span>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 leading-tight">
                    {selectedNews.title}
                  </h2>
                </div>
                <button
                  onClick={closeNewsModal}
                  className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Article Image */}
              {selectedNews.image_url && (
                <div className="rounded-xl overflow-hidden">
                  <img
                    src={selectedNews.image_url}
                    alt={selectedNews.title}
                    className="w-full h-64 object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* Article Metadata */}
              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                {selectedNews.author && selectedNews.author !== 'Unknown' && (
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    <span>{selectedNews.author}</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span>{new Date(selectedNews.date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Newspaper className="w-4 h-4" />
                  <span>{selectedNews.source}</span>
                </div>
              </div>

              {/* Loading State */}
              {loadingDetails && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <Loader className="w-12 h-12 animate-spin text-black mx-auto mb-4" />
                    <p className="text-gray-600">Loading detailed analysis...</p>
                  </div>
                </div>
              )}

              {/* Detailed Analysis */}
              {!loadingDetails && newsDetails && !newsDetails.error && newsDetails.detailed_analysis && (
                <div className="space-y-6">
                  {/* Executive Summary */}
                  {newsDetails.detailed_analysis.executive_summary && (
                    <div className="bg-gradient-to-br from-blue-50 to-white rounded-xl border border-blue-200 p-5">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Executive Summary</h3>
                      <p className="text-gray-700 leading-relaxed">
                        {newsDetails.detailed_analysis.executive_summary}
                      </p>
                    </div>
                  )}

                  {/* Key Points */}
                  {newsDetails.detailed_analysis?.key_points && newsDetails.detailed_analysis.key_points.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Points</h3>
                      <ul className="space-y-2">
                        {newsDetails.detailed_analysis.key_points.map((point: string, index: number) => (
                          <motion.li
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-start gap-3 text-gray-700"
                          >
                            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                            <span>{point}</span>
                          </motion.li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Financial Implications */}
                  {newsDetails.detailed_analysis?.financial_implications && 
                   Object.keys(newsDetails.detailed_analysis.financial_implications).length > 0 && (
                    <div className="bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-200 p-5">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Financial Implications</h3>
                      <div className="grid md:grid-cols-2 gap-4">
                        {newsDetails.detailed_analysis.financial_implications.short_term && (
                          <div>
                            <p className="text-sm font-semibold text-gray-700 mb-2">Short-term (3-6 months)</p>
                            <p className="text-sm text-gray-600">{newsDetails.detailed_analysis.financial_implications.short_term}</p>
                          </div>
                        )}
                        {newsDetails.detailed_analysis.financial_implications.long_term && (
                          <div>
                            <p className="text-sm font-semibold text-gray-700 mb-2">Long-term (6+ months)</p>
                            <p className="text-sm text-gray-600">{newsDetails.detailed_analysis.financial_implications.long_term}</p>
                          </div>
                        )}
                        {newsDetails.detailed_analysis.financial_implications.revenue_impact && (
                          <div>
                            <p className="text-sm font-semibold text-gray-700 mb-2">Revenue Impact</p>
                            <p className="text-sm text-gray-600">{newsDetails.detailed_analysis.financial_implications.revenue_impact}</p>
                          </div>
                        )}
                        {newsDetails.detailed_analysis.financial_implications.market_position && (
                          <div>
                            <p className="text-sm font-semibold text-gray-700 mb-2">Market Position</p>
                            <p className="text-sm text-gray-600">{newsDetails.detailed_analysis.financial_implications.market_position}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Risk Assessment */}
                  {newsDetails.detailed_analysis?.risk_assessment && 
                   Object.keys(newsDetails.detailed_analysis.risk_assessment).length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment</h3>
                      <div className="grid md:grid-cols-2 gap-3">
                        {Object.entries(newsDetails.detailed_analysis.risk_assessment).map(([key, value]: [string, any]) => {
                          const riskLevel = value.toLowerCase().includes('high') ? 'high' : 
                                          value.toLowerCase().includes('medium') ? 'medium' : 'low';
                          const riskColor = riskLevel === 'high' ? 'bg-red-50 border-red-200 text-red-700' :
                                          riskLevel === 'medium' ? 'bg-yellow-50 border-yellow-200 text-yellow-700' :
                                          'bg-green-50 border-green-200 text-green-700';
                          
                          return (
                            <div key={key} className={`rounded-lg border p-4 ${riskColor}`}>
                              <p className="text-sm font-semibold mb-2 capitalize">{key.replace(/_/g, ' ')}</p>
                              <p className="text-xs">{value}</p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Opportunities & Threats */}
                  <div className="grid md:grid-cols-2 gap-6">
                    {newsDetails.detailed_analysis?.opportunities && newsDetails.detailed_analysis.opportunities.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                          <TrendingUp className="w-5 h-5 text-green-600" />
                          Opportunities
                        </h3>
                        <ul className="space-y-2">
                          {newsDetails.detailed_analysis.opportunities.map((opp: string, index: number) => (
                            <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                              <span className="text-green-600 mt-1">•</span>
                              <span>{opp}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {newsDetails.detailed_analysis?.threats && newsDetails.detailed_analysis.threats.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                          <TrendingDown className="w-5 h-5 text-red-600" />
                          Threats
                        </h3>
                        <ul className="space-y-2">
                          {newsDetails.detailed_analysis.threats.map((threat: string, index: number) => (
                            <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                              <span className="text-red-600 mt-1">•</span>
                              <span>{threat}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Recommendations */}
                  {newsDetails.detailed_analysis?.recommendations && 
                   Object.keys(newsDetails.detailed_analysis.recommendations).length > 0 && (
                    <div className="bg-gradient-to-br from-purple-50 to-white rounded-xl border border-purple-200 p-5">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
                      <div className="space-y-4">
                        {newsDetails.detailed_analysis.recommendations.for_lenders && (
                          <div>
                            <p className="text-sm font-semibold text-purple-700 mb-2">For Lenders/Creditors:</p>
                            <p className="text-sm text-gray-700">{newsDetails.detailed_analysis.recommendations.for_lenders}</p>
                          </div>
                        )}
                        {newsDetails.detailed_analysis.recommendations.for_investors && (
                          <div>
                            <p className="text-sm font-semibold text-purple-700 mb-2">For Investors:</p>
                            <p className="text-sm text-gray-700">{newsDetails.detailed_analysis.recommendations.for_investors}</p>
                          </div>
                        )}
                        {newsDetails.detailed_analysis.recommendations.monitoring_points && newsDetails.detailed_analysis.recommendations.monitoring_points.length > 0 && (
                          <div>
                            <p className="text-sm font-semibold text-purple-700 mb-2">Key Monitoring Points:</p>
                            <ul className="space-y-1">
                              {newsDetails.detailed_analysis.recommendations.monitoring_points.map((point: string, index: number) => (
                                <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                                  <span className="text-purple-600">→</span>
                                  <span>{point}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Key Metrics to Watch */}
                  {newsDetails.detailed_analysis?.key_metrics_to_watch && newsDetails.detailed_analysis.key_metrics_to_watch.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Metrics to Watch</h3>
                      <div className="flex flex-wrap gap-2">
                        {newsDetails.detailed_analysis.key_metrics_to_watch.map((metric: string, index: number) => (
                          <span
                            key={index}
                            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium"
                          >
                            {metric}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Error State */}
              {!loadingDetails && newsDetails?.error && (
                <div className="text-center py-8">
                  <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
                  <p className="text-red-600 font-medium">{newsDetails.error}</p>
                </div>
              )}

              {/* Fallback: Show basic description if no detailed analysis */}
              {!loadingDetails && !newsDetails && (
                <div className="prose prose-sm max-w-none">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Article Summary</h3>
                  <p className="text-gray-700 leading-relaxed">
                    {selectedNews.full_description || selectedNews.summary}
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                {selectedNews.url && (
                  <motion.a
                    href={selectedNews.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 transition-all duration-200"
                  >
                    Read Full Article
                    <ExternalLink className="w-4 h-4" />
                  </motion.a>
                )}
                <motion.button
                  onClick={closeNewsModal}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-gray-50 transition-all duration-200"
                >
                  Close
                </motion.button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};

export default CompanyInsightsTab;
