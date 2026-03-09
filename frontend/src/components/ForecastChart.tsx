/**
 * Forecast Chart Component
 * 
 * Displays historical and projected financial data with confidence intervals.
 * Shows assumptions and methodology with interactive filtering.
 * 
 * Requirements: 5.1, 5.3, 5.5, 13.2
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart } from 'recharts';
import { motion } from 'framer-motion';
import { Info } from 'lucide-react';
import { useState } from 'react';

interface ForecastDataPoint {
  year: string;
  actual?: number;
  projected?: number;
  confidenceUpper?: number;
  confidenceLower?: number;
}

interface ForecastChartProps {
  data: ForecastDataPoint[];
  title: string;
  yAxisLabel?: string;
  formatValue?: (value: number) => string;
  assumptions?: string[];
  methodology?: string;
  confidenceLevel?: number;
}

const ForecastChart = ({
  data,
  title,
  yAxisLabel,
  formatValue = (value) => `$${value.toLocaleString()}`,
  assumptions = [],
  methodology,
  confidenceLevel = 95,
}: ForecastChartProps) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white border-2 border-gray-200 p-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-black">{title}</h3>
          <p className="text-xs text-gray-600 mt-1">
            Historical data (solid) and {confidenceLevel}% confidence interval (shaded)
          </p>
        </div>
        {(assumptions.length > 0 || methodology) && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-black transition-colors"
          >
            <Info className="w-4 h-4" />
            {showDetails ? 'Hide' : 'Show'} Details
          </button>
        )}
      </div>

      {/* Assumptions and Methodology */}
      {showDetails && (assumptions.length > 0 || methodology) && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mb-4 p-4 bg-gray-50 border-2 border-gray-200"
        >
          {methodology && (
            <div className="mb-3">
              <h4 className="text-sm font-bold text-black mb-1">Methodology</h4>
              <p className="text-sm text-gray-700">{methodology}</p>
            </div>
          )}
          {assumptions.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-black mb-1">Key Assumptions</h4>
              <ul className="list-disc list-inside space-y-1">
                {assumptions.map((assumption, index) => (
                  <li key={index} className="text-sm text-gray-700">
                    {assumption}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="year"
            stroke="#6b7280"
            style={{ fontSize: '12px', fontWeight: 500 }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '12px', fontWeight: 500 }}
            label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined}
            tickFormatter={formatValue}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '2px solid black',
              borderRadius: 0,
              padding: '8px 12px',
            }}
            labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
            formatter={(value: number, name: string) => {
              const labels: Record<string, string> = {
                actual: 'Actual',
                projected: 'Projected',
                confidenceUpper: 'Upper Bound',
                confidenceLower: 'Lower Bound',
              };
              return [formatValue(value), labels[name] || name];
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          
          {/* Confidence interval area */}
          <Area
            type="monotone"
            dataKey="confidenceUpper"
            stroke="none"
            fill="#93c5fd"
            fillOpacity={0.3}
            name="Confidence Interval"
          />
          <Area
            type="monotone"
            dataKey="confidenceLower"
            stroke="none"
            fill="#93c5fd"
            fillOpacity={0.3}
          />
          
          {/* Actual historical data */}
          <Line
            type="monotone"
            dataKey="actual"
            name="Historical"
            stroke="#1f2937"
            strokeWidth={3}
            dot={{ fill: '#1f2937', r: 5 }}
            activeDot={{ r: 7 }}
            connectNulls={false}
          />
          
          {/* Projected data */}
          <Line
            type="monotone"
            dataKey="projected"
            name="Forecast"
            stroke="#3b82f6"
            strokeWidth={3}
            strokeDasharray="5 5"
            dot={{ fill: '#3b82f6', r: 5 }}
            activeDot={{ r: 7 }}
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Legend explanation */}
      <div className="mt-4 flex items-center gap-6 text-xs text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-8 h-0.5 bg-gray-800"></div>
          <span>Historical Data</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-0.5 bg-blue-500 border-dashed border-t-2 border-blue-500"></div>
          <span>Projected Data</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-3 bg-blue-200 opacity-50"></div>
          <span>{confidenceLevel}% Confidence Interval</span>
        </div>
      </div>
    </motion.div>
  );
};

export default ForecastChart;
