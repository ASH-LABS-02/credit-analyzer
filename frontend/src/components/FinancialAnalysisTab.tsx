/**
 * FinancialAnalysisTab Component
 * Requirements: 4.1, 4.2, 4.5, 5.1, 5.3, 5.5, 13.2, 13.5
 */

import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Percent, 
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Activity
} from 'lucide-react';
import FinancialChart from './FinancialChart';
import FinancialRatioCard from './FinancialRatioCard';

interface FinancialAnalysisTabProps {
  analysisResults: any;
  loading: boolean;
}

const FinancialAnalysisTab: React.FC<FinancialAnalysisTabProps> = ({
  analysisResults,
  loading,
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mx-auto mb-2"></div>
          <p className="text-gray-600 text-sm">Loading financial analysis...</p>
        </div>
      </div>
    );
  }

  if (!analysisResults || !analysisResults.financial_metrics) {
    return (
      <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
        <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No financial analysis available</p>
      </div>
    );
  }

  const { financial_metrics } = analysisResults;

  // Extract data
  const revenue = financial_metrics.revenue || [];
  const profit = financial_metrics.profit || [];
  const revenueGrowth = financial_metrics.revenue_growth || [];
  const profitGrowth = financial_metrics.profit_growth || [];
  const currentRatio = financial_metrics.current_ratio;
  const debtToEquity = financial_metrics.debt_to_equity;
  const profitMargin = financial_metrics.profit_margin;

  // Calculate latest values
  const latestRevenue = revenue.length > 0 ? revenue[revenue.length - 1] : 0;
  const latestProfit = profit.length > 0 ? profit[profit.length - 1] : 0;
  const latestRevenueGrowth = revenueGrowth.length > 0 ? revenueGrowth[revenueGrowth.length - 1] : 0;
  const latestProfitGrowth = profitGrowth.length > 0 ? profitGrowth[profitGrowth.length - 1] : 0;

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `₹${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `₹${(value / 1000).toFixed(2)}K`;
    }
    return `₹${value.toFixed(2)}`;
  };

  // Format percentage
  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  // Determine analysis period
  const analysisPeriod = revenue.length > 0 ? `${revenue.length} Years` : 'N/A';

  // Build historical data for chart
  const historicalData = revenue.map((rev, index) => ({
    year: `Year ${index + 1}`,
    revenue: rev,
    profit: profit[index] || 0,
  }));

  // Determine financial health
  const strengths = [];
  const concerns = [];

  if (latestRevenueGrowth > 15) {
    strengths.push(`Strong revenue growth of ${formatPercent(latestRevenueGrowth)}`);
  } else if (latestRevenueGrowth < 0) {
    concerns.push(`Declining revenue with ${formatPercent(latestRevenueGrowth)} growth`);
  }

  if (profitMargin && profitMargin > 0.10) {
    strengths.push(`Healthy profit margin of ${(profitMargin * 100).toFixed(1)}%`);
  } else if (profitMargin && profitMargin < 0.05) {
    concerns.push(`Low profit margin of ${(profitMargin * 100).toFixed(1)}%`);
  }

  if (currentRatio && currentRatio > 1.5) {
    strengths.push(`Strong liquidity with current ratio of ${currentRatio.toFixed(2)}`);
  } else if (currentRatio && currentRatio < 1.0) {
    concerns.push(`Weak liquidity with current ratio of ${currentRatio.toFixed(2)}`);
  }

  if (debtToEquity !== undefined && debtToEquity < 0.5) {
    strengths.push(`Conservative debt levels with D/E ratio of ${debtToEquity.toFixed(2)}`);
  } else if (debtToEquity !== undefined && debtToEquity > 1.5) {
    concerns.push(`High leverage with D/E ratio of ${debtToEquity.toFixed(2)}`);
  }

  return (
    <div className="space-y-6">
      {/* Header with Analysis Period */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-black">Financial Analysis</h2>
        <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-bold">
          Analysis Period: {analysisPeriod}
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Latest Revenue */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow-lg"
        >
          <div className="flex items-center justify-between mb-3">
            <DollarSign className="w-8 h-8" />
            {latestRevenueGrowth !== 0 && (
              <span className={`flex items-center text-sm font-bold ${
                latestRevenueGrowth > 0 ? 'text-green-200' : 'text-red-200'
              }`}>
                {latestRevenueGrowth > 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                {formatPercent(latestRevenueGrowth)}
              </span>
            )}
          </div>
          <p className="text-sm opacity-90 mb-1">Latest Revenue</p>
          <p className="text-3xl font-bold">{formatCurrency(latestRevenue)}</p>
        </motion.div>

        {/* Latest Profit */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg shadow-lg"
        >
          <div className="flex items-center justify-between mb-3">
            <TrendingUp className="w-8 h-8" />
            {latestProfitGrowth !== 0 && (
              <span className={`flex items-center text-sm font-bold ${
                latestProfitGrowth > 0 ? 'text-green-200' : 'text-red-200'
              }`}>
                {latestProfitGrowth > 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                {formatPercent(latestProfitGrowth)}
              </span>
            )}
          </div>
          <p className="text-sm opacity-90 mb-1">Latest Profit</p>
          <p className="text-3xl font-bold">{formatCurrency(latestProfit)}</p>
        </motion.div>

        {/* Profit Margin */}
        {profitMargin !== undefined && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow-lg"
          >
            <div className="flex items-center justify-between mb-3">
              <Percent className="w-8 h-8" />
              <span className={`text-sm font-bold ${
                profitMargin > 0.10 ? 'text-green-200' : profitMargin > 0.05 ? 'text-yellow-200' : 'text-red-200'
              }`}>
                {profitMargin > 0.10 ? '✓ Good' : profitMargin > 0.05 ? '⚠ Fair' : '✗ Low'}
              </span>
            </div>
            <p className="text-sm opacity-90 mb-1">Profit Margin</p>
            <p className="text-3xl font-bold">{(profitMargin * 100).toFixed(1)}%</p>
          </motion.div>
        )}

        {/* Growth Trend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gradient-to-br from-orange-500 to-orange-600 text-white p-6 rounded-lg shadow-lg"
        >
          <div className="flex items-center justify-between mb-3">
            <Activity className="w-8 h-8" />
            {latestRevenueGrowth > 0 ? (
              <TrendingUp className="w-6 h-6 text-green-200" />
            ) : (
              <TrendingDown className="w-6 h-6 text-red-200" />
            )}
          </div>
          <p className="text-sm opacity-90 mb-1">Growth Trend</p>
          <p className="text-3xl font-bold">
            {latestRevenueGrowth > 15 ? 'Strong' : latestRevenueGrowth > 5 ? 'Moderate' : latestRevenueGrowth > 0 ? 'Slow' : 'Declining'}
          </p>
        </motion.div>
      </div>

      {/* Year-over-Year Growth Rates */}
      {(revenueGrowth.length > 0 || profitGrowth.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="border-2 border-gray-200 p-6 rounded-lg shadow-sm bg-white"
        >
          <h3 className="text-xl font-bold text-black mb-4 flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            Year-over-Year Growth Rates
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-300">
                  <th className="text-left py-3 px-4 text-sm font-bold text-gray-700">Period</th>
                  <th className="text-right py-3 px-4 text-sm font-bold text-gray-700">Revenue Growth</th>
                  <th className="text-right py-3 px-4 text-sm font-bold text-gray-700">Profit Growth</th>
                </tr>
              </thead>
              <tbody>
                {revenueGrowth.map((growth, index) => (
                  <tr key={index} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-800">
                      Year {index + 1} → Year {index + 2}
                    </td>
                    <td className="text-right py-3 px-4">
                      <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${
                        growth > 15 ? 'bg-green-100 text-green-800' :
                        growth > 5 ? 'bg-blue-100 text-blue-800' :
                        growth > 0 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {formatPercent(growth)}
                      </span>
                    </td>
                    <td className="text-right py-3 px-4">
                      {profitGrowth[index] !== undefined && (
                        <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${
                          profitGrowth[index] > 15 ? 'bg-green-100 text-green-800' :
                          profitGrowth[index] > 5 ? 'bg-blue-100 text-blue-800' :
                          profitGrowth[index] > 0 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {formatPercent(profitGrowth[index])}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Financial Ratios */}
      <div>
        <h3 className="text-xl font-bold text-black mb-4">Key Financial Ratios</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {currentRatio !== undefined && (
            <FinancialRatioCard
              name="Current Ratio"
              value={currentRatio}
              definition="Current Assets / Current Liabilities"
              benchmark={2.0}
              goodRange={{ min: 1.5, max: 3.0 }}
            />
          )}
          {debtToEquity !== undefined && (
            <FinancialRatioCard
              name="Debt to Equity"
              value={debtToEquity}
              definition="Total Debt / Total Equity"
              benchmark={1.0}
              goodRange={{ min: 0, max: 1.5 }}
            />
          )}
          {profitMargin !== undefined && (
            <FinancialRatioCard
              name="Profit Margin"
              value={profitMargin}
              definition="Net Profit / Revenue"
              format="percentage"
              benchmark={0.10}
              goodRange={{ min: 0.10, max: 0.30 }}
            />
          )}
        </div>
      </div>

      {/* Charts */}
      {historicalData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <FinancialChart
            data={historicalData}
            title="Revenue & Profit Trend"
            type="line"
            dataKeys={[
              { key: 'revenue', name: 'Revenue', color: '#3b82f6' },
              { key: 'profit', name: 'Profit', color: '#10b981' },
            ]}
            tooltipFormatter={(value) => formatCurrency(value)}
          />
        </motion.div>
      )}

      {/* Financial Health Summary */}
      {(strengths.length > 0 || concerns.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="space-y-4"
        >
          <h3 className="text-xl font-bold text-black">Financial Health Summary</h3>
          
          {strengths.length > 0 && (
            <div className="border-2 border-green-200 bg-green-50 p-5 rounded-lg">
              <h4 className="font-bold text-green-800 mb-3 text-lg flex items-center gap-2">
                <span className="text-2xl">✓</span> Key Strengths
              </h4>
              <ul className="space-y-2">
                {strengths.map((strength, index) => (
                  <li key={index} className="flex items-start gap-2 text-base text-green-700">
                    <span className="text-green-600 mt-1">•</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {concerns.length > 0 && (
            <div className="border-2 border-yellow-200 bg-yellow-50 p-5 rounded-lg">
              <h4 className="font-bold text-yellow-800 mb-3 text-lg flex items-center gap-2">
                <span className="text-2xl">⚠</span> Areas to Monitor
              </h4>
              <ul className="space-y-2">
                {concerns.map((concern, index) => (
                  <li key={index} className="flex items-start gap-2 text-base text-yellow-700">
                    <span className="text-yellow-600 mt-1">•</span>
                    <span>{concern}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default FinancialAnalysisTab;
