import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ActionsLog.css';

function ActionsLog() {
  const [actions, setActions] = useState([]);
  const [totalTokens, setTotalTokens] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const [newAction, setNewAction] = useState({
    action_type: '',
    action_details: '',
    green_tokens: 0
  });

  useEffect(() => {
    fetchActions();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchActions, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchActions = async () => {
    try {
      const timestamp = new Date().getTime();
      const response = await axios.get(
        `${apiUrl}/actions_log?farm_id=FARM001&limit=100&_t=${timestamp}`,
        {
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
          }
        }
      );
      setActions(response.data.actions || []);
      setTotalTokens(response.data.total_green_tokens || 0);
    } catch (error) {
      console.error('Error fetching actions:', error);
    }
  };

  const logAction = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${apiUrl}/actions_log`, {
        farm_id: 'FARM001',
        ...newAction,
        green_tokens: parseInt(newAction.green_tokens) || 0
      });
      
      alert('✅ Action logged successfully!');
      setShowAddForm(false);
      setNewAction({
        action_type: '',
        action_details: '',
        green_tokens: 0
      });
      fetchActions();
    } catch (error) {
      console.error('Error logging action:', error);
      alert('❌ Error logging action. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const deleteAction = async (actionId) => {
    if (window.confirm('Are you sure you want to delete this action?')) {
      try {
        await axios.delete(`${apiUrl}/actions_log/${actionId}`);
        alert('✅ Action deleted successfully!');
        fetchActions();
      } catch (error) {
        console.error('Error deleting action:', error);
        alert('❌ Error deleting action.');
      }
    }
  };

  const getActionIcon = (type) => {
    const icons = {
      irrigation: '🚿',
      fertilization: '🌱',
      pesticide: '🦠',
      harvesting: '🚜',
      planting: '🌾',
      eco_action: '🌍',
      rotation: '🔄',
      composting: '♻️',
      rainwater: '💧',
      solar: '☀️',
      organic: '🍃'
    };
    return icons[type] || '📝';
  };

  const getActionColor = (type) => {
    const colors = {
      irrigation: '#3b82f6',
      fertilization: '#10b981',
      pesticide: '#f59e0b',
      harvesting: '#8b5cf6',
      planting: '#10b981',
      eco_action: '#059669',
      rotation: '#6366f1',
      composting: '#059669',
      rainwater: '#3b82f6',
      solar: '#f59e0b',
      organic: '#10b981'
    };
    return colors[type] || '#6b7280';
  };

  const filteredActions = filterType === 'all' 
    ? actions 
    : actions.filter(action => action.action_type === filterType);

  const getActionsByType = (type) => {
    return actions.filter(action => action.action_type === type).length;
  };

  const getTokensByType = (type) => {
    return actions
      .filter(action => action.action_type === type)
      .reduce((sum, action) => sum + (action.green_tokens_earned || 0), 0);
  };

  const actionTypes = [
    { value: 'irrigation', label: '🚿 Irrigation', tokens: 10 },
    { value: 'fertilization', label: '🌱 Fertilization', tokens: 15 },
    { value: 'eco_action', label: '🌍 Eco Action', tokens: 20 },
    { value: 'rotation', label: '🔄 Crop Rotation', tokens: 20 },
    { value: 'composting', label: '♻️ Composting', tokens: 14 },
    { value: 'rainwater', label: '💧 Rainwater Harvesting', tokens: 30 },
    { value: 'solar', label: '☀️ Solar Power', tokens: 25 },
    { value: 'organic', label: '🍃 Organic Methods', tokens: 18 },
    { value: 'planting', label: '🌾 Planting', tokens: 5 },
    { value: 'harvesting', label: '🚜 Harvesting', tokens: 5 }
  ];

  const uniqueActionTypes = [...new Set(actions.map(a => a.action_type))];

  return (
    <div className="actions-log">
      <div className="actions-header">
        <div className="header-title">
          <h2>📝 Actions Log</h2>
          <p>Track all your farming activities and green token earnings</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-refresh" 
            onClick={fetchActions}
            title="Refresh data"
          >
            🔄 Refresh
          </button>
          <button 
            className="btn-add" 
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? '❌ Cancel' : '➕ Log Action'}
          </button>
        </div>
      </div>

      {/* Total Tokens Card */}
      <div className="tokens-summary">
        <div className="tokens-card">
          <div className="tokens-icon">🌟</div>
          <div className="tokens-info">
            <h3>{totalTokens}</h3>
            <p>Total Green Tokens Earned</p>
          </div>
        </div>
        <div className="tokens-card">
          <div className="tokens-icon">📊</div>
          <div className="tokens-info">
            <h3>{actions.length}</h3>
            <p>Total Actions Logged</p>
          </div>
        </div>
        <div className="tokens-card">
          <div className="tokens-icon">🎯</div>
          <div className="tokens-info">
            <h3>{actions.length > 0 ? (totalTokens / actions.length).toFixed(1) : 0}</h3>
            <p>Avg Tokens per Action</p>
          </div>
        </div>
      </div>

      {/* Add Action Form */}
      {showAddForm && (
        <div className="add-action-form">
          <h3>➕ Log New Action</h3>
          <form onSubmit={logAction}>
            <div className="form-row">
              <div className="form-group">
                <label>Action Type</label>
                <select
                  value={newAction.action_type}
                  onChange={(e) => {
                    const selectedType = actionTypes.find(t => t.value === e.target.value);
                    setNewAction({ 
                      ...newAction, 
                      action_type: e.target.value,
                      green_tokens: selectedType ? selectedType.tokens : 0
                    });
                  }}
                  required
                >
                  <option value="">Select action type</option>
                  {actionTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label} (+{type.tokens} tokens)
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Green Tokens</label>
                <input
                  type="number"
                  min="0"
                  value={newAction.green_tokens}
                  onChange={(e) => setNewAction({ ...newAction, green_tokens: e.target.value })}
                  placeholder="e.g., 20"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Action Details</label>
              <textarea
                value={newAction.action_details}
                onChange={(e) => setNewAction({ ...newAction, action_details: e.target.value })}
                placeholder="Describe what you did... (e.g., Installed drip irrigation system in wheat field)"
                rows="4"
                required
              />
            </div>

            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? '⏳ Logging...' : '✅ Log Action'}
            </button>
          </form>
        </div>
      )}

      {/* Filter Buttons */}
      {uniqueActionTypes.length > 0 && (
        <div className="actions-filters">
          <button
            className={filterType === 'all' ? 'filter-btn active' : 'filter-btn'}
            onClick={() => setFilterType('all')}
          >
            📦 All ({actions.length})
          </button>
          {uniqueActionTypes.map(type => (
            <button
              key={type}
              className={filterType === type ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilterType(type)}
            >
              {getActionIcon(type)} {type.charAt(0).toUpperCase() + type.slice(1)} ({getActionsByType(type)})
            </button>
          ))}
        </div>
      )}

      {/* Actions List */}
      <div className="actions-list">
        {filteredActions.length === 0 ? (
          <div className="empty-state">
            <h3>📝 No Actions Found</h3>
            <p>Click "Log Action" to start tracking your farming activities</p>
          </div>
        ) : (
          filteredActions.map((action) => (
            <div 
              key={action.id} 
              className="action-card"
              style={{ borderLeft: `4px solid ${getActionColor(action.action_type)}` }}
            >
              <div className="action-header">
                <div className="action-title">
                  <span 
                    className="action-icon"
                    style={{ 
                      background: getActionColor(action.action_type) + '20',
                      color: getActionColor(action.action_type)
                    }}
                  >
                    {getActionIcon(action.action_type)}
                  </span>
                  <div>
                    <h3>{action.action_type.charAt(0).toUpperCase() + action.action_type.slice(1).replace('_', ' ')}</h3>
                    <p className="action-time">{new Date(action.timestamp).toLocaleString()}</p>
                  </div>
                </div>
                <div className="action-tokens">
                  <span className="tokens-badge">+{action.green_tokens_earned} 🌟</span>
                </div>
              </div>

              <div className="action-details">
                <p>{action.action_details}</p>
              </div>

              <div className="action-footer">
                <span className="action-id">ID: {action.id}</span>
                <button 
                  className="btn-delete-action"
                  onClick={() => deleteAction(action.id)}
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Statistics Summary */}
      {actions.length > 0 && (
        <div className="actions-summary">
          <h3>📊 Activity Summary</h3>
          <div className="summary-grid">
            {uniqueActionTypes.map(type => (
              <div key={type} className="summary-item">
                <span className="summary-icon">{getActionIcon(type)}</span>
                <div className="summary-info">
                  <p className="summary-type">{type.charAt(0).toUpperCase() + type.slice(1)}</p>
                  <p className="summary-stats">
                    {getActionsByType(type)} actions • {getTokensByType(type)} tokens 🌟
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ActionsLog;
