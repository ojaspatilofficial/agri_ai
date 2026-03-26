import React, { useState, useEffect } from 'react';
import axios from 'axios';

function MarketView({ apiUrl }) {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [crop, setCrop] = useState('wheat');

  useEffect(() => {
    fetchMarketData();
  }, [crop]);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiUrl}/get_market_forecast?crop=${crop}`);
      setMarketData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching market data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>💰 Market Prices & AI Forecast</h2>
          {marketData?.ml_model && (
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <span style={{ 
                fontSize: '0.875rem', 
                color: '#16a34a', 
                fontWeight: '600',
                background: '#f0fdf4',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                border: '1px solid #bbf7d0'
              }}>
                🤖 ML-Powered: {marketData.ml_model.accuracy.accuracy_percentage}% Accurate
              </span>
              <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                {marketData.ml_model.type} | Error: {marketData.ml_model.accuracy.mape}%
              </span>
            </div>
          )}
        </div>
        <select 
          value={crop}
          onChange={(e) => setCrop(e.target.value)}
          style={{ padding: '0.5rem 1rem', borderRadius: '8px', border: '2px solid #e5e7eb', fontSize: '1rem' }}
        >
          <option value="wheat">🌾 Wheat</option>
          <option value="rice">🌾 Rice</option>
          <option value="corn">🌽 Corn</option>
          <option value="cotton">☁️ Cotton</option>
          <option value="potato">🥔 Potato</option>
          <option value="onion">🧅 Onion</option>
          <option value="tomato">🍅 Tomato</option>
        </select>
      </div>

      {/* ML Model Info Banner */}
      {marketData?.ml_model && (
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '1rem 1.5rem',
          borderRadius: '12px',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '0.875rem', opacity: 0.9 }}>Powered by Machine Learning</div>
            <div style={{ fontSize: '1.25rem', fontWeight: '600', marginTop: '0.25rem' }}>
              {marketData.ml_model.type}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.875rem', opacity: 0.9 }}>Data Source</div>
            <div style={{ fontSize: '1rem', fontWeight: '600', marginTop: '0.25rem' }}>
              {marketData.ml_model.data_source}
            </div>
          </div>
        </div>
      )}

      {/* Price Overview */}
      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">💵 Current Price</h3>
          </div>
          <div className="card-content">
            <div className="metric">
              <div className="metric-value">
                ₹{marketData?.current_price?.toFixed(2) || 0}
                <span className="metric-unit">/quintal</span>
              </div>
            </div>
            <div className={`status-badge status-${marketData?.trend === 'rising' ? 'good' : marketData?.trend === 'falling' ? 'critical' : 'fair'}`} style={{ marginTop: '1rem' }}>
              {marketData?.trend === 'rising' ? '📈 Rising' : marketData?.trend === 'falling' ? '📉 Falling' : '➡️ Stable'}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🎯 Best Selling Window</h3>
          </div>
          <div className="card-content">
            <div style={{ marginBottom: '1rem' }}>
              <div className="metric-label">Optimal Date</div>
              <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#16a34a' }}>
                {marketData?.best_selling_window?.date || 'N/A'}
              </div>
            </div>
            <div style={{ marginBottom: '0.5rem' }}>
              <strong>Expected Price:</strong>
              <span style={{ float: 'right' }}>₹{marketData?.best_selling_window?.expected_price || 0}</span>
            </div>
            <div>
              <strong>Potential Gain:</strong>
              <span style={{ 
                float: 'right', 
                color: marketData?.best_selling_window?.potential_gain >= 0 ? '#16a34a' : '#dc2626', 
                fontWeight: '600' 
              }}>
                {marketData?.best_selling_window?.potential_gain >= 0 ? '+' : ''}{marketData?.best_selling_window?.potential_gain?.toFixed(2) || 0}%
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🎯 ML Model Performance</h3>
          </div>
          <div className="card-content">
            {marketData?.ml_model?.accuracy && (
              <>
                <div style={{ marginBottom: '0.5rem' }}>
                  <strong>Accuracy:</strong>
                  <span style={{ float: 'right', color: '#16a34a', fontWeight: '600' }}>
                    {marketData.ml_model.accuracy.accuracy_percentage}%
                  </span>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <strong>Avg Error:</strong>
                  <span style={{ float: 'right' }}>₹{marketData.ml_model.accuracy.mae}/quintal</span>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <strong>Error Rate:</strong>
                  <span style={{ float: 'right' }}>{marketData.ml_model.accuracy.mape}%</span>
                </div>
                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #e5e7eb' }}>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                    R² Score: {marketData.ml_model.accuracy.r2_score}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Market Insights */}
      {marketData?.market_insights && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h3 className="card-title">📊 Market Intelligence</h3>
          </div>
          <div className="card-content">
            <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
              <div>
                <div className="metric-label">Price Volatility</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600' }}>
                  {marketData.market_insights.price_volatility}
                  <span style={{ 
                    fontSize: '0.75rem', 
                    marginLeft: '0.5rem',
                    color: marketData.market_insights.volatility_level === 'high' ? '#dc2626' : 
                           marketData.market_insights.volatility_level === 'medium' ? '#f59e0b' : '#16a34a'
                  }}>
                    ({marketData.market_insights.volatility_level})
                  </span>
                </div>
              </div>
              <div>
                <div className="metric-label">Data Quality</div>
                <div style={{ fontSize: '1rem', fontWeight: '600', marginTop: '0.5rem' }}>
                  {marketData.market_insights.data_quality}
                </div>
              </div>
              <div>
                <div className="metric-label">Prediction Confidence</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#16a34a' }}>
                  {marketData.market_insights.prediction_confidence}%
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Price Forecast Chart */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">📈 30-Day ML Price Forecast</h3>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Predictions with confidence intervals
          </div>
        </div>
        <div className="card-content">
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Date</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>Price (₹)</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>Change %</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Confidence</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>Interval</th>
                </tr>
              </thead>
              <tbody>
                {marketData?.price_forecast?.slice(0, 15).map((forecast, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '0.75rem' }}>{forecast.date}</td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: '600' }}>
                      ₹{forecast.price}
                    </td>
                    <td style={{ 
                      padding: '0.75rem', 
                      textAlign: 'right',
                      color: forecast.change_from_current > 0 ? '#16a34a' : forecast.change_from_current < 0 ? '#dc2626' : '#6b7280',
                      fontWeight: '600'
                    }}>
                      {forecast.change_from_current > 0 ? '+' : ''}{forecast.change_from_current}%
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <span style={{
                        padding: '0.25rem 0.5rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        background: forecast.confidence === 'high' ? '#dcfce7' : 
                                   forecast.confidence === 'medium' ? '#fef3c7' : '#fee2e2',
                        color: forecast.confidence === 'high' ? '#166534' : 
                               forecast.confidence === 'medium' ? '#92400e' : '#991b1b'
                      }}>
                        {forecast.confidence}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.875rem', color: '#6b7280' }}>
                      {forecast.confidence_interval}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#6b7280', textAlign: 'center' }}>
            📊 Showing 15 of {marketData?.price_forecast?.length} predictions
          </div>
        </div>
      </div>

      {/* ML Features Used */}
      {marketData?.ml_model?.features_used && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h3 className="card-title">🔬 ML Features Analyzed</h3>
          </div>
          <div className="card-content">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {marketData.ml_model.features_used.map((feature, index) => (
                <span key={index} style={{
                  padding: '0.5rem 1rem',
                  background: '#f3f4f6',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  color: '#374151',
                  border: '1px solid #e5e7eb'
                }}>
                  ✓ {feature}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">💡 AI-Powered Recommendations</h3>
        </div>
        <div className="card-content">
          <ul className="recommendations">
            {marketData?.recommendations?.map((rec, index) => (
              <li key={index} className="recommendation-item">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Price Factors */}
      {marketData?.market_insights?.price_factors && marketData.market_insights.price_factors.length > 0 && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h3 className="card-title">🔍 Price Influencing Factors</h3>
          </div>
          <div className="card-content">
            <ul style={{ paddingLeft: '1.5rem' }}>
              {marketData.market_insights.price_factors.map((factor, index) => (
                <li key={index} style={{ marginBottom: '0.5rem' }}>{factor}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default MarketView;
