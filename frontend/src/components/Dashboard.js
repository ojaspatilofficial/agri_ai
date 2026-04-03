import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Dashboard({ farmId, apiUrl }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [sensorData, setSensorData] = useState(null);
  const [realtimeRecs, setRealtimeRecs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isRunningAgents, setIsRunningAgents] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    fetchRealtimeRecommendations();
    
    // Refresh dashboard every 30 seconds
    const dashboardInterval = setInterval(fetchDashboardData, 30000);
    
    // Refresh real-time recommendations every 10 seconds
    const recsInterval = setInterval(fetchRealtimeRecommendations, 10000);
    
    return () => {
      clearInterval(dashboardInterval);
      clearInterval(recsInterval);
    };
  }, [farmId, apiUrl]);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${apiUrl}/dashboard?farm_id=${farmId}`);
      setDashboardData(response.data);
      
      if (response.data.sensors) {
        // Handle both single object and array response
        setSensorData(Array.isArray(response.data.sensors) ? response.data.sensors[0] : response.data.sensors);
      }
      
      setLoading(false);
    } catch (error) {
      if (error.code === 'ERR_NETWORK') {
        console.warn('Backend not available - will retry...');
      } else {
        console.error('Error fetching dashboard data:', error);
      }
      setLoading(false);
    }
  };

  const fetchRealtimeRecommendations = async () => {
    try {
      const response = await axios.get(`${apiUrl}/realtime_recommendations?farm_id=${farmId}`);
      setRealtimeRecs(response.data.recommendations || []);
      setLastUpdate(new Date());
    } catch (error) {
      if (error.code !== 'ERR_NETWORK') {
        console.error('Error fetching real-time recommendations:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  const triggerScenario = async (scenario) => {
    try {
      const targetFarmId = farmId || 'FARM001';
      const response = await axios.post(`${apiUrl}/simulate_sensors`, {
        farm_id: targetFarmId,
        duration_minutes: 1
      });
      await fetchDashboardData();
      await fetchRealtimeRecommendations();
      alert(`✅ Sensors simulated successfully for ${scenario} scenario.`);
    } catch (error) {
      alert(`❌ Error simulating sensors: ${error.message}`);
    }
  };

  const handleRunAgents = async () => {
    setIsRunningAgents(true);
    try {
      const targetFarmId = farmId || 'FARM001';
      await axios.post(`${apiUrl}/run_agents?farm_id=${encodeURIComponent(targetFarmId)}`);
      await fetchDashboardData(); 
      alert("✅ Agents successfully executed and recommendations updated!");
    } catch (error) {
      alert(`❌ Error running orchestrator: ${error.message}`);
    }
    setIsRunningAgents(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <h2 style={{ fontSize: '1.75rem', margin: 0 }}>📹 Real-Time Farm Dashboard</h2>
        
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => triggerScenario('test')}
            style={{
              padding: '0.5rem 1rem',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: '600'
            }}
          >
            🔄 Simulate Sensors
          </button>
        </div>
      </div>
      
      {/* Sensor Readings */}
      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">💧 Soil Moisture</h3>
            <span className={`status-badge ${getSoilMoistureStatus(sensorData?.soil_moisture)}`}>
              {getSoilMoistureStatus(sensorData?.soil_moisture)}
            </span>
          </div>
          <div className="card-content">
            <div className="metric">
              <div className="metric-label">Current Level</div>
              <div className="metric-value">
                {sensorData?.soil_moisture?.toFixed(1) || 0}
                <span className="metric-unit">%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🌡️ Temperature</h3>
          </div>
          <div className="card-content">
            <div className="metric">
              <div className="metric-label">Air Temp</div>
              <div className="metric-value">
                {sensorData?.air_temperature?.toFixed(1) || 0}
                <span className="metric-unit">°C</span>
              </div>
            </div>
            <div className="metric" style={{ marginTop: '1rem' }}>
              <div className="metric-label">Soil Temp</div>
              <div className="metric-value" style={{ fontSize: '1.25rem' }}>
                {sensorData?.soil_temperature?.toFixed(1) || 0}
                <span className="metric-unit">°C</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🧪 Soil pH</h3>
          </div>
          <div className="card-content">
            <div className="metric">
              <div className="metric-label">pH Level</div>
              <div className="metric-value">
                {sensorData?.soil_ph?.toFixed(1) || 0}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🌱 NPK Levels</h3>
          </div>
          <div className="card-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span>N: {sensorData?.npk_nitrogen?.toFixed(0) || 0} mg/kg</span>
              <span>P: {sensorData?.npk_phosphorus?.toFixed(0) || 0} mg/kg</span>
              <span>K: {sensorData?.npk_potassium?.toFixed(0) || 0} mg/kg</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Orchestration Card */}
      <div className="card" style={{ marginTop: '1.5rem', border: '2px solid #8b5cf6' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="card-title" style={{ color: '#6d28d9', margin: 0 }}>🧠 AI Orchestrator</h3>
          <button 
            onClick={handleRunAgents} 
            disabled={isRunningAgents}
            style={{
              padding: '0.6rem 1.2rem',
              background: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: isRunningAgents ? 'wait' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {isRunningAgents ? '⏳ Analyzing...' : '🚀 Run Analysis'}
          </button>
        </div>
        <div className="card-content">
          {dashboardData?.recommendations && dashboardData.recommendations.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {dashboardData.recommendations.map((rec, index) => (
                <div key={index} style={{
                  padding: '1rem',
                  background: '#faf5ff',
                  borderLeft: '4px solid #8b5cf6',
                  borderRadius: '8px'
                }}>
                  <p>{rec.recommendation_text}</p>
                  <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#7c3aed' }}>
                    Agent: {rec.agent_name} | {new Date(rec.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
             <div style={{ textAlign: 'center', padding: '2rem', color: '#8b5cf6' }}>
               <p>No recent recommendations. Click 'Run Analysis' to generate new insights.</p>
             </div>
          )}
        </div>
      </div>

      {/* Real-Time Recommendations */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">🤖 Real-Time Alerts</h3>
        </div>
        <div className="card-content">
          {realtimeRecs.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {realtimeRecs.map((rec, index) => (
                <div key={index} style={{
                  padding: '1rem',
                  background: rec.priority === 'critical' ? '#fee2e2' : '#f0fdf4',
                  borderLeft: `4px solid ${rec.priority === 'critical' ? '#ef4444' : '#10b981'}`,
                  borderRadius: '8px'
                }}>
                  <strong>{rec.title}</strong>
                  <p>{rec.message}</p>
                  <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>💡 {rec.action}</p>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '1rem', color: '#10b981' }}>
              ✅ All systems optimal.
            </div>
          )}
        </div>
      </div>

      {/* Green Token Wallet */}
      <div className="token-wallet" style={{ marginTop: '1.5rem' }}>
        <h3>⭐ Green Token Wallet</h3>
        <div className="token-balance">
          {dashboardData?.blockchain?.total_tokens_issued || 0}
        </div>
        <p>Total Tokens Earned</p>
      </div>
    </div>
  );
}

function getSoilMoistureStatus(moisture) {
  if (!moisture) return 'unknown';
  if (moisture >= 50) return 'excellent';
  if (moisture >= 40) return 'good';
  if (moisture >= 30) return 'fair';
  return 'critical';
}

function getPhStatus(ph) {
  if (!ph) return 'unknown';
  if (ph >= 6.0 && ph <= 7.5) return 'good';
  return 'fair';
}

export default Dashboard;
