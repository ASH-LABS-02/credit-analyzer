/**
 * NewsInsightsTab Component - Premium Design
 * 
 * Displays company news with sentiment analysis and detailed AI insights
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Newspaper,
  AlertCircle,
  Loader,
  X,
  ExternalLink,
  Calendar,
  User,
  BarChart3,
  Zap
} from 'lucide-react';

interface NewsInsightsTabProps {
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

const NewsInsightsTab: React.FC<NewsInsightsTabProps> = ({
  applicationId,
  companyName
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newsData, setNewsData] = useState<any>(null);
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
  const [showNewsModal, setShowNewsModal] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [newsDetails, setNewsDetails] = useState<any>(null);

  useEffect(() => {
    fetchNews();
  }, [applicationId]);

  const fetchNews = async () => {
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
        throw new Error('Failed to fetch news');
      }

      const data = await response.json();
      setNewsData(data.news);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load news');
    } finally {
      setLoading(false);
    }
  };

  const handleNewsClick = async (newsItem: NewsItem) => {
    setSelectedNews(newsItem);
    setShowNewsModal(true);
    setLoadingDetails(true);
    setNewsDetails(null);

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
            news_url: newsItem.url || '',
            news_title: newsItem.title,
            news_description: newsItem.full_description || newsItem.summary,
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
      setNewsDetails({ error: 'Failed to load detailed analysis' });
    } finally {
      setLoadingDetails(false);
    }
  };

  const closeNewsModal = () => {
    setShowNewsModal(false);
    setSelectedNews(null);
    setNewsDetails(null);
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.5) return 'bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-300 text-emerald-900';
    if (score > 0) return 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-300 text-blue-900';
    if (score > -0.5) return 'bg-gradient-to-br from-amber-50 to-orange-50 border-amber-300 text-amber-900';
    return 'bg-gradient-to-br from-rose-50 to-red-50 border-rose-300 text-rose-900';
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
          <p className="text-gray-600">Loading news insights...</p>
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
        <h3 className="text-xl font-bold text-gray-900 mb-2">Failed to Load News</h3>
        <p className="text-gray-600 mb-6">{error}</p>
        <button
          onClick={fetchNews}
          className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors"
        >
          Try Again
        </button>
      </motion.div>
    );
  }

  if (!newsData) {
    return (
      <div className="text-center py-16">
        <Newspaper className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No news available</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 bg-gradient-to-br from-slate-50 to-gray-100 p-8 rounded-3xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl flex items-center justify-center shadow-lg">
          <Newspaper className="w-7 h-7 text-white" />
        </div>
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            News & Sentiment Analysis
          </h2>
          <p className="text-gray-600 text-sm font-medium">{companyName}</p>
        </div>
      </div>

      {/* News Grid */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* Positive News */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900">Positive News</h3>
            <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-sm font-bold">
              {newsData.positive?.length || 0}
            </span>
          </div>
          
          <div className="space-y-4">
            {newsData.positive?.map((item: NewsItem, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => handleNewsClick(item)}
                className={`rounded-2xl border-2 p-5 ${getSentimentColor(item.sentiment_score)} hover:shadow-xl transition-all duration-200 cursor-pointer`}
              >
                <div className="flex items-start justify-between mb-3">
                  <h4 className="font-bold text-base flex-1 leading-tight">{item.title}</h4>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleNewsClick(item);
                    }}
                    className="text-xs text-indigo-600 hover:text-indigo-800 ml-2 flex items-center gap-1 font-semibold"
                  >
                    Details
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
                
                <p className="text-sm text-gray-700 mb-4 leading-relaxed">
                  {item.full_description || item.summary}
                </p>
                
                {item.sentiment_reasoning && (
                  <div className="mb-4 p-3 bg-white/60 rounded-xl border border-emerald-200">
                    <p className="text-xs text-gray-700">
                      <span className="font-bold text-emerald-800">AI Analysis:</span> {item.sentiment_reasoning}
                    </p>
                  </div>
                )}
                
                <div className="flex items-center justify-between text-xs mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-700 font-semibold">{item.source}</span>
                    {item.author && item.author !== "Unknown" && (
                      <>
                        <span className="text-gray-400">•</span>
                        <span className="text-gray-600">{item.author}</span>
                      </>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-gray-600">
                    <Calendar className="w-3 h-3" />
                    <span>{new Date(item.date).toLocaleDateString()}</span>
                  </div>
                </div>
                
                {item.sentiment_score && (
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-white/50 rounded-full overflow-hidden shadow-inner">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-teal-600 shadow-lg"
                        style={{ width: `${Math.abs(item.sentiment_score) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-emerald-700">
                      +{(item.sentiment_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Negative News */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-rose-100 rounded-xl flex items-center justify-center">
              <TrendingDown className="w-5 h-5 text-rose-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900">Negative News</h3>
            <span className="px-3 py-1 bg-rose-100 text-rose-800 rounded-full text-sm font-bold">
              {newsData.negative?.length || 0}
            </span>
          </div>
          
          <div className="space-y-4">
            {newsData.negative?.map((item: NewsItem, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => handleNewsClick(item)}
                className={`rounded-2xl border-2 p-5 ${getSentimentColor(item.sentiment_score)} hover:shadow-xl transition-all duration-200 cursor-pointer`}
              >
                <div className="flex items-start justify-between mb-3">
                  <h4 className="font-bold text-base flex-1 leading-tight">{item.title}</h4>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleNewsClick(item);
                    }}
                    className="text-xs text-indigo-600 hover:text-indigo-800 ml-2 flex items-center gap-1 font-semibold"
                  >
                    Details
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
                
                <p className="text-sm text-gray-700 mb-4 leading-relaxed">
                  {item.full_description || item.summary}
                </p>
                
                {item.sentiment_reasoning && (
                  <div className="mb-4 p-3 bg-white/60 rounded-xl border border-rose-200">
                    <p className="text-xs text-gray-700">
                      <span className="font-bold text-rose-800">AI Analysis:</span> {item.sentiment_reasoning}
                    </p>
                  </div>
                )}
                
                <div className="flex items-center justify-between text-xs mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-700 font-semibold">{item.source}</span>
                    {item.author && item.author !== "Unknown" && (
                      <>
                        <span className="text-gray-400">•</span>
                        <span className="text-gray-600">{item.author}</span>
                      </>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-gray-600">
                    <Calendar className="w-3 h-3" />
                    <span>{new Date(item.date).toLocaleDateString()}</span>
                  </div>
                </div>
                
                {item.sentiment_score && (
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-white/50 rounded-full overflow-hidden shadow-inner">
                      <div
                        className="h-full bg-gradient-to-r from-rose-500 to-red-600 shadow-lg"
                        style={{ width: `${Math.abs(item.sentiment_score) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-rose-700">
                      {(item.sentiment_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* News Source Attribution */}
      <div className="mt-8 p-5 bg-white rounded-2xl border-2 border-gray-200 shadow-md">
        <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
          <BarChart3 className="w-4 h-4" />
          <span>
            News powered by <span className="font-bold text-gray-900">{newsData.source || 'NewsAPI'}</span>
            {newsData.api_status === 'fallback' && ' (AI Generated)'}
          </span>
          <span className="text-gray-400">•</span>
          <span>Last updated: {new Date(newsData.last_updated).toLocaleString()}</span>
        </div>
      </div>

      {/* Detailed News Modal */}
      <AnimatePresence>
        {showNewsModal && selectedNews && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={closeNewsModal}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl shadow-2xl border-2 border-gray-200 max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            >
              {/* Modal Header */}
              <div className="sticky top-0 bg-gradient-to-br from-white to-gray-50 border-b-2 border-gray-200 p-8 rounded-t-3xl z-10">
                <div className="flex items-start justify-between">
                  <div className="flex-1 pr-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className={`px-4 py-2 rounded-xl text-sm font-bold shadow-md ${
                        selectedNews.sentiment_score > 0 
                          ? 'bg-emerald-100 text-emerald-800' 
                          : 'bg-rose-100 text-rose-800'
                      }`}>
                        {selectedNews.sentiment_label || (selectedNews.sentiment_score > 0 ? 'Positive' : 'Negative')}
                      </span>
                      <span className="text-sm text-gray-600 font-medium">{selectedNews.source}</span>
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900 leading-tight mb-2">
                      {selectedNews.title}
                    </h2>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      {selectedNews.author && selectedNews.author !== "Unknown" && (
                        <div className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          <span>{selectedNews.author}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(selectedNews.date).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={closeNewsModal}
                    className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-xl flex items-center justify-center transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="p-8 space-y-6">
                {/* Loading State */}
                {loadingDetails && (
                  <div className="text-center py-12">
                    <Loader className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
                    <p className="text-gray-600 font-medium">Generating detailed analysis...</p>
                  </div>
                )}

                {/* Detailed Analysis */}
                {!loadingDetails && newsDetails?.detailed_analysis && (
                  <div className="space-y-6">
                    {/* Executive Summary */}
                    {newsDetails.detailed_analysis.executive_summary && (
                      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-6 border-2 border-indigo-200">
                        <div className="flex items-center gap-2 mb-3">
                          <Zap className="w-5 h-5 text-indigo-600" />
                          <h3 className="text-lg font-bold text-indigo-900">Executive Summary</h3>
                        </div>
                        <p className="text-indigo-900 leading-relaxed font-medium">
                          {newsDetails.detailed_analysis.executive_summary}
                        </p>
                      </div>
                    )}

                    {/* Key Points */}
                    {newsDetails.detailed_analysis.key_points && newsDetails.detailed_analysis.key_points.length > 0 && (
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 mb-3">Key Points</h3>
                        <ul className="space-y-2">
                          {newsDetails.detailed_analysis.key_points.map((point: string, index: number) => (
                            <li key={index} className="flex items-start gap-3 text-gray-700">
                              <span className="text-indigo-600 mt-1">•</span>
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Financial Implications */}
                    {newsDetails.detailed_analysis.financial_implications && (
                      <div className="bg-white rounded-2xl border-2 border-gray-200 p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Financial Implications</h3>
                        <div className="grid md:grid-cols-2 gap-4">
                          {Object.entries(newsDetails.detailed_analysis.financial_implications).map(([key, value]: [string, any]) => (
                            <div key={key} className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                              <p className="text-xs font-bold text-gray-600 mb-2 uppercase tracking-wider">
                                {key.replace(/_/g, ' ')}
                              </p>
                              <p className="text-sm text-gray-900">{value}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Risk Assessment */}
                    {newsDetails.detailed_analysis.risk_assessment && (
                      <div className="bg-white rounded-2xl border-2 border-gray-200 p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Risk Assessment</h3>
                        <div className="grid md:grid-cols-2 gap-4">
                          {Object.entries(newsDetails.detailed_analysis.risk_assessment).map(([key, value]: [string, any]) => {
                            const riskLevel = value.toLowerCase();
                            const riskColor = 
                              riskLevel.includes('high') || riskLevel.includes('critical')
                                ? 'bg-rose-50 border-rose-200 text-rose-700'
                                : riskLevel.includes('medium')
                                ? 'bg-amber-50 border-amber-200 text-amber-700'
                                : 'bg-emerald-50 border-emerald-200 text-emerald-700';
                            
                            return (
                              <div key={key} className={`rounded-xl p-4 border-2 ${riskColor}`}>
                                <p className="text-xs font-bold mb-2 uppercase tracking-wider">
                                  {key.replace(/_/g, ' ')}
                                </p>
                                <p className="text-sm font-medium">{value}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {newsDetails.detailed_analysis.recommendations && (
                      <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl border-2 border-purple-200 p-6">
                        <h3 className="text-lg font-bold text-purple-900 mb-4">Recommendations</h3>
                        <div className="space-y-4">
                          {newsDetails.detailed_analysis.recommendations.for_lenders && (
                            <div>
                              <p className="text-sm font-bold text-purple-800 mb-2">For Lenders:</p>
                              <p className="text-sm text-purple-900">{newsDetails.detailed_analysis.recommendations.for_lenders}</p>
                            </div>
                          )}
                          {newsDetails.detailed_analysis.recommendations.for_investors && (
                            <div>
                              <p className="text-sm font-bold text-purple-800 mb-2">For Investors:</p>
                              <p className="text-sm text-purple-900">{newsDetails.detailed_analysis.recommendations.for_investors}</p>
                            </div>
                          )}
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

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  {selectedNews.url && (
                    <motion.a
                      href={selectedNews.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl font-bold hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg"
                    >
                      Read Full Article
                      <ExternalLink className="w-5 h-5" />
                    </motion.a>
                  )}
                  <motion.button
                    onClick={closeNewsModal}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="px-6 py-4 border-2 border-gray-300 rounded-2xl text-gray-700 font-bold hover:bg-gray-50 transition-all duration-200"
                  >
                    Close
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NewsInsightsTab;
