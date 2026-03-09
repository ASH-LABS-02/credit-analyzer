/**
 * LegalCasesTab Component - Premium Design
 * 
 * Displays company legal cases, litigation history, and regulatory actions
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  CheckCircle,
  Loader,
  Scale,
  FileText,
  Building,
  Calendar,
  TrendingUp,
  TrendingDown,
  Shield,
  AlertTriangle
} from 'lucide-react';

interface LegalCasesTabProps {
  applicationId: string;
  companyName: string;
}

const LegalCasesTab: React.FC<LegalCasesTabProps> = ({
  applicationId,
  companyName
}) => {
  const [legalCases, setLegalCases] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLegalCases();
  }, [applicationId]);

  const fetchLegalCases = async () => {
    try {
      setLoading(true);
      setError(null);
      
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
      setError(err instanceof Error ? err.message : 'Failed to load legal cases');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'low':
      case 'unknown':
        return {
          bg: 'bg-gradient-to-br from-emerald-50 to-teal-50',
          border: 'border-emerald-300',
          badge: 'bg-emerald-100 text-emerald-800'
        };
      case 'medium':
        return {
          bg: 'bg-gradient-to-br from-amber-50 to-orange-50',
          border: 'border-amber-300',
          badge: 'bg-amber-100 text-amber-800'
        };
      case 'high':
      case 'critical':
        return {
          bg: 'bg-gradient-to-br from-rose-50 to-red-50',
          border: 'border-rose-300',
          badge: 'bg-rose-100 text-rose-800'
        };
      default:
        return {
          bg: 'bg-gradient-to-br from-gray-50 to-slate-50',
          border: 'border-gray-300',
          badge: 'bg-gray-100 text-gray-800'
        };
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-600 text-white';
      case 'high':
        return 'bg-red-500 text-white';
      case 'medium':
        return 'bg-amber-500 text-white';
      case 'low':
        return 'bg-gray-500 text-white';
      default:
        return 'bg-gray-400 text-white';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Searching legal records...</p>
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
        <AlertCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-gray-900 mb-2">Failed to Load Legal Cases</h3>
        <p className="text-gray-600 mb-6">{error}</p>
        <button
          onClick={fetchLegalCases}
          className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors"
        >
          Try Again
        </button>
      </motion.div>
    );
  }

  if (!legalCases) {
    return (
      <div className="text-center py-16">
        <Scale className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No legal case information available</p>
      </div>
    );
  }

  const riskColors = getRiskColor(legalCases.risk_assessment?.overall_risk_level);

  return (
    <div className="space-y-8 bg-gradient-to-br from-slate-50 to-gray-100 p-8 rounded-3xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl flex items-center justify-center shadow-lg">
          <Scale className="w-7 h-7 text-white" />
        </div>
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            Legal & Compliance Status
          </h2>
          <p className="text-gray-600 text-sm font-medium">{companyName}</p>
        </div>
      </div>

      {/* Risk Assessment Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`rounded-3xl border-2 p-8 shadow-xl ${riskColors.bg} ${riskColors.border}`}
      >
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-8 h-8 text-indigo-600" />
              <h3 className="text-2xl font-bold text-gray-900">Legal Risk Assessment</h3>
            </div>
            <p className="text-gray-800 leading-relaxed text-lg">{legalCases.summary}</p>
          </div>
          <span className={`px-5 py-3 rounded-2xl font-bold text-sm uppercase tracking-wide shadow-md ${riskColors.badge}`}>
            {legalCases.risk_assessment?.overall_risk_level || 'Unknown'} Risk
          </span>
        </div>

        {/* Credit Impact */}
        {legalCases.risk_assessment?.credit_impact && (
          <div className="mt-6 pt-6 border-t-2 border-gray-300/50">
            <p className="text-sm font-bold text-gray-700 mb-3 uppercase tracking-wider">Credit Impact Assessment</p>
            <div className="flex items-center gap-3">
              {legalCases.risk_assessment.credit_impact === 'positive' ? (
                <TrendingUp className="w-6 h-6 text-emerald-600" />
              ) : legalCases.risk_assessment.credit_impact === 'neutral' ? (
                <Shield className="w-6 h-6 text-gray-600" />
              ) : (
                <TrendingDown className="w-6 h-6 text-rose-600" />
              )}
              <span className={`inline-block px-4 py-2 rounded-xl text-base font-bold shadow-md ${
                legalCases.risk_assessment.credit_impact === 'positive'
                  ? 'bg-emerald-100 text-emerald-900'
                  : legalCases.risk_assessment.credit_impact === 'neutral'
                  ? 'bg-gray-100 text-gray-900'
                  : 'bg-rose-100 text-rose-900'
              }`}>
                {legalCases.risk_assessment.credit_impact.charAt(0).toUpperCase() + 
                 legalCases.risk_assessment.credit_impact.slice(1)} Impact
              </span>
            </div>
          </div>
        )}
      </motion.div>

      {/* Ongoing Cases */}
      {legalCases.ongoing_cases && legalCases.ongoing_cases.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <AlertTriangle className="w-6 h-6 text-rose-600" />
            <h3 className="text-2xl font-bold text-gray-900">
              Ongoing Legal Cases ({legalCases.ongoing_cases.length})
            </h3>
          </div>
          
          <div className="grid gap-5">
            {legalCases.ongoing_cases.map((case_item: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-2xl p-6 border-2 border-rose-200 shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-rose-100 rounded-xl flex items-center justify-center">
                      <FileText className="w-6 h-6 text-rose-600" />
                    </div>
                    <span className="px-4 py-2 bg-rose-100 text-rose-900 rounded-xl text-sm font-bold uppercase tracking-wide">
                      {case_item.case_type}
                    </span>
                  </div>
                  <span className={`px-4 py-2 rounded-xl text-sm font-bold uppercase tracking-wide shadow-md ${getSeverityColor(case_item.severity)}`}>
                    {case_item.severity} Severity
                  </span>
                </div>
                
                <p className="text-gray-900 font-semibold text-lg mb-4">{case_item.description}</p>
                
                <div className="space-y-3 bg-rose-50 rounded-xl p-4 border border-rose-200">
                  {case_item.financial_impact && (
                    <div>
                      <p className="text-xs font-bold text-rose-900 mb-1 uppercase tracking-wider">Financial Impact</p>
                      <p className="text-sm text-rose-800">{case_item.financial_impact}</p>
                    </div>
                  )}
                  {case_item.credit_risk_impact && (
                    <div>
                      <p className="text-xs font-bold text-rose-900 mb-1 uppercase tracking-wider">Credit Risk Impact</p>
                      <p className="text-sm text-rose-800">{case_item.credit_risk_impact}</p>
                    </div>
                  )}
                  {case_item.estimated_year && (
                    <div className="flex items-center gap-2 text-sm text-rose-700">
                      <Calendar className="w-4 h-4" />
                      <span className="font-medium">Year: {case_item.estimated_year}</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Past Cases */}
      {legalCases.past_cases && legalCases.past_cases.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <FileText className="w-6 h-6 text-gray-600" />
            <h3 className="text-2xl font-bold text-gray-900">
              Past Legal Cases ({legalCases.past_cases.length})
            </h3>
          </div>
          
          <div className="grid md:grid-cols-2 gap-4">
            {legalCases.past_cases.map((case_item: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white rounded-2xl p-5 border-2 border-gray-200 shadow-md hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <span className="px-3 py-2 bg-gray-200 text-gray-900 rounded-xl text-xs font-bold uppercase tracking-wide">
                    {case_item.case_type}
                  </span>
                  {case_item.year && (
                    <span className="text-sm text-gray-600 font-medium">{case_item.year}</span>
                  )}
                </div>
                <p className="text-gray-900 font-medium mb-2">{case_item.description}</p>
                {case_item.outcome && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs font-bold text-gray-600 mb-1 uppercase tracking-wider">Outcome</p>
                    <p className="text-sm text-gray-700">{case_item.outcome}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Regulatory Actions */}
      {legalCases.regulatory_actions && legalCases.regulatory_actions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <Building className="w-6 h-6 text-amber-600" />
            <h3 className="text-2xl font-bold text-gray-900">
              Regulatory Actions ({legalCases.regulatory_actions.length})
            </h3>
          </div>
          
          <div className="grid gap-4">
            {legalCases.regulatory_actions.map((action: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-2xl p-5 border-2 border-amber-200 shadow-md hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="text-xs font-bold text-amber-900 mb-1 uppercase tracking-wider">Regulatory Authority</p>
                    <p className="font-bold text-gray-900 text-lg">{action.authority}</p>
                  </div>
                  <span className={`px-4 py-2 rounded-xl text-sm font-bold uppercase tracking-wide shadow-md ${getSeverityColor(action.severity)}`}>
                    {action.severity}
                  </span>
                </div>
                <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                  <p className="text-gray-900 font-medium">{action.action}</p>
                  {action.year && (
                    <p className="text-sm text-amber-700 mt-2 font-medium">Year: {action.year}</p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Risk Assessment Details */}
      {legalCases.risk_assessment && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
          className="grid md:grid-cols-2 gap-6"
        >
          {/* Key Concerns */}
          {legalCases.risk_assessment.key_concerns && legalCases.risk_assessment.key_concerns.length > 0 && (
            <div className="bg-gradient-to-br from-rose-50 to-red-50 rounded-3xl border-2 border-rose-300 p-7 shadow-lg">
              <h4 className="font-bold text-rose-900 mb-5 text-xl flex items-center gap-2">
                <AlertCircle className="w-6 h-6" />
                Key Concerns
              </h4>
              <ul className="space-y-3">
                {legalCases.risk_assessment.key_concerns.map((concern: string, index: number) => (
                  <motion.li
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-3 text-sm text-rose-900 font-medium"
                  >
                    <span className="text-rose-600 mt-0.5 text-lg">⚠</span>
                    <span>{concern}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          )}

          {/* Mitigating Factors */}
          {legalCases.risk_assessment.mitigating_factors && legalCases.risk_assessment.mitigating_factors.length > 0 && (
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-3xl border-2 border-emerald-300 p-7 shadow-lg">
              <h4 className="font-bold text-emerald-900 mb-5 text-xl flex items-center gap-2">
                <CheckCircle className="w-6 h-6" />
                Mitigating Factors
              </h4>
              <ul className="space-y-3">
                {legalCases.risk_assessment.mitigating_factors.map((factor: string, index: number) => (
                  <motion.li
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-3 text-sm text-emerald-900 font-medium"
                  >
                    <span className="text-emerald-600 mt-0.5 text-lg">✓</span>
                    <span>{factor}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}

      {/* Recommendation */}
      {legalCases.risk_assessment?.recommendation && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.5 }}
          className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-3xl border-2 border-indigo-300 p-8 shadow-xl"
        >
          <h4 className="font-bold text-indigo-900 mb-4 text-xl flex items-center gap-2">
            <Shield className="w-6 h-6" />
            Recommendation for Lenders
          </h4>
          <p className="text-indigo-900 leading-relaxed text-lg font-medium">
            {legalCases.risk_assessment.recommendation}
          </p>
        </motion.div>
      )}

      {/* Recommended Checks */}
      {legalCases.recommended_checks && legalCases.recommended_checks.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.6 }}
          className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-3xl border-2 border-blue-300 p-7 shadow-lg"
        >
          <h4 className="font-bold text-blue-900 mb-5 text-xl">Recommended Due Diligence</h4>
          <ul className="space-y-3">
            {legalCases.recommended_checks.map((check: string, index: number) => (
              <motion.li
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-3 text-sm text-blue-900 font-medium"
              >
                <span className="text-blue-600 mt-0.5 text-lg">→</span>
                <span>{check}</span>
              </motion.li>
            ))}
          </ul>
        </motion.div>
      )}

      {/* Data Quality Notice */}
      {legalCases.requires_manual_verification && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.7 }}
          className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-2xl border-2 border-yellow-300 p-6 shadow-lg"
        >
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
            <div>
              <p className="text-base font-bold text-yellow-900 mb-2">Manual Verification Required</p>
              <p className="text-sm text-yellow-800 leading-relaxed mb-3">
                This information is based on automated search. Please verify through official court records (eCourts, NCLT, etc.) for accurate legal status.
              </p>
              {legalCases.note && (
                <p className="text-xs text-yellow-700 font-medium bg-yellow-100 rounded-lg p-3 border border-yellow-200">
                  {legalCases.note}
                </p>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Metadata */}
      <div className="text-center text-sm text-gray-500 pt-4 border-t border-gray-300">
        <p>Last checked: {legalCases.last_checked || 'N/A'}</p>
        <p className="text-xs mt-1">Data source: {legalCases.data_source || 'Unknown'}</p>
      </div>
    </div>
  );
};

export default LegalCasesTab;
