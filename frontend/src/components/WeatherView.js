import React, { useState, useEffect } from 'react';
import axios from 'axios';

function WeatherView({ apiUrl }) {
  const [weatherData, setWeatherData] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [location, setLocation] = useState('Pune');
  const [inputValue, setInputValue] = useState('Pune');

  useEffect(() => {
    fetchWeatherData();
  }, [location]); // Re-fetch when location changes

  const fetchWeatherData = async () => {
    try {
      setLoading(true);
      
      // Use the location state (not inputValue) for API calls
      const searchLocation = location || 'Pune';
      
      // Add timestamp to prevent caching
      const timestamp = new Date().getTime();
      
      // Fetch current weather with cache-busting
      const weatherResponse = await axios.get(`${apiUrl}/get_weather?location=${searchLocation}&_t=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      setWeatherData(weatherResponse.data);
      
      // Fetch forecast with cache-busting
      const forecastResponse = await axios.get(`${apiUrl}/get_forecast?location=${searchLocation}&hours=24&_t=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      setForecast(forecastResponse.data);
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching weather:', error);
      alert('Error fetching weather. Please check the location name and try again.');
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (inputValue.trim()) {
      // Validate input - check if it's not a weather condition
      const weatherConditions = ['rain', 'sunny', 'cloudy', 'storm', 'snow', 'fog', 'mist', 'drizzle', 'thunder', 'wind', 'hot', 'cold', 'warm', 'cool'];
      const lowerInput = inputValue.trim().toLowerCase();
      
      if (weatherConditions.includes(lowerInput)) {
        alert('⚠️ Please enter a city name, not a weather condition.\n\nExamples: Mumbai, Delhi, Bangalore, Pune');
        return;
      }
      
      // Check minimum length
      if (inputValue.trim().length < 2) {
        alert('⚠️ Please enter a valid city name (at least 2 characters)');
        return;
      }
      
      setLocation(inputValue.trim());
      // useEffect will trigger fetchWeatherData automatically
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', margin: 0, marginBottom: '0.5rem' }}>🌤️ Weather & Forecast</h2>
          {weatherData?.data_source && (
            <span style={{ 
              fontSize: '0.875rem', 
              color: weatherData.data_source.includes('OpenWeather') ? '#16a34a' : '#f59e0b', 
              fontWeight: '600',
              background: weatherData.data_source.includes('OpenWeather') ? '#f0fdf4' : '#fef3c7',
              padding: '0.25rem 0.75rem',
              borderRadius: '9999px',
              border: weatherData.data_source.includes('OpenWeather') ? '1px solid #bbf7d0' : '1px solid #fde68a'
            }}>
              {weatherData.data_source.includes('OpenWeather') ? '🌐 Real-time OpenWeather API' : '⚠️ Demo Mode (Simulated)'}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '1.2rem' }}>📍</span>
            <input 
              type="text" 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter location (e.g., Mumbai, Delhi)"
              disabled={loading}
              style={{ 
                padding: '0.5rem 1rem 0.5rem 2.5rem', 
                borderRadius: '8px', 
                border: '2px solid #e5e7eb',
                fontSize: '1rem',
                minWidth: '250px',
                opacity: loading ? 0.6 : 1,
                cursor: loading ? 'not-allowed' : 'text'
              }}
            />
          </div>
          <button 
            onClick={handleSearch}
            disabled={loading}
            style={{
              padding: '0.5rem 1.5rem',
              background: loading ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.background = '#2563eb';
                e.target.style.transform = 'translateY(-2px)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.background = '#3b82f6';
                e.target.style.transform = 'translateY(0)';
              }
            }}
          >
            {loading ? '⏳ Loading...' : '🔍 Search'}
          </button>
        </div>
      </div>

      {/* Current Location Display with Coordinates */}
      <div style={{ 
        marginBottom: '1rem', 
        padding: '0.75rem 1rem', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
        borderRadius: '8px',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.2rem' }}>📍</span>
          <span style={{ fontSize: '1rem', fontWeight: '600' }}>
            {weatherData?.location || location}
          </span>
        </div>
        {weatherData?.coordinates && (
          <span style={{ fontSize: '0.875rem', opacity: 0.9 }}>
            {weatherData.coordinates.lat.toFixed(2)}°N, {weatherData.coordinates.lon.toFixed(2)}°E
          </span>
        )}
      </div>

      {/* Current Weather */}
      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🌡️ Current Weather</h3>
          </div>
          <div className="card-content">
            <div className="metric">
              <div className="metric-label">Temperature</div>
              <div className="metric-value">
                {weatherData?.current?.temperature || 0}
                <span className="metric-unit">°C</span>
              </div>
              {weatherData?.current?.feels_like && (
                <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.5rem' }}>
                  Feels like {weatherData.current.feels_like}°C
                </div>
              )}
            </div>
            <div style={{ marginTop: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Humidity:</span>
                <span style={{ fontWeight: '600' }}>{weatherData?.current?.humidity || 0}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Wind Speed:</span>
                <span style={{ fontWeight: '600' }}>{weatherData?.current?.wind_speed || 0} km/h</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Wind Direction:</span>
                <span style={{ fontWeight: '600' }}>{weatherData?.current?.wind_direction || 'N/A'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Cloud Cover:</span>
                <span style={{ fontWeight: '600' }}>{weatherData?.current?.cloud_cover || 0}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Pressure:</span>
                <span style={{ fontWeight: '600' }}>{weatherData?.current?.pressure || 0} hPa</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Visibility:</span>
                <span style={{ fontWeight: '600' }}>{weatherData?.current?.visibility || 0} km</span>
              </div>
              <div style={{ 
                marginTop: '1rem', 
                padding: '0.75rem', 
                background: '#f3f4f6', 
                borderRadius: '6px',
                textAlign: 'center',
                fontWeight: '600'
              }}>
                {weatherData?.current?.conditions || 'N/A'}
                {weatherData?.current?.description && (
                  <div style={{ fontSize: '0.875rem', fontWeight: 'normal', color: '#6b7280', marginTop: '0.25rem' }}>
                    {weatherData.current.description}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📊 Forecast Summary</h3>
          </div>
          <div className="card-content">
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Avg Temperature:</span>
                <span>{forecast?.summary?.avg_temperature || 0}°C</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Max Temperature:</span>
                <span>{forecast?.summary?.max_temperature || 0}°C</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Rain Probability:</span>
                <span>{forecast?.summary?.max_rain_probability || 0}%</span>
              </div>
            </div>
            <div className={`status-badge ${forecast?.summary?.rain_expected ? 'status-critical' : 'status-good'}`}>
              {forecast?.summary?.rain_expected ? '🌧️ Rain Expected' : '☀️ Clear'}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">⚠️ Weather Risk</h3>
          </div>
          <div className="card-content">
            <div className="metric">
              <div className="metric-label">Risk Level</div>
              <div className={`status-badge status-${forecast?.risk_score?.level || 'good'}`}>
                {forecast?.risk_score?.level?.toUpperCase() || 'LOW'}
              </div>
            </div>
            <div style={{ marginTop: '1rem' }}>
              <strong>Risk Factors:</strong>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                {forecast?.risk_score?.factors?.length > 0 ? (
                  forecast.risk_score.factors.map((factor, index) => (
                    <li key={index}>{factor}</li>
                  ))
                ) : (
                  <li>No significant risks</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">💡 Recommendations</h3>
        </div>
        <div className="card-content">
          <ul className="recommendations">
            {forecast?.recommendations?.map((rec, index) => (
              <li key={index} className="recommendation-item">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Hourly Forecast */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">📅 {forecast?.data_source?.includes('OpenWeather') ? 'Real-time' : 'Simulated'} Forecast</h3>
          {forecast?.data_source && (
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
              Data source: {forecast.data_source}
            </div>
          )}
        </div>
        <div className="card-content">
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Time</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Temp (°C)</th>
                  {forecast?.hourly_forecast?.[0]?.feels_like && (
                    <th style={{ padding: '0.75rem', textAlign: 'left' }}>Feels Like</th>
                  )}
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Humidity</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Rain %</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Wind</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Conditions</th>
                </tr>
              </thead>
              <tbody>
                {forecast?.hourly_forecast?.slice(0, 12).map((hour, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '0.75rem', fontWeight: '600' }}>
                      {new Date(hour.time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td style={{ padding: '0.75rem' }}>{hour.temperature}°C</td>
                    {hour.feels_like && (
                      <td style={{ padding: '0.75rem', color: '#6b7280' }}>{hour.feels_like}°C</td>
                    )}
                    <td style={{ padding: '0.75rem' }}>{hour.humidity}%</td>
                    <td style={{ 
                      padding: '0.75rem',
                      color: hour.rain_probability > 60 ? '#dc2626' : hour.rain_probability > 30 ? '#f59e0b' : '#16a34a',
                      fontWeight: '600'
                    }}>
                      {hour.rain_probability}%
                    </td>
                    <td style={{ padding: '0.75rem' }}>{hour.wind_speed} km/h</td>
                    <td style={{ padding: '0.75rem' }}>
                      <div>{hour.conditions}</div>
                      {hour.description && (
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                          {hour.description}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#6b7280', textAlign: 'center' }}>
            {forecast?.data_source?.includes('OpenWeather') ? 
              '🌐 Real-time data from OpenWeather API' : 
              '⚠️ Simulated forecast for demonstration'}
          </div>
        </div>
      </div>
    </div>
  );
}

export default WeatherView;
