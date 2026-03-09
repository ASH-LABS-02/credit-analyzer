/**
 * FinancialRatioCard Component
 * 
 * Displays a financial ratio with definition and benchmark comparison
 * 
 * Requirements: 4.1, 4.5, 13.2
 */

import { motion } from 'framer-motion';
import { Info } from 'lucide-react';
import { useState } from 'react';

interface FinancialRatioCardProps {
  name: string;
  value: number;
  definition: string;
  benchmark?: number;
  format?: 'number' | 'percentage' | 'currency';
  goodRange?: { min: number; max: number };
}

const FinancialRatioCard: React.FC<FinancialRatioCardProps> = ({
  name,
  value,
  definition,
  benchmark,
  format = 'number',
  goodRange,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const formatValue = (val: number) => {
    switch (format) {
      case 'percentage':
        return `${(val * 100).toFixed(1)}%`;
      case 'currency':
        return `$${val.toLocaleString()}`;
      default:
        return val.toFixed(2);
    }
  };

  const getStatusColor = () => {
    if (!goodRange) return 'text-black';
    if (value >= goodRange.min && value <= goodRange.max) return 'text-green-600';
    return 'text-yellow-600';
  };

  const getBenchmarkComparison = () => {
    if (!benchmark) return null;
    const diff = ((value - benchmark) / benchmark) * 100;
    const isPositive = diff > 0;
    return (
      <p className="text-xs text-gray-600 mt-1">
        {isPositive ? '+' : ''}{diff.toFixed(1)}% vs industry avg ({formatValue(benchmark)})
      </p>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="border-2 border-gray-200 p-4 hover:border-black transition-colors relative"
    >
      <div className="flex items-start justify-between mb-2">
        <p className="text-sm font-medium text-gray-700">{name}</p>
        <button
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          className="text-gray-400 hover:text-black transition-colors"
        >
          <Info className="w-4 h-4" />
        </button>
      </div>
      
      <p className={`text-2xl font-bold ${getStatusColor()}`}>
        {formatValue(value)}
      </p>
      
      {getBenchmarkComparison()}
      
      {showTooltip && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute z-10 top-full left-0 right-0 mt-2 bg-white border-2 border-black p-3 shadow-lg"
        >
          <p className="text-xs text-gray-700">{definition}</p>
          {goodRange && (
            <p className="text-xs text-gray-600 mt-2">
              Good range: {formatValue(goodRange.min)} - {formatValue(goodRange.max)}
            </p>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};

export default FinancialRatioCard;
