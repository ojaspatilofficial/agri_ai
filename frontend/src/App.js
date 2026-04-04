import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import WeatherView from './components/WeatherView';
import MarketView from './components/MarketView';
import BlockchainView from './components/BlockchainViewEnhanced';
import VoiceAssistant from './components/VoiceAssistant';
import CropsManager from './components/CropsManager';
import ActionsLog from './components/ActionsLog';
import SatelliteView from './components/SatelliteView';
import ProfileView from './components/ProfileView';
import LanguageSelector from './components/LanguageSelector';
import AgroBrainOS from './components/AgroBrainOS';
import { useLanguage } from './context/LanguageContext';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const getFarmIdFromFarmer = (farmerData) => {
  if (!farmerData) return 'FARM001';
  return farmerData.farmerId || farmerData.farmer_id || 'FARM001';
};

function App() {
  const { t } = useLanguage();
  const [farmer, setFarmer] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [farmId, setFarmId] = useState('FARM001');
  const [loading, setLoading] = useState(false);

  // Check if farmer is already logged in
  useEffect(() => {
    const storedFarmer = localStorage.getItem('farmer');
    if (storedFarmer) {
      const parsedFarmer = JSON.parse(storedFarmer);
      setFarmer(parsedFarmer);
      setFarmId(getFarmIdFromFarmer(parsedFarmer));
    }
  }, []);

  const handleLogin = (farmerData) => {
    setFarmer(farmerData);
    setFarmId(getFarmIdFromFarmer(farmerData));
  };

  const handleLogout = () => {
    localStorage.removeItem('farmer');
    setFarmer(null);
    setActiveTab('dashboard');
  };

  // Initialize sensor data on load
  useEffect(() => {
    if (farmer) {
      initializeSensors(getFarmIdFromFarmer(farmer));
    }
  }, [farmer]);

  const initializeSensors = async (targetFarmId = farmId) => {
    try {
      await axios.post(`${API_BASE_URL}/simulate_sensors`, {
        farm_id: targetFarmId,
        duration_minutes: 10
      });
    } catch (error) {
      // Silently handle - backend may not be running yet
      if (error.code === 'ERR_NETWORK') {
        console.warn('Backend not available - sensors will be initialized when backend starts');
      } else {
        console.error('Error initializing sensors:', error);
      }
    }
  };

  const handleRunAgents = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/run_agents?farm_id=${farmId}`);
      if (response.data && response.data.error) {
        alert('⚠️ ' + response.data.error);
      } else {
        alert('✅ All AI agents executed successfully! Check the dashboard for recommendations.');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      if (error.code === 'ERR_NETWORK') {
        alert('❌ Network Error: Backend server is not running.\n\nPlease start the backend server:\n1. Open a terminal in the backend folder\n2. Run: python main.py');
      } else {
        alert('❌ Error running agents: ' + errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  // Show login page if not authenticated
  if (!farmer) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div>
          <h1>🌾 Smart Farming AI System</h1>
          <p>{t('welcome')}, {farmer.name} | {t('farmId')}: {farmId}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <LanguageSelector />
          <button 
            onClick={handleLogout}
            style={{
              padding: '0.5rem 1.5rem',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => e.target.style.background = '#dc2626'}
            onMouseLeave={(e) => e.target.style.background = '#ef4444'}
          >
            🚪 {t('logout')}
          </button>
        </div>
      </header>

      {/* Navigation */}
      <nav className="nav">
        <button 
          className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 {t('dashboard')}
        </button>
        <button 
          className={`nav-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          🧠 AgroBrain OS
        </button>
        <button 
          className={`nav-btn ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          👤 {t('profile')}
        </button>
        <button 
          className={`nav-btn ${activeTab === 'crops' ? 'active' : ''}`}
          onClick={() => setActiveTab('crops')}
        >
          🌾 {t('crops')}
        </button>
        <button 
          className={`nav-btn ${activeTab === 'actions' ? 'active' : ''}`}
          onClick={() => setActiveTab('actions')}
        >
          📝 {t('actionsLog')}
        </button>
        <button 
          className={`nav-btn ${activeTab === 'weather' ? 'active' : ''}`}
          onClick={() => setActiveTab('weather')}
        >
          🌤️ {t('weather')}
        </button>
        <button 
          className={`nav-btn ${activeTab === 'market' ? 'active' : ''}`}
          onClick={() => setActiveTab('market')}
        >
          💰 {t('market')}
        </button>
        <button 
          className={`nav-btn ${activeTab === 'satellite' ? 'active' : ''}`}
          onClick={() => setActiveTab('satellite')}
        >
          🛰️ {t('satellite')}
        </button>
        <button 
          className={`nav-btn ${activeTab === 'blockchain' ? 'active' : ''}`}
          onClick={() => setActiveTab('blockchain')}
        >
          🌟 {t('greenTokens')}
        </button>
        <button 
          className="nav-btn"
          onClick={handleRunAgents}
          disabled={loading}
          style={{
            background: loading ? '#9ca3af' : '#f3f4f6',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1
          }}
        >
          {loading ? '⏳ ' + t('loading') : '🤖 ' + t('runAllAgents')}
        </button>
      </nav>

      {/* Main Content */}
      <div className="container">
        {activeTab === 'dashboard' && <Dashboard farmId={farmId} apiUrl={API_BASE_URL} />}
        {activeTab === 'analytics' && <AgroBrainOS farmId={farmId} apiUrl={API_BASE_URL} />}
        {activeTab === 'profile' && <ProfileView farmer={farmer} apiUrl={API_BASE_URL} />}
        {activeTab === 'crops' && <CropsManager />}
        {activeTab === 'actions' && <ActionsLog />}
        {activeTab === 'weather' && <WeatherView apiUrl={API_BASE_URL} />}
        {activeTab === 'market' && <MarketView apiUrl={API_BASE_URL} />}
        {activeTab === 'satellite' && <SatelliteView farmId={farmId} apiUrl={API_BASE_URL} />}
        {activeTab === 'blockchain' && <BlockchainView apiUrl={API_BASE_URL} farmId={farmId} />}
      </div>

      {/* Voice Assistant */}
      <VoiceAssistant apiUrl={API_BASE_URL} farmer={farmer} />
    </div>
  );
}

export default App;
