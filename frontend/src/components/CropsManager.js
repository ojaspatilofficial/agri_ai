import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './CropsManager.css';

function CropsManager() {
  const [crops, setCrops] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const [newCrop, setNewCrop] = useState({
    crop_type: '',
    planted_date: '',
    expected_harvest_date: '',
    area_hectares: '',
    status: 'growing'
  });




  
  useEffect(() => {
    fetchCrops();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchCrops, 30000);
    return () => clearInterval(interval);
  }, [filterStatus]);

  const fetchCrops = async () => {
    try {
      const timestamp = new Date().getTime();
      const statusParam = filterStatus !== 'all' ? `&status=${filterStatus}` : '';
      const response = await axios.get(
        `${apiUrl}/crops?farm_id=FARM001${statusParam}&_t=${timestamp}`,
        {
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
          }
        }
      );
      setCrops(response.data.crops || []);
    } catch (error) {
      console.error('Error fetching crops:', error);
    }
  };

  const addCrop = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${apiUrl}/crops`, {
        farm_id: 'FARM001',
        ...newCrop,
        area_hectares: parseFloat(newCrop.area_hectares)
      });
      
      alert('✅ Crop added successfully!');
      setShowAddForm(false);
      setNewCrop({
        crop_type: '',
        planted_date: '',
        expected_harvest_date: '',
        area_hectares: '',
        status: 'growing'
      });
      fetchCrops();
    } catch (error) {
      console.error('Error adding crop:', error);
      alert('❌ Error adding crop. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const updateCropStatus = async (cropId, newStatus) => {
    try {
      await axios.put(`${apiUrl}/crops/${cropId}/status?status=${newStatus}`);
      alert(`✅ Crop status updated to ${newStatus}!`);
      fetchCrops();
    } catch (error) {
      console.error('Error updating crop:', error);
      alert('❌ Error updating crop status.');
    }
  };

  const deleteCrop = async (cropId) => {
    if (window.confirm('Are you sure you want to delete this crop?')) {
      try {
        await axios.delete(`${apiUrl}/crops/${cropId}`);
        alert('✅ Crop deleted successfully!');
        fetchCrops();
      } catch (error) {
        console.error('Error deleting crop:', error);
        alert('❌ Error deleting crop.');
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'growing': return '#10b981';
      case 'ready': return '#f59e0b';
      case 'harvested': return '#6366f1';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'growing': return '🌱';
      case 'ready': return '✅';
      case 'harvested': return '🚜';
      case 'failed': return '❌';
      default: return '📦';
    }
  };

  const getCropIcon = (cropType) => {
    const icons = {
      wheat: '🌾',
      rice: '🍚',
      corn: '🌽',
      tomatoes: '🍅',
      potatoes: '🥔',
      onions: '🧅',
      carrots: '🥕',
      sugarcane: '🎋',
      cotton: '☁️',
      soybeans: '🫘'
    };
    return icons[cropType.toLowerCase()] || '🌿';
  };

  const calculateTotalArea = () => {
    return crops.reduce((sum, crop) => sum + (crop.area_hectares || 0), 0).toFixed(2);
  };

  const getCropsByStatus = (status) => {
    return crops.filter(crop => crop.status === status).length;
  };

  const cropTypes = [
    'wheat', 'rice', 'corn', 'tomatoes', 'potatoes', 
    'onions', 'carrots', 'sugarcane', 'cotton', 'soybeans'
  ];

  return (
    <div className="crops-manager">
      <div className="crops-header">
        <div className="header-title">
          <h2>🌾 Crops Management</h2>
          <p>Track your crops from planting to harvest</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-refresh" 
            onClick={fetchCrops}
            title="Refresh data"
          >
            🔄 Refresh
          </button>
          <button 
            className="btn-add" 
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? '❌ Cancel' : '➕ Add Crop'}
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="crops-stats">
        <div className="stat-card">
          <div className="stat-icon">🌾</div>
          <div className="stat-info">
            <h3>{crops.length}</h3>
            <p>Total Crops</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🌱</div>
          <div className="stat-info">
            <h3>{getCropsByStatus('growing')}</h3>
            <p>Growing</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-info">
            <h3>{getCropsByStatus('ready')}</h3>
            <p>Ready</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🚜</div>
          <div className="stat-info">
            <h3>{getCropsByStatus('harvested')}</h3>
            <p>Harvested</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📏</div>
          <div className="stat-info">
            <h3>{calculateTotalArea()}</h3>
            <p>Total Hectares</p>
          </div>
        </div>
      </div>

      {/* Add Crop Form */}
      {showAddForm && (
        <div className="add-crop-form">
          <h3>➕ Add New Crop</h3>
          <form onSubmit={addCrop}>
            <div className="form-row">
              <div className="form-group">
                <label>Crop Type</label>
                <select
                  value={newCrop.crop_type}
                  onChange={(e) => setNewCrop({ ...newCrop, crop_type: e.target.value })}
                  required
                >
                  <option value="">Select crop type</option>
                  {cropTypes.map(type => (
                    <option key={type} value={type}>
                      {getCropIcon(type)} {type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Area (Hectares)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  value={newCrop.area_hectares}
                  onChange={(e) => setNewCrop({ ...newCrop, area_hectares: e.target.value })}
                  placeholder="e.g., 5.5"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Planted Date</label>
                <input
                  type="date"
                  value={newCrop.planted_date}
                  onChange={(e) => setNewCrop({ ...newCrop, planted_date: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Expected Harvest Date</label>
                <input
                  type="date"
                  value={newCrop.expected_harvest_date}
                  onChange={(e) => setNewCrop({ ...newCrop, expected_harvest_date: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Initial Status</label>
              <select
                value={newCrop.status}
                onChange={(e) => setNewCrop({ ...newCrop, status: e.target.value })}
              >
                <option value="growing">🌱 Growing</option>
                <option value="ready">✅ Ready</option>
              </select>
            </div>

            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? '⏳ Adding...' : '✅ Add Crop'}
            </button>
          </form>
        </div>
      )}

      {/* Filter Buttons */}
      <div className="crops-filters">
        <button
          className={filterStatus === 'all' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilterStatus('all')}
        >
          📦 All ({crops.length})
        </button>
        <button
          className={filterStatus === 'growing' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilterStatus('growing')}
        >
          🌱 Growing ({getCropsByStatus('growing')})
        </button>
        <button
          className={filterStatus === 'ready' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilterStatus('ready')}
        >
          ✅ Ready ({getCropsByStatus('ready')})
        </button>
        <button
          className={filterStatus === 'harvested' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilterStatus('harvested')}
        >
          🚜 Harvested ({getCropsByStatus('harvested')})
        </button>
      </div>

      {/* Crops List */}
      <div className="crops-list">
        {crops.length === 0 ? (
          <div className="empty-state">
            <h3>🌾 No Crops Found</h3>
            <p>Click "Add Crop" to start tracking your crops</p>
          </div>
        ) : (
          crops.map((crop) => (
            <div key={crop.id} className="crop-card">
              <div className="crop-header">
                <div className="crop-title">
                  <span className="crop-icon">{getCropIcon(crop.crop_type)}</span>
                  <h3>{crop.crop_type.charAt(0).toUpperCase() + crop.crop_type.slice(1)}</h3>
                </div>
                <div 
                  className="crop-status"
                  style={{ 
                    backgroundColor: getStatusColor(crop.status) + '20',
                    color: getStatusColor(crop.status)
                  }}
                >
                  {getStatusIcon(crop.status)} {crop.status.toUpperCase()}
                </div>
              </div>

              <div className="crop-details">
                <div className="detail-item">
                  <span className="detail-label">📏 Area:</span>
                  <span className="detail-value">{crop.area_hectares} hectares</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">🌱 Planted:</span>
                  <span className="detail-value">{new Date(crop.planted_date).toLocaleDateString()}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">📅 Expected Harvest:</span>
                  <span className="detail-value">{new Date(crop.expected_harvest_date).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="crop-actions">
                {crop.status === 'growing' && (
                  <button 
                    className="btn-action btn-ready"
                    onClick={() => updateCropStatus(crop.id, 'ready')}
                  >
                    ✅ Mark Ready
                  </button>
                )}
                {crop.status === 'ready' && (
                  <button 
                    className="btn-action btn-harvest"
                    onClick={() => updateCropStatus(crop.id, 'harvested')}
                  >
                    🚜 Mark Harvested
                  </button>
                )}
                {crop.status === 'harvested' && (
                  <button 
                    className="btn-action btn-delete"
                    onClick={() => deleteCrop(crop.id)}
                  >
                    🗑️ Delete
                  </button>
                )}
                {crop.status === 'growing' && (
                  <button 
                    className="btn-action btn-delete"
                    onClick={() => deleteCrop(crop.id)}
                  >
                    🗑️ Delete
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default CropsManager;
