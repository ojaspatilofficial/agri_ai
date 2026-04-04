import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ProfileView({ farmer, apiUrl }) {
  const [farmerProfile, setFarmerProfile] = useState(null);
  const [weather, setWeather] = useState(null);
  const [market, setMarket] = useState(null);
  const [satellite, setSatellite] = useState(null);
  const [cropsData, setCropsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});

  const farmId = farmer?.farmerId || farmer?.farmer_id || 'FARM001';

  useEffect(() => {
    fetchAllData();
  }, [farmId]);

  const fetchAllData = async () => {
    setLoading(true);
    const newErrors = {};

    const results = await Promise.allSettled([
      axios.get(`${apiUrl}/profile?farm_id=${farmId}`),
      axios.get(`${apiUrl}/get_weather?location=Pune`),
      axios.get(`${apiUrl}/get_market_forecast?crop=wheat`),
      axios.get(`${apiUrl}/drone_satellite_analysis?farm_id=${farmId}`),
      axios.get(`${apiUrl}/crops?farm_id=${farmId}`)
    ]);

    if (results[0].status === 'fulfilled') setFarmerProfile(results[0].value.data);
    else newErrors.profile = true;

    if (results[1].status === 'fulfilled') setWeather(results[1].value.data);
    else newErrors.weather = true;

    if (results[2].status === 'fulfilled') setMarket(results[2].value.data);
    else newErrors.market = true;

    if (results[3].status === 'fulfilled') setSatellite(results[3].value.data);
    else newErrors.satellite = true;

    if (results[4].status === 'fulfilled') setCropsData(results[4].value.data.crops || []);
    else newErrors.crops = true;

    setErrors(newErrors);
    setLoading(false);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px', gap: '1rem' }}>
        <div className="spinner"></div>
        <p style={{ color: '#6b7280', fontSize: '0.95rem' }}>Loading your farm profile…</p>
      </div>
    );
  }

  const activeCropsCount = cropsData.filter(c => c.status === 'growing').length;
  const totalCropHa = cropsData.reduce((sum, c) => sum + (c.area_hectares || 0), 0);
  const lat = farmerProfile?.latitude || 18.5204;
  const lon = farmerProfile?.longitude || 73.8567;
  const farmSize = farmerProfile?.farm_size || 12.5;
  const farmSizeAcres = (farmSize * 2.471).toFixed(1);

  // OpenStreetMap embed URL
  const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${lon - 0.02}%2C${lat - 0.015}%2C${lon + 0.02}%2C${lat + 0.015}&layer=mapnik&marker=${lat}%2C${lon}`;
  const mapLink = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=14/${lat}/${lon}`;

  return (
    <div style={{ animation: 'fadeIn 0.4s ease-out' }}>

      {/* ── Hero Banner ── */}
      <div style={{
        background: 'linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%)',
        color: 'white',
        padding: '2rem 2.5rem',
        borderRadius: '1.5rem',
        marginBottom: '2rem',
        display: 'flex',
        alignItems: 'center',
        gap: '2rem',
        flexWrap: 'wrap',
        boxShadow: '0 10px 30px -5px rgba(16, 185, 129, 0.45)'
      }}>
        <div style={{
          width: '90px', height: '90px',
          background: 'rgba(255,255,255,0.2)',
          borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '2.75rem',
          border: '3px solid rgba(255,255,255,0.5)',
          flexShrink: 0
        }}>👤</div>

        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: '1.9rem', margin: '0 0 0.25rem 0', fontWeight: '800' }}>
            {farmerProfile?.name || farmer?.name || 'Farmer'}
          </h2>
          <p style={{ opacity: 0.85, margin: '0 0 0.75rem 0', fontSize: '0.95rem' }}>
            ✉️ {farmerProfile?.email || farmer?.email} &nbsp;|&nbsp; 🆔 {farmId}
            {farmerProfile?.phone && <> &nbsp;|&nbsp; 📞 {farmerProfile.phone}</>}
          </p>
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            {[
              { icon: '📍', text: farmerProfile?.location || 'Pune, Maharashtra' },
              { icon: '📐', text: `${farmSize} ha  (${farmSizeAcres} acres)` },
              { icon: '🌐', text: `${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E` },
            ].map((badge, i) => (
              <span key={i} style={{
                background: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(4px)',
                padding: '0.35rem 0.9rem',
                borderRadius: '2rem',
                fontSize: '0.82rem',
                fontWeight: '600',
                border: '1px solid rgba(255,255,255,0.3)'
              }}>
                {badge.icon} {badge.text}
              </span>
            ))}
          </div>
        </div>

        <button onClick={fetchAllData} style={{
          background: 'rgba(255,255,255,0.2)',
          border: '1px solid rgba(255,255,255,0.4)',
          color: 'white',
          padding: '0.5rem 1rem',
          borderRadius: '0.75rem',
          cursor: 'pointer',
          fontWeight: '600',
          fontSize: '0.85rem',
          flexShrink: 0
        }}>
          🔄 Refresh
        </button>
      </div>

      {/* ── Farm Location Map ── */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="card-title">🗺️ Farm Location & Size</h3>
          <a href={mapLink} target="_blank" rel="noreferrer" style={{
            fontSize: '0.82rem', color: '#059669', fontWeight: '600', textDecoration: 'none',
            padding: '0.3rem 0.75rem', background: '#f0fdf4', borderRadius: '0.5rem',
            border: '1px solid #bbf7d0'
          }}>
            Open Full Map ↗
          </a>
        </div>
        <div className="card-content" style={{ padding: 0 }}>
          {/* Stats row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 0, borderBottom: '1px solid #f3f4f6' }}>
            {[
              { label: 'Latitude', value: `${lat.toFixed(4)}°N`, icon: '🌐' },
              { label: 'Longitude', value: `${lon.toFixed(4)}°E`, icon: '🌐' },
              { label: 'Farm Size', value: `${farmSize} ha`, icon: '📐' },
              { label: 'Equivalent', value: `${farmSizeAcres} acres`, icon: '🌾' },
            ].map((item, i) => (
              <div key={i} style={{
                padding: '1rem 1.25rem',
                borderRight: i < 3 ? '1px solid #f3f4f6' : 'none',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '1.1rem' }}>{item.icon}</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#111827', marginTop: '0.25rem' }}>{item.value}</div>
                <div style={{ fontSize: '0.72rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{item.label}</div>
              </div>
            ))}
          </div>

          {/* Interactive Map */}
          <div style={{ position: 'relative', height: '300px', borderRadius: '0 0 1rem 1rem', overflow: 'hidden' }}>
            <iframe
              title="Farm Location Map"
              src={mapUrl}
              style={{ width: '100%', height: '100%', border: 'none' }}
              loading="lazy"
            />
            {/* Farm size overlay pin */}
            <div style={{
              position: 'absolute', top: '12px', left: '12px',
              background: 'white', padding: '0.5rem 0.75rem',
              borderRadius: '0.75rem', boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              fontSize: '0.8rem', fontWeight: '700', color: '#065f46',
              border: '2px solid #10b981'
            }}>
              📍 {farmerProfile?.name || 'Your Farm'} — {farmSize}ha
            </div>
          </div>
        </div>
      </div>

      {/* ── 3-Column Data Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>

        {/* Crop Assets */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🚜 Crop Assets</h3>
            <span style={{ fontSize: '0.75rem', color: '#10b981', background: '#f0fdf4', padding: '0.2rem 0.5rem', borderRadius: '1rem', fontWeight: '600' }}>
              LIVE
            </span>
          </div>
          <div className="card-content">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
              <StatBox value={activeCropsCount} label="Active Crops" color="#059669" bg="#f0fdf4" />
              <StatBox value={`${totalCropHa.toFixed(1)} ha`} label="Planted Area" color="#059669" bg="#f0fdf4" />
            </div>
            {cropsData.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem', padding: '1rem 0' }}>
                No crops added yet. Use the Crops tab to add your first crop.
              </p>
            ) : (
              cropsData.slice(0, 4).map((crop, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '0.6rem 0',
                  borderBottom: i < Math.min(cropsData.length, 4) - 1 ? '1px solid #f3f4f6' : 'none'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span style={{ fontSize: '1.2rem' }}>{getCropIcon(crop.crop_type)}</span>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{crop.crop_type}</div>
                      <div style={{ fontSize: '0.72rem', color: '#9ca3af' }}>{crop.area_hectares} ha</div>
                    </div>
                  </div>
                  <StatusBadge status={crop.status} />
                </div>
              ))
            )}
            {cropsData.length > 4 && (
              <p style={{ textAlign: 'center', fontSize: '0.8rem', color: '#6b7280', marginTop: '0.5rem' }}>
                +{cropsData.length - 4} more crops
              </p>
            )}
          </div>
        </div>

        {/* Weather */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🌤️ Live Weather</h3>
            <span style={{ fontSize: '0.72rem', color: '#3b82f6', background: '#eff6ff', padding: '0.2rem 0.5rem', borderRadius: '1rem', fontWeight: '600' }}>
              OpenWeather
            </span>
          </div>
          <div className="card-content">
            {weather ? (
              <>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                  <div>
                    <div style={{ fontSize: '3rem', fontWeight: '800', color: '#1d4ed8', lineHeight: 1 }}>
                      {weather.current?.temperature ?? '—'}°C
                    </div>
                    <div style={{ fontSize: '0.9rem', color: '#6b7280', marginTop: '0.25rem' }}>
                      Feels like {weather.current?.feels_like ?? '—'}°C
                    </div>
                  </div>
                  <div style={{ fontSize: '3.5rem' }}>{getWeatherIcon(weather.current?.conditions)}</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
                  <InfoChip icon="💧" label="Humidity" value={`${weather.current?.humidity ?? '—'}%`} />
                  <InfoChip icon="📍" label="Location" value={weather.location || 'Pune'} />
                  <InfoChip icon="☁️" label="Conditions" value={weather.current?.conditions ?? '—'} />
                  <InfoChip icon="📊" label="Source" value="OpenWeather" />
                </div>
              </>
            ) : (
              <ErrorMessage msg="Weather data unavailable" />
            )}
          </div>
        </div>

        {/* Market */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📈 Market Prices</h3>
            <span style={{ fontSize: '0.72rem', color: '#d97706', background: '#fffbeb', padding: '0.2rem 0.5rem', borderRadius: '1rem', fontWeight: '600' }}>
              data.gov.in
            </span>
          </div>
          <div className="card-content">
            {market ? (
              <>
                <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.82rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {market.crop || 'Wheat'} · Today's Avg Price
                  </div>
                  <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#059669', margin: '0.25rem 0' }}>
                    ₹{market.current_price ? Math.round(market.current_price).toLocaleString() : '—'}
                    <span style={{ fontSize: '0.9rem', fontWeight: '400', color: '#6b7280' }}>/qtl</span>
                  </div>
                  <div style={{
                    display: 'inline-block', padding: '0.3rem 0.85rem',
                    background: '#dcfce7', color: '#15803d',
                    borderRadius: '2rem', fontWeight: '700', fontSize: '0.8rem'
                  }}>
                    📊 {market.mandis_count || 10} Mandis Surveyed
                  </div>
                </div>
                {market.sample_mandis?.slice(0, 3).map((m, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between',
                    padding: '0.45rem 0',
                    borderTop: '1px solid #f3f4f6',
                    fontSize: '0.82rem'
                  }}>
                    <span style={{ color: '#374151' }}>{m.mandi}</span>
                    <span style={{ fontWeight: '700', color: '#059669' }}>₹{Math.round(m.price).toLocaleString()}</span>
                  </div>
                ))}
              </>
            ) : (
              <ErrorMessage msg="Market data unavailable" />
            )}
          </div>
        </div>
      </div>

      {/* ── Satellite + Contact ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>

        {/* Satellite */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🛰️ Satellite & Field Health</h3>
            <span style={{ fontSize: '0.72rem', color: '#7c3aed', background: '#f5f3ff', padding: '0.2rem 0.5rem', borderRadius: '1rem', fontWeight: '600' }}>
              NASA POWER
            </span>
          </div>
          <div className="card-content">
            {satellite ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                <StatBox value={satellite.drone_analysis?.ndvi_average ?? '—'} label="NDVI Index" color="#7c3aed" bg="#f5f3ff" />
                <StatBox value={satellite.drone_analysis?.crop_health ?? '—'} label="Crop Health" color="#7c3aed" bg="#f5f3ff" />
                <StatBox
                  value={`${satellite.satellite_analysis?.temperature_trend?.current ?? '—'}°C`}
                  label="Sat. Temp"
                  color="#7c3aed" bg="#f5f3ff"
                />
                <StatBox
                  value={`${satellite.satellite_analysis?.precipitation?.last_7_days_mm ?? '—'}mm`}
                  label="7-Day Rain"
                  color="#7c3aed" bg="#f5f3ff"
                />
              </div>
            ) : (
              <ErrorMessage msg="Satellite data unavailable" />
            )}

            {satellite?.recommendations?.length > 0 && (
              <div style={{ marginTop: '1.25rem', borderTop: '1px solid #f3f4f6', paddingTop: '1rem' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#6d28d9', marginBottom: '0.5rem' }}>
                  🤖 AI Field Recommendations
                </div>
                {satellite.recommendations.slice(0, 3).map((r, i) => (
                  <div key={i} style={{
                    fontSize: '0.82rem', color: '#374151',
                    padding: '0.4rem 0.6rem',
                    background: '#faf5ff',
                    borderLeft: '3px solid #8b5cf6',
                    borderRadius: '0 0.4rem 0.4rem 0',
                    marginBottom: '0.4rem'
                  }}>{r}</div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Contact Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📋 Account Details</h3>
          </div>
          <div className="card-content">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {[
                { icon: '👤', label: 'Name', value: farmerProfile?.name || '—' },
                { icon: '📧', label: 'Email', value: farmerProfile?.email || '—' },
                { icon: '📞', label: 'Phone', value: farmerProfile?.phone || '—' },
                { icon: '🌍', label: 'Language', value: farmerProfile?.language?.toUpperCase() || 'EN' },
                { icon: '📐', label: 'Farm Size', value: `${farmSize} ha · ${farmSizeAcres} acres` },
                { icon: '🌐', label: 'GPS', value: `${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E` },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{item.icon}</span>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{item.label}</div>
                    <div style={{ fontWeight: '600', fontSize: '0.88rem', color: '#111827' }}>{item.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}

// ── Sub-components ──────────────────────────────────────

function StatBox({ value, label, color, bg }) {
  return (
    <div style={{ textAlign: 'center', padding: '0.85rem 0.5rem', background: bg, borderRadius: '0.75rem' }}>
      <div style={{ fontSize: '1.3rem', fontWeight: '800', color }}>{value}</div>
      <div style={{ fontSize: '0.7rem', color, opacity: 0.75, textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.15rem' }}>{label}</div>
    </div>
  );
}

function InfoChip({ icon, label, value }) {
  return (
    <div style={{ background: '#f9fafb', borderRadius: '0.6rem', padding: '0.5rem 0.6rem' }}>
      <div style={{ fontSize: '0.68rem', color: '#9ca3af', textTransform: 'uppercase' }}>{icon} {label}</div>
      <div style={{ fontWeight: '600', fontSize: '0.82rem', color: '#374151', marginTop: '0.1rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</div>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    growing: { bg: '#dcfce7', color: '#166534', label: 'Growing' },
    ready:   { bg: '#fef9c3', color: '#854d0e', label: 'Ready' },
    harvested: { bg: '#f3f4f6', color: '#374151', label: 'Harvested' },
  };
  const s = map[status] || { bg: '#f3f4f6', color: '#6b7280', label: status };
  return (
    <span style={{ background: s.bg, color: s.color, fontSize: '0.72rem', fontWeight: '700', padding: '0.2rem 0.55rem', borderRadius: '1rem', textTransform: 'capitalize' }}>
      {s.label}
    </span>
  );
}

function ErrorMessage({ msg }) {
  return (
    <div style={{ textAlign: 'center', padding: '1.5rem 0', color: '#9ca3af', fontSize: '0.85rem' }}>
      ⚠️ {msg}
    </div>
  );
}

function getCropIcon(cropType) {
  const icons = { wheat: '🌾', rice: '🍚', corn: '🌽', maize: '🌽', tomato: '🍅', tomatoes: '🍅', potato: '🥔', potatoes: '🥔', onion: '🧅', onions: '🧅', carrot: '🥕', sugarcane: '🎋', cotton: '☁️', soybean: '🫘', soybeans: '🫘', mango: '🥭', banana: '🍌', chilli: '🌶️', sorghum: '🌿', bajra: '🌿' };
  return icons[cropType?.toLowerCase()] || '🌿';
}

function getWeatherIcon(condition) {
  if (!condition) return '🌤️';
  const c = condition.toLowerCase();
  if (c.includes('rain') || c.includes('drizzle')) return '🌧️';
  if (c.includes('thunder')) return '⛈️';
  if (c.includes('cloud')) return '☁️';
  if (c.includes('fog') || c.includes('mist') || c.includes('haze')) return '🌫️';
  if (c.includes('snow')) return '❄️';
  if (c.includes('clear') || c.includes('sunny')) return '☀️';
  return '🌤️';
}

export default ProfileView;
