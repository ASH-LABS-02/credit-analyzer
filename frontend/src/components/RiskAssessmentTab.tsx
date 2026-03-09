/**
 * RiskAssessmentTab Component - Premium Design
 * Requirements: 6.1, 6.2, 6.3, 6.7, 13.2
 * 
 * Enhanced with premium minimal aesthetic and professional polish
 */

import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertCircle, 
  ChevronDown, 
  ChevronUp, 
  Shield,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  AlertTriangle,
  BarChart3,
  Target,
  Zap,
  Award
} from 'lucide-react';
import { useState } from 'react';

interface RiskAssessmentTabProps {
  application: any;
  analysisResults: any;
  loading: boolean;
}

const RiskAssessmentTab: React.FC<RiskAssessmentTabProps> = ({
  application,
  analysisResults,
  loading,
}) => {
  const [expandedFactor, setExpandedFactor] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-gray-600">Analyzing risk factors...</p>
        </motion.div>
      </div>
    );
  }

  const creditScore = application?.credit_score || 0;
  const recommendation = application?.recommendation || 'pending';

  // Extract risk analysis from analysisResults
  const riskAssessment = analysisResults?.risk_assessment || {};
  const riskFactorsData = riskAssessment?.risk_factors || {};
  
  // Build risk factors array from real data with detailed explanations
  const riskFactors = [];
  
  if (riskFactorsData.liquidity) {
    riskFactors.push({
      name: 'Liquidity',
      icon: TrendingUp,
      score: Math.round(riskFactorsData.liquidity.score * 100),
      weight: 30,
      assessment: riskFactorsData.liquidity.assessment || 'Liquidity position analysis',
      explanation: riskFactorsData.liquidity.explanation || 'Liquidity position analysis',
      metrics: riskFactorsData.liquidity.metrics || {},
      impact: riskFactorsData.liquidity.impact || 'Neutral'
    });
  }
  
  if (riskFactorsData.leverage) {
    riskFactors.push({
      name: 'Leverage',
      icon: BarChart3,
      score: Math.round(riskFactorsData.leverage.score * 100),
      weight: 25,
      assessment: riskFactorsData.leverage.assessment || 'Debt and leverage analysis',
      explanation: riskFactorsData.leverage.explanation || 'Debt and leverage analysis',
      metrics: riskFactorsData.leverage.metrics || {},
      impact: riskFactorsData.leverage.impact || 'Neutral'
    });
  }
  
  if (riskFactorsData.profitability) {
    riskFactors.push({
      name: 'Profitability',
      icon: Target,
      score: Math.round(riskFactorsData.profitability.score * 100),
      weight: 25,
      assessment: riskFactorsData.profitability.assessment || 'Profitability analysis',
      explanation: riskFactorsData.profitability.explanation || 'Profitability analysis',
      metrics: riskFactorsData.profitability.metrics || {},
      impact: riskFactorsData.profitability.impact || 'Neutral'
    });
  }
  
  if (riskFactorsData.growth) {
    riskFactors.push({
      name: 'Growth',
      icon: TrendingUp,
      score: Math.round(riskFactorsData.growth.score * 100),
      weight: 20,
      assessment: riskFactorsData.growth.assessment || 'Growth trend analysis',
      explanation: riskFactorsData.growth.explanation || 'Growth trend analysis',
      metrics: riskFactorsData.growth.metrics || {},
      impact: riskFactorsData.growth.impact || 'Neutral'
    });
  }
  
  // Fallback to mock data if no real data available
  if (riskFactors.length === 0) {
    riskFactors.push(
      { name: 'Financial Health', icon: Shield, score: 85, weight: 35, explanation: 'Strong liquidity and profitability ratios', impact: 'Positive' },
      { name: 'Cash Flow', icon: TrendingUp, score: 78, weight: 25, explanation: 'Consistent positive cash flow', impact: 'Positive' },
      { name: 'Industry', icon: BarChart3, score: 72, weight: 15, explanation: 'Stable industry with moderate growth', impact: 'Neutral' },
      { name: 'Promoter', icon: Award, score: 80, weight: 15, explanation: 'Experienced management team', impact: 'Positive' },
      { name: 'External Intelligence', icon: Target, score: 75, weight: 10, explanation: 'Positive market sentiment', impact: 'Positive' }
    );
  }
  
  // Extract key strengths and concerns
  const keyStrengths = riskAssessment?.key_strengths || [];
  const keyConcerns = riskAssessment?.key_concerns || [];
  const recommendationRationale = riskAssessment?.recommendation_rationale || '';
  const decisionLogic = riskAssessment?.decision_logic || '';

  // Get recommendation color and icon - Premium Dark Theme
  const getRecommendationStyle = () => {
    if (recommendation === 'approve') {
      return {
        color: 'from-emerald-600 to-teal-700',
        textColor: 'text-emerald-700',
        bgColor: 'bg-gradient-to-br from-emerald-50 to-teal-50',
        borderColor: 'border-emerald-300',
        icon: CheckCircle,
        label: 'Approved'
      };
    } else if (recommendation === 'approve_with_conditions') {
      return {
        color: 'from-amber-500 to-orange-600',
        textColor: 'text-amber-700',
        bgColor: 'bg-gradient-to-br from-amber-50 to-orange-50',
        borderColor: 'border-amber-300',
        icon: AlertTriangle,
        label: 'Conditional Approval'
      };
    } else {
      return {
        color: 'from-rose-500 to-red-600',
        textColor: 'text-rose-700',
        bgColor: 'bg-gradient-to-br from-rose-50 to-red-50',
        borderColor: 'border-rose-300',
        icon: AlertCircle,
        label: 'Review Required'
      };
    }
  };

  const recStyle = getRecommendationStyle();
  const RecommendationIcon = recStyle.icon;

  return (
    <div className="space-y-8 bg-gradient-to-br from-slate-50 to-gray-100 p-8 rounded-3xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl flex items-center justify-center shadow-lg">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">Risk Assessment</h2>
          <p className="text-gray-600 text-sm font-medium">Comprehensive credit risk analysis</p>
        </div>
      </div>

      {/* Credit Score Hero Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`bg-gradient-to-br ${recStyle.color} text-white rounded-3xl p-10 shadow-2xl border border-white/20`}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-4">
              <RecommendationIcon className="w-8 h-8" />
              <span className="text-lg font-semibold opacity-90">Credit Decision</span>
            </div>
            <h3 className="text-5xl font-bold mb-2">{recStyle.label}</h3>
            <p className="text-white/90 text-lg">
              Credit Score: <span className="font-bold">{creditScore}/100</span>
            </p>
          </div>
          
          {/* Circular Score Gauge */}
          <div className="relative w-40 h-40">
            <svg className="transform -rotate-90 w-40 h-40">
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke="rgba(255,255,255,0.2)"
                strokeWidth="12"
                fill="none"
              />
              <motion.circle
                cx="80"
                cy="80"
                r="70"
                stroke="white"
                strokeWidth="12"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 70}`}
                strokeDashoffset={`${2 * Math.PI * 70 * (1 - creditScore / 100)}`}
                initial={{ strokeDashoffset: 2 * Math.PI * 70 }}
                animate={{ strokeDashoffset: 2 * Math.PI * 70 * (1 - creditScore / 100) }}
                transition={{ duration: 1.5, ease: 'easeOut' }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-bold">{creditScore}</span>
              <span className="text-sm opacity-75">Score</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Decision Rationale */}
      {recommendationRationale && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className={`${recStyle.bgColor} border-2 ${recStyle.borderColor} rounded-3xl p-8 shadow-lg backdrop-blur-sm`}
        >
          <h3 className={`text-xl font-bold ${recStyle.textColor} mb-4 flex items-center gap-2`}>
            <Zap className="w-6 h-6" />
            Decision Rationale
          </h3>
          <p className="text-gray-800 leading-relaxed mb-4 text-base">{recommendationRationale}</p>
          
          {decisionLogic && (
            <div className="mt-5 pt-5 border-t-2 border-gray-300/50">
              <p className="text-xs font-bold text-gray-600 mb-2 uppercase tracking-wider">Calculation Method</p>
              <p className="text-sm text-gray-700 font-medium">{decisionLogic}</p>
            </div>
          )}
        </motion.div>
      )}

      {/* Risk Factors Grid */}
      <div>
        <h3 className="text-2xl font-bold text-gray-900 mb-3">Risk Factor Analysis</h3>
        <p className="text-gray-600 text-sm mb-6 font-medium">Click any factor to view detailed breakdown</p>
        
        <div className="grid gap-4">
          {riskFactors.map((factor, index) => {
            const FactorIcon = factor.icon;
            const isExpanded = expandedFactor === factor.name;
            
            return (
              <motion.div
                key={factor.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className={`bg-white border-2 rounded-2xl overflow-hidden transition-all duration-200 ${
                  isExpanded ? 'border-indigo-500 shadow-2xl shadow-indigo-100' : 'border-gray-300 hover:border-indigo-300 hover:shadow-xl'
                }`}
              >
                <div
                  className="p-6 cursor-pointer"
                  onClick={() => setExpandedFactor(isExpanded ? null : factor.name)}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-md ${
                        factor.score >= 70 ? 'bg-gradient-to-br from-emerald-100 to-teal-100' :
                        factor.score >= 40 ? 'bg-gradient-to-br from-amber-100 to-orange-100' :
                        'bg-gradient-to-br from-rose-100 to-red-100'
                      }`}>
                        <FactorIcon className={`w-7 h-7 ${
                          factor.score >= 70 ? 'text-emerald-700' :
                          factor.score >= 40 ? 'text-amber-700' :
                          'text-rose-700'
                        }`} />
                      </div>
                      <div>
                        <h4 className="text-xl font-bold text-gray-900">{factor.name}</h4>
                        <p className="text-sm text-gray-600 font-medium">Weight: {factor.weight}%</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className={`px-5 py-3 rounded-2xl font-bold text-xl shadow-md ${
                        factor.score >= 70 ? 'bg-gradient-to-br from-emerald-100 to-teal-100 text-emerald-800' :
                        factor.score >= 40 ? 'bg-gradient-to-br from-amber-100 to-orange-100 text-amber-800' :
                        'bg-gradient-to-br from-rose-100 to-red-100 text-rose-800'
                      }`}>
                        {factor.score}
                      </div>
                      <motion.div
                        animate={{ rotate: isExpanded ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronDown className="w-6 h-6 text-gray-500" />
                      </motion.div>
                    </div>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden shadow-inner">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${factor.score}%` }}
                      transition={{ duration: 0.8, ease: 'easeOut', delay: index * 0.1 }}
                      className={`h-full shadow-lg ${
                        factor.score >= 70 ? 'bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600' :
                        factor.score >= 40 ? 'bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600' :
                        'bg-gradient-to-r from-rose-500 via-red-500 to-rose-600'
                      }`}
                    />
                  </div>
                </div>
                
                {/* Expanded Content */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                      className="border-t-2 border-gray-100"
                    >
                      <div className="p-6 space-y-4 bg-gradient-to-br from-slate-50 to-gray-100">
                        {/* Assessment */}
                        {factor.assessment && (
                          <div className="bg-white rounded-2xl p-5 border-2 border-gray-200 shadow-md">
                            <p className="text-xs font-bold text-gray-600 mb-2 uppercase tracking-wider">Assessment</p>
                            <p className="text-base text-gray-900 font-semibold">{factor.assessment}</p>
                          </div>
                        )}
                        
                        {/* Detailed Explanation */}
                        {factor.explanation && (
                          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-5 border-l-4 border-indigo-500 shadow-md">
                            <p className="text-xs font-bold text-indigo-900 mb-2 uppercase tracking-wider">Detailed Analysis</p>
                            <p className="text-base text-indigo-900 leading-relaxed font-medium">{factor.explanation}</p>
                          </div>
                        )}
                        
                        {/* Metrics Grid */}
                        {factor.metrics && Object.keys(factor.metrics).length > 0 && (
                          <div>
                            <p className="text-xs font-bold text-gray-600 mb-3 uppercase tracking-wider">Key Metrics</p>
                            <div className="grid grid-cols-2 gap-3">
                              {Object.entries(factor.metrics).map(([key, value]) => (
                                <div key={key} className="bg-white rounded-2xl p-5 border-2 border-gray-200 shadow-md hover:shadow-lg transition-shadow">
                                  <p className="text-xs text-gray-600 capitalize mb-2 font-semibold">{key.replace(/_/g, ' ')}</p>
                                  <p className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                                    {typeof value === 'number' 
                                      ? (value < 1 ? (value * 100).toFixed(1) + '%' : value.toFixed(2))
                                      : Array.isArray(value) 
                                      ? value.map(v => v.toFixed(1) + '%').join(', ')
                                      : value}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Impact Badge */}
                        {factor.impact && (
                          <div>
                            <p className="text-xs font-bold text-gray-600 mb-3 uppercase tracking-wider">Impact on Decision</p>
                            <span className={`inline-flex items-center gap-2 px-5 py-3 text-sm font-bold rounded-2xl shadow-md ${
                              factor.impact?.toLowerCase().includes('positive') || factor.impact?.toLowerCase().includes('very positive')
                                ? 'bg-gradient-to-r from-emerald-100 to-teal-100 text-emerald-800 border-2 border-emerald-300'
                                : factor.impact?.toLowerCase().includes('negative')
                                ? 'bg-gradient-to-r from-rose-100 to-red-100 text-rose-800 border-2 border-rose-300'
                                : 'bg-gradient-to-r from-gray-100 to-slate-100 text-gray-800 border-2 border-gray-300'
                            }`}>
                              {factor.impact?.toLowerCase().includes('positive') ? (
                                <TrendingUp className="w-5 h-5" />
                              ) : factor.impact?.toLowerCase().includes('negative') ? (
                                <TrendingDown className="w-5 h-5" />
                              ) : (
                                <BarChart3 className="w-5 h-5" />
                              )}
                              {factor.impact}
                            </span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Key Insights */}
      {(keyStrengths.length > 0 || keyConcerns.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="space-y-5"
        >
          <h3 className="text-2xl font-bold text-gray-900">Key Insights</h3>
          
          <div className="grid md:grid-cols-2 gap-5">
            {/* Strengths */}
            {keyStrengths.length > 0 && (
              <div className="bg-gradient-to-br from-emerald-50 to-teal-50 border-2 border-emerald-300 rounded-3xl p-7 shadow-lg">
                <h4 className="font-bold text-emerald-900 mb-5 text-xl flex items-center gap-2">
                  <CheckCircle className="w-6 h-6" />
                  Key Strengths
                </h4>
                <ul className="space-y-3">
                  {keyStrengths.map((strength, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-start gap-3 text-sm text-emerald-900 font-medium"
                    >
                      <span className="text-emerald-600 mt-0.5 text-lg">✓</span>
                      <span>{strength}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Concerns */}
            {keyConcerns.length > 0 && (
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-300 rounded-3xl p-7 shadow-lg">
                <h4 className="font-bold text-amber-900 mb-5 text-xl flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6" />
                  Areas to Monitor
                </h4>
                <ul className="space-y-3">
                  {keyConcerns.map((concern, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-start gap-3 text-sm text-amber-900 font-medium"
                    >
                      <span className="text-amber-600 mt-0.5 text-lg">⚠</span>
                      <span>{concern}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default RiskAssessmentTab;
