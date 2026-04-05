import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './AgroBrainOS.css';

function AgroBrainOS({ apiUrl, farmId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAgentData, setShowAgentData] = useState(false);
  const [selectedCrop, setSelectedCrop] = useState(null);

  // Copilot
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  const fetchOSData = async (cropType = null) => {
    try {
      setLoading(true);
      setError(null);
      const params = { farm_id: farmId };
      if (cropType || selectedCrop) {
        params.crop_type = cropType || selectedCrop;
      }
      
      const response = await axios.get(`${apiUrl}/agrobrain_os_data`, { params });
      
      if (response.data?.data) {
        setData(response.data.data);
        if (response.data.data.selected_crop && !selectedCrop) {
          setSelectedCrop(response.data.data.selected_crop);
        }
      } else {
        setError('No data returned from server.');
      }
    } catch (err) {
      setError(`Failed to load: ${err.message}`);
      console.error('AgroBrain OS load failed', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOSData(selectedCrop); }, [apiUrl, farmId, selectedCrop]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, chatLoading]);

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim() || chatLoading) return;

    const userMsg = chatMessage.trim();
    const newHistory = [...chatHistory, { role: 'user', text: userMsg }];
    setChatHistory(newHistory);
    setChatMessage('');
    setChatLoading(true);

    try {
      const response = await axios.post(`${apiUrl}/copilot_chat`, {
        farm_id: farmId,
        message: userMsg
      });
      setChatHistory([...newHistory, { role: 'ai', text: response.data.reply }]);
    } catch (err) {
      setChatHistory([...newHistory, {
        role: 'ai',
        text: `⚠️ Network error: ${err.message}. Please check backend is running.`
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleListen = () => {
    if (!data?.advisor_message) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(data.advisor_message);
    utterance.rate = 0.88;
    utterance.lang = 'en-IN';
    window.speechSynthesis.speak(utterance);
  };

  // ── Loading / Error ──────────────────────────────────────────────
  if (loading && !data) {
    return (
      <div className="ab-loading">
        <div className="ab-spinner" />
        <p>AgroBrain OS is analyzing your farm data...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="ab-error">
        <h3>⚠️ Could not load AgroBrain OS</h3>
        <p>{error}</p>
        <button className="ab-btn-refresh" onClick={fetchOSData}>↻ Retry</button>
      </div>
    );
  }

  if (!data || !data.health_score) {
    return <div className="ab-error"><p>No analytics data available. Refresh to try again.</p></div>;
  }

  const alerts = data.smart_alerts || [];
  const agentData = data.agent_data || null;

  return (
    <div className="agrobrain-container">

      {/* ── Header ───────────────────────────────────────────────── */}
      <div className="ab-header">
        <div className="ab-title-group">
          <h2>🧠 AgroBrain OS</h2>
          <p>Your Farm Decision Engine — Powered by Groq AI</p>
        </div>
        <div className="ab-controls" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {data.available_crops && data.available_crops.length > 0 && (
            <select 
              value={selectedCrop || data.selected_crop || data.available_crops[0]} 
              onChange={(e) => setSelectedCrop(e.target.value)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                border: '1px solid #d1d5db',
                background: 'white',
                fontWeight: '500',
                color: '#374151',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {data.available_crops.map(crop => (
                <option key={crop} value={crop}>{crop}</option>
              ))}
            </select>
          )}
          <button className="ab-btn-refresh" onClick={() => fetchOSData(selectedCrop)} disabled={loading}>
            {loading ? '⏳' : '↻'} Refresh
          </button>
        </div>
      </div>

      {/* ── Smart Alerts Bar ─────────────────────────────────────── */}
      {alerts.length > 0 && (
        <div className="ab-alerts-bar">
          {alerts.map((alert, idx) => (
            <div
              key={idx}
              className={`ab-alert-pill ab-alert-${(alert.priority || 'LOW').toLowerCase()}`}
            >
              {alert.priority === 'HIGH' ? '🔴' : alert.priority === 'MEDIUM' ? '🟡' : '🟢'}
              {' '}{alert.message}
            </div>
          ))}
        </div>
      )}

      {/* ── Health Banner ────────────────────────────────────────── */}
      <div
        className="ab-health-banner"
        style={{
          background: data.health_score.score >= 80
            ? 'linear-gradient(135deg, #065f46 0%, #059669 100%)'
            : data.health_score.score >= 60
            ? 'linear-gradient(135deg, #92400e 0%, #d97706 100%)'
            : 'linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%)'
        }}
      >
        <div className="ab-health-score-container">
          <p>Farm Health Score</p>
          <div className="ab-score-value">
            {data.health_score.score}<span>/100</span>
          </div>
          <div className="ab-grade-badge">
            Grade: <strong>{data.health_score.grade}</strong>
          </div>
          <div className="ab-trend">
            📈 {data.health_score.trend}
          </div>
        </div>
        <div className="ab-health-factors">
          <p>Key Factors:</p>
          <ul>
            {(data.health_score.key_factors || []).map((f, i) => (
              <li key={i}>• {f}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* ── Best Action + Advisor ────────────────────────────────── */}
      <div className="ab-quadrants">

        {/* Best Action */}
        <div className="ab-card">
          <div className="ab-card-header">
            <h3>🎯 Best Action</h3>
            <span
              className="ab-urgency-badge"
              style={{
                background: data.best_action.urgency === 'HIGH'
                  ? '#ef4444'
                  : data.best_action.urgency === 'MEDIUM'
                  ? '#f59e0b'
                  : '#10b981'
              }}
            >
              {data.best_action.urgency}
            </span>
          </div>
          <h2 className="ab-action-title">{data.best_action.action}</h2>
          <p className="ab-action-reason">{data.best_action.reasoning}</p>

          <div className="ab-impact-grid">
            <div className="ab-impact-item">
              <p className="ab-impact-label">Yield</p>
              <p className="ab-impact-value">📈 {data.best_action.impact?.yield}</p>
            </div>
            <div className="ab-impact-item">
              <p className="ab-impact-label">Profit</p>
              <p className="ab-impact-value">💰 {data.best_action.impact?.profit}</p>
            </div>
            <div className="ab-impact-item">
              <p className="ab-impact-label">Water</p>
              <p className="ab-impact-value">💧 {data.best_action.impact?.water}</p>
            </div>
            <div className="ab-impact-item">
              <p className="ab-impact-label">Risk</p>
              <p className="ab-impact-value">⚠️ {data.best_action.impact?.risk}</p>
            </div>
          </div>

          <div className="ab-action-buttons">
            <button className="ab-btn-apply">✔️ Apply Now</button>
            <button className="ab-btn-delay">⏳ Delay</button>
            <button className="ab-btn-monitor">👁️ Monitor</button>
          </div>
          <p className="ab-confidence">Confidence: {data.best_action.confidence_pct}%</p>
        </div>

        {/* Advisor */}
        <div className="ab-card">
          <div className="ab-card-header">
            <h3>💬 Your Advisor</h3>
          </div>
          <p className="ab-advisor-text">{data.advisor_message}</p>
          <button className="ab-btn-listen" onClick={handleListen}>
            🔊 Listen
          </button>
          <p className="ab-advisor-footer">AI-generated based on your live farm data.</p>
        </div>
      </div>

      {/* ── Real Agent Data Toggle ───────────────────────────────── */}
      <button
        className="ab-toggle-btn"
        onClick={() => setShowAgentData(!showAgentData)}
      >
        🔍 {showAgentData ? 'Hide' : 'Show'} Real Agent Data
      </button>

      {showAgentData && (
        <>
          {/* 6-Card Agent Grid */}
          {agentData && (
            <div className="ab-agent-grid">

              <div className="ab-agent-card ab-ac-soil">
                <h4>🌱 Soil Analysis</h4>
                <div className="ab-ac-grid-2">
                  <div className="ab-ac-item"><span>Moisture:</span> <strong>{agentData.soil_analysis?.moisture}</strong></div>
                  <div className="ab-ac-item"><span>pH:</span> <strong>{agentData.soil_analysis?.ph}</strong></div>
                  <div className="ab-ac-item"><span>Nitrogen:</span> {agentData.soil_analysis?.nitrogen}</div>
                  <div className="ab-ac-item"><span>Phosphorus:</span> {agentData.soil_analysis?.phosphorus}</div>
                  <div className="ab-ac-item"><span>Potassium:</span> {agentData.soil_analysis?.potassium}</div>
                  <div className="ab-ac-item"><span>Quality:</span> <strong>{agentData.soil_analysis?.quality}</strong></div>
                </div>
              </div>

              <div className="ab-agent-card ab-ac-water">
                <h4>💧 Water Management</h4>
                <div className="ab-ac-grid-1">
                  <div className="ab-ac-item"><span>Need Irrigation:</span> <strong>{agentData.water_management?.need_irrigation}</strong></div>
                  <div className="ab-ac-item"><span>Duration:</span> {agentData.water_management?.duration}</div>
                  <div className="ab-ac-item"><span>Volume:</span> {agentData.water_management?.volume}</div>
                  <div className="ab-ac-item"><span>Reason:</span> {agentData.water_management?.reason}</div>
                </div>
              </div>

              <div className="ab-agent-card ab-ac-disease">
                <h4>🦠 Disease Risk</h4>
                <div className="ab-ac-grid-1">
                  <div className="ab-ac-item"><span>Disease Detected:</span> <strong>{agentData.disease_risk?.disease_detected}</strong></div>
                  <div className="ab-ac-item">
                    <span>Risk Level:</span>
                    <strong style={{ color: agentData.disease_risk?.risk_level === 'none' ? '#059669' : agentData.disease_risk?.risk_level === 'high' ? '#dc2626' : '#d97706' }}>
                      {' '}{agentData.disease_risk?.risk_level}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="ab-agent-card ab-ac-yield">
                <h4>🌾 Yield Prediction</h4>
                <div className="ab-ac-grid-1">
                  <div className="ab-ac-item"><span>Expected Yield:</span> <strong>{agentData.yield_prediction?.expected_yield}</strong></div>
                  <div className="ab-ac-item"><span>Harvest Date:</span> {agentData.yield_prediction?.harvest_date}</div>
                  <div className="ab-ac-item"><span>Days to Harvest:</span> {agentData.yield_prediction?.days_to_harvest}</div>
                  <div className="ab-ac-item"><span>Market Value:</span> <strong>{agentData.yield_prediction?.market_value}</strong></div>
                </div>
              </div>

              <div className="ab-agent-card ab-ac-market">
                <h4>💰 Market Prices</h4>
                <div className="ab-ac-grid-1">
                  <div className="ab-ac-item"><span>Current Price:</span> <strong>{agentData.market_prices?.current_price}</strong></div>
                  <div className="ab-ac-item"><span>Trend:</span> {agentData.market_prices?.trend}</div>
                  <div className="ab-ac-item"><span>Best Sell Window:</span> {agentData.market_prices?.best_sell_window}</div>
                  <div className="ab-ac-item"><span>Expected Price:</span> {agentData.market_prices?.expected_price}</div>
                </div>
              </div>

              <div className="ab-agent-card ab-ac-sus">
                <h4>🌿 Sustainability</h4>
                <div className="ab-ac-grid-1">
                  <div className="ab-ac-item"><span>Green Score:</span> <strong>{agentData.sustainability?.green_score}</strong></div>
                  <div className="ab-ac-item"><span>Carbon Rating:</span> {agentData.sustainability?.carbon_rating}</div>
                  <div className="ab-ac-item"><span>Water Efficiency:</span> {agentData.sustainability?.water_efficiency}</div>
                </div>
              </div>

            </div>
          )}

          {/* What-If Comparison */}
          <div className="ab-card">
            <h3>⚖️ What-If Comparison</h3>
            <div className="ab-whatif-grid">
              <div className="ab-whatif-card ab-whatif-now">
                <h4 style={{ color: '#059669' }}>✅ Act Now</h4>
                <ul>
                  <li>📈 Yield: <strong>{data.what_if?.act_now?.yield}</strong></li>
                  <li>💰 Profit: <strong>{data.what_if?.act_now?.profit}</strong></li>
                  <li>💧 Water: {data.what_if?.act_now?.water}</li>
                  <li>⚠️ Risk: {data.what_if?.act_now?.risk}</li>
                </ul>
              </div>
              <div className="ab-whatif-card ab-whatif-wait">
                <h4 style={{ color: '#6b7280' }}>⏸️ Wait</h4>
                <ul>
                  <li>📈 Yield: <strong>{data.what_if?.wait?.yield}</strong></li>
                  <li>💰 Profit: <strong>{data.what_if?.wait?.profit}</strong></li>
                  <li>💧 Water: {data.what_if?.wait?.water}</li>
                  <li>⚠️ Risk: {data.what_if?.wait?.risk}</li>
                </ul>
              </div>
            </div>
          </div>
        </>
      )}

      {/* ── Farm Copilot (ALWAYS VISIBLE) ───────────────────────── */}
      <div className="ab-copilot">
        <div className="ab-copilot-header">
          <h3>🌾 Farm Copilot</h3>
          <span className="ab-copilot-badge">Powered by Groq AI</span>
        </div>

        <div className="ab-copilot-chat" style={{ minHeight: chatHistory.length === 0 ? '120px' : '200px' }}>
          {chatHistory.length === 0 ? (
            <div className="ab-copilot-placeholder">
              <p>Ask me anything about your farm!</p>
              <div className="ab-quick-questions">
                {['Should I irrigate today?', 'When to harvest?', 'Aaj kya karu?', 'What is my soil health?'].map((q) => (
                  <button
                    key={q}
                    className="ab-quick-btn"
                    onClick={() => {
                      setChatMessage(q);
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            chatHistory.map((msg, idx) => (
              <div
                key={idx}
                className={`ab-chat-msg ${msg.role === 'user' ? 'ab-chat-farmer' : 'ab-chat-ai'}`}
              >
                {msg.role === 'ai' && <span className="ab-chat-avatar">🧠</span>}
                <span>{msg.text}</span>
              </div>
            ))
          )}
          {chatLoading && (
            <div className="ab-chat-msg ab-chat-ai">
              <span className="ab-chat-avatar">🧠</span>
              <span className="ab-typing">Analyzing your farm data...</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <form className="ab-copilot-input" onSubmit={handleChatSubmit}>
          <input
            type="text"
            placeholder="Ask: 'Should I irrigate?' or 'Aaj kya karu?'"
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            disabled={chatLoading}
          />
          <button type="submit" disabled={chatLoading || !chatMessage.trim()}>
            {chatLoading ? '⏳' : 'Send'}
          </button>
        </form>
      </div>

    </div>
  );
}

export default AgroBrainOS;
