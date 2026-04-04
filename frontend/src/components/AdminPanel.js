import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AdminPanel.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const LEVEL_CONFIG = {
  L0_SUBMITTED:        { label: 'Submitted',       color: '#6b7280' },
  L1_IMAGE_UPLOADED:   { label: 'Image Uploaded',  color: '#f59e0b' },
  L2_GEO_VERIFIED:     { label: 'Geo Verified',    color: '#10b981' },
  L3_ADMIN_REVIEW:     { label: 'Admin Review',    color: '#3b82f6' },
  L4_VIDEO_PENDING:    { label: 'Call Scheduled',  color: '#8b5cf6' },
  L4_VIDEO_VERIFIED:   { label: 'Call Done',       color: '#059669' },
  L5_APPROVED:         { label: 'Approved ✓',      color: '#16a34a' },
  L5_REJECTED:         { label: 'Rejected',         color: '#dc2626' },
  verification_failed: { label: 'Geo Failed',       color: '#ef4444' },
};

const STATUS_FILTERS = ['all', 'pending', 'geo_failed', 'video_pending', 'approved', 'rejected'];

function StatusBadge({ level, status }) {
  const cfg = LEVEL_CONFIG[level] || { label: level || status, color: '#6b7280' };
  return (
    <span className="admin-status-badge" style={{ background: cfg.color + '18', color: cfg.color, borderColor: cfg.color + '60' }}>
      {cfg.label}
    </span>
  );
}

// ── Admin Login ──────────────────────────────────────────────────────────────
function AdminLogin({ onLogin }) {
  const [creds, setCreds] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API_BASE}/admin/login`, creds);
      if (res.data.status === 'success') {
        localStorage.setItem('admin_token', res.data.admin_token);
        localStorage.setItem('admin_user', JSON.stringify({ username: res.data.username, role: res.data.role }));
        onLogin(res.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-wrap">
      <div className="admin-login-card">
        <div className="admin-login-header">
          <span className="admin-logo">🛡️</span>
          <h2>Admin Dashboard</h2>
          <p>Smart Farming Verification Portal</p>
        </div>
        <form onSubmit={handleLogin} className="admin-login-form">
          <div className="admin-form-group">
            <label>Username</label>
            <input type="text" value={creds.username} onChange={e => setCreds({ ...creds, username: e.target.value })} placeholder="admin" required />
          </div>
          <div className="admin-form-group">
            <label>Password</label>
            <input type="password" value={creds.password} onChange={e => setCreds({ ...creds, password: e.target.value })} placeholder="••••••" required />
          </div>
          {error && <div className="admin-error">❌ {error}</div>}
          <button type="submit" className="admin-login-btn" disabled={loading}>
            {loading ? '⏳ Logging in...' : '🔐 Login'}
          </button>
        </form>
        <div className="admin-register-hint">
          <small>First time? Register via: <code>POST /admin/register</code> with your <code>ADMIN_SUPER_SECRET</code></small>
        </div>
      </div>
    </div>
  );
}

// ── Schedule Call Modal ───────────────────────────────────────────────────────
function ScheduleModal({ action, token, onClose, onDone }) {
  const [phone, setPhone] = useState(action.verification_phone || '');
  const [scheduledAt, setScheduledAt] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async e => {
    e.preventDefault();
    if (!phone || phone.trim().length < 7) { setError('Enter a valid phone number'); return; }
    if (!scheduledAt) { setError('Select a date and time'); return; }
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/admin/schedule_call/${action.id}`, {
        phone: phone.trim(),
        scheduled_at: new Date(scheduledAt).toISOString(),
        notes,
      }, { headers: { 'X-Admin-Token': token } });
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || 'Schedule failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>📹 Schedule WhatsApp Verification Call</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <p className="modal-sub">Farm: <strong>{action.farm_id}</strong> | Action #{action.id} — {action.action_type}</p>
          <div className="admin-form-group">
            <label>WhatsApp Phone Number *</label>
            <input type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+919876543210" required />
          </div>
          <div className="admin-form-group">
            <label>Call Date & Time *</label>
            <input type="datetime-local" value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} required />
          </div>
          <div className="admin-form-group">
            <label>Notes (optional)</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows="2" placeholder="e.g. Verify composting on north field" />
          </div>
          {error && <div className="admin-error">❌ {error}</div>}
          <div className="modal-actions">
            <button type="button" className="admin-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="admin-btn-primary" disabled={loading}>
              {loading ? '⏳ Scheduling...' : '📅 Schedule Call'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Farm Profile Modal ────────────────────────────────────────────────────────
function FarmProfileModal({ farmId, token, onClose, onDone }) {
  const [form, setForm] = useState({ farm_name: '', latitude: '', longitude: '', area_hectares: '', verification_radius_meters: 600 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`${API_BASE}/admin/farm_profile/${farmId}`, { headers: { 'X-Admin-Token': token } })
      .then(r => setForm({ ...r.data, latitude: r.data.latitude ?? '', longitude: r.data.longitude ?? '' }))
      .catch(() => {});
  }, [farmId, token]);

  const handleSave = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const payload = {};
    if (form.farm_name) payload.farm_name = form.farm_name;
    if (form.latitude !== '') payload.latitude = parseFloat(form.latitude);
    if (form.longitude !== '') payload.longitude = parseFloat(form.longitude);
    if (form.area_hectares !== '') payload.area_hectares = parseFloat(form.area_hectares);
    payload.verification_radius_meters = parseFloat(form.verification_radius_meters) || 600;
    try {
      await axios.put(`${API_BASE}/admin/farm_profile/${farmId}`, payload, { headers: { 'X-Admin-Token': token } });
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || 'Save failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>🗺️ Edit Farm Profile — {farmId}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSave} className="modal-body">
          <div className="admin-form-group"><label>Farm Name</label><input value={form.farm_name || ''} onChange={e => setForm({ ...form, farm_name: e.target.value })} placeholder="Optional" /></div>
          <div className="form-row-2">
            <div className="admin-form-group"><label>Latitude</label><input type="number" step="any" value={form.latitude} onChange={e => setForm({ ...form, latitude: e.target.value })} placeholder="e.g. 18.5204" /></div>
            <div className="admin-form-group"><label>Longitude</label><input type="number" step="any" value={form.longitude} onChange={e => setForm({ ...form, longitude: e.target.value })} placeholder="e.g. 73.8567" /></div>
          </div>
          <div className="form-row-2">
            <div className="admin-form-group"><label>Area (hectares)</label><input type="number" step="any" value={form.area_hectares} onChange={e => setForm({ ...form, area_hectares: e.target.value })} placeholder="e.g. 5.0" /></div>
            <div className="admin-form-group"><label>Radius (metres)</label><input type="number" value={form.verification_radius_meters} onChange={e => setForm({ ...form, verification_radius_meters: e.target.value })} min="10" /></div>
          </div>
          {error && <div className="admin-error">❌ {error}</div>}
          <div className="modal-actions">
            <button type="button" className="admin-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="admin-btn-primary" disabled={loading}>{loading ? '⏳ Saving...' : '💾 Save Profile'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Admin Panel ──────────────────────────────────────────────────────────
function AdminPanel({ onLogout }) {
  const token = localStorage.getItem('admin_token');
  const adminUser = JSON.parse(localStorage.getItem('admin_user') || '{}');

  const [activeTab, setActiveTab] = useState('queue');
  const [queueFilter, setQueueFilter] = useState('all');
  const [queue, setQueue] = useState([]);
  const [farmers, setFarmers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState('');
  const [scheduleAction, setScheduleAction] = useState(null);
  const [farmProfileId, setFarmProfileId] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [reviewNotes, setReviewNotes] = useState({});

  const headers = { 'X-Admin-Token': token };

  const showToast = msg => { setToast(msg); setTimeout(() => setToast(''), 3500); };

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/admin/queue?status=${queueFilter}&limit=200`, { headers });
      setQueue(res.data.actions || []);
    } catch (e) { showToast('❌ Failed to load queue'); }
    finally { setLoading(false); }
  };

  const fetchFarmers = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/farmers`, { headers });
      setFarmers(res.data.farmers || []);
    } catch (e) { showToast('❌ Failed to load farmers'); }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/stats`, { headers });
      setStats(res.data);
    } catch (e) {}
  };

  useEffect(() => { fetchQueue(); fetchStats(); }, [queueFilter]);
  useEffect(() => { if (activeTab === 'farmers') fetchFarmers(); }, [activeTab]);

  const approve = async (id) => {
    const notes = reviewNotes[id] || '';
    try {
      await axios.post(`${API_BASE}/admin/approve/${id}`, { reviewer: adminUser.username, notes }, { headers });
      showToast('✅ Approved & tokens minted');
      fetchQueue(); fetchStats();
    } catch (e) { showToast('❌ ' + (e.response?.data?.detail || 'Approve failed')); }
  };

  const reject = async (id) => {
    const notes = reviewNotes[id] || '';
    if (!window.confirm('Reject this token request?')) return;
    try {
      await axios.post(`${API_BASE}/admin/reject/${id}`, { reviewer: adminUser.username, notes }, { headers });
      showToast('🚫 Rejected');
      fetchQueue(); fetchStats();
    } catch (e) { showToast('❌ ' + (e.response?.data?.detail || 'Reject failed')); }
  };

  const markCall = async (id, callStatus) => {
    const notes = reviewNotes[id] || '';
    try {
      await axios.post(`${API_BASE}/admin/complete_call/${id}`, { call_status: callStatus, notes }, { headers });
      showToast(callStatus === 'completed' ? '✅ Call marked completed' : '⚠️ Call marked failed');
      fetchQueue(); fetchStats();
    } catch (e) { showToast('❌ ' + (e.response?.data?.detail || 'Update failed')); }
  };

  return (
    <div className="admin-panel">
      {/* Toast */}
      {toast && <div className="admin-toast">{toast}</div>}

      {/* Modals */}
      {scheduleAction && (
        <ScheduleModal action={scheduleAction} token={token}
          onClose={() => setScheduleAction(null)}
          onDone={() => { setScheduleAction(null); fetchQueue(); showToast('📅 Call scheduled'); }} />
      )}
      {farmProfileId && (
        <FarmProfileModal farmId={farmProfileId} token={token}
          onClose={() => setFarmProfileId(null)}
          onDone={() => { setFarmProfileId(null); fetchFarmers(); showToast('✅ Farm profile updated'); }} />
      )}

      {/* Header */}
      <div className="admin-header">
        <div>
          <h1>🛡️ Admin Dashboard</h1>
          <p>Verification & Token Management — Logged in as <strong>{adminUser.username}</strong> ({adminUser.role})</p>
        </div>
        <button className="admin-logout-btn" onClick={onLogout}>🚪 Logout</button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="admin-stats-row">
          {[
            { label: 'Total Farmers',   value: stats.total_farmers,       icon: '👨‍🌾' },
            { label: 'Total Actions',   value: stats.total_actions,       icon: '📋' },
            { label: 'Pending Review',  value: stats.pending,             icon: '⏳' },
            { label: 'Approved',        value: stats.approved,            icon: '✅' },
            { label: 'Rejected',        value: stats.rejected,            icon: '❌' },
            { label: 'Geo Failed',      value: stats.geo_failed,          icon: '📍' },
            { label: 'Tokens Minted',   value: stats.total_tokens_minted, icon: '🌟' },
          ].map(s => (
            <div className="admin-stat-card" key={s.label}>
              <span className="stat-icon">{s.icon}</span>
              <div><p className="stat-value">{s.value ?? 0}</p><p className="stat-label">{s.label}</p></div>
            </div>
          ))}
        </div>
      )}

      {/* Tab Nav */}
      <div className="admin-tabs">
        <button className={activeTab === 'queue' ? 'admin-tab active' : 'admin-tab'} onClick={() => setActiveTab('queue')}>🔍 Verification Queue</button>
        <button className={activeTab === 'farmers' ? 'admin-tab active' : 'admin-tab'} onClick={() => setActiveTab('farmers')}>👨‍🌾 Farmers</button>
      </div>

      {/* Queue Tab */}
      {activeTab === 'queue' && (
        <div className="admin-tab-content">
          <div className="queue-filters">
            {STATUS_FILTERS.map(f => (
              <button key={f} className={queueFilter === f ? 'filter-btn active' : 'filter-btn'} onClick={() => setQueueFilter(f)}>
                {f === 'all' ? '📦 All' : f === 'pending' ? '⏳ Pending' : f === 'geo_failed' ? '📍 Geo Failed' :
                 f === 'video_pending' ? '📹 Video Pending' : f === 'approved' ? '✅ Approved' : '❌ Rejected'}
                {' '}({queue.filter(a => {
                  if (f === 'all') return true;
                  if (f === 'pending') return ['pending','awaiting_admin_review','awaiting_video_verification'].includes(a.token_request_status);
                  if (f === 'geo_failed') return a.verification_status === 'geo_failed';
                  if (f === 'video_pending') return a.video_verification_status === 'scheduled';
                  return a.token_request_status === f;
                }).length})
              </button>
            ))}
            <button className="admin-btn-refresh" onClick={fetchQueue}>🔄</button>
          </div>

          {loading ? (
            <div className="admin-loading">⏳ Loading queue...</div>
          ) : queue.length === 0 ? (
            <div className="admin-empty">📭 No records match this filter</div>
          ) : (
            <div className="queue-list">
              {queue.map(action => (
                <div key={action.id} className="queue-card">
                  <div className="queue-card-top" onClick={() => setExpandedId(expandedId === action.id ? null : action.id)}>
                    <div className="queue-meta">
                      <span className="queue-farm-id">{action.farm_id}</span>
                      <span className="queue-action-type">{(action.action_type || 'unspecified').replace('_', ' ')}</span>
                      <StatusBadge level={action.verification_level} status={action.token_request_status} />
                    </div>
                    <div className="queue-right">
                      <span className="queue-tokens">+{action.requested_green_tokens} 🌟</span>
                      <span className="queue-date">{new Date(action.timestamp).toLocaleDateString()}</span>
                      <span className="queue-expand">{expandedId === action.id ? '▲' : '▼'}</span>
                    </div>
                  </div>

                  {expandedId === action.id && (
                    <div className="queue-detail">
                      <div className="detail-grid">
                        <div className="detail-col">
                          <p><strong>Details:</strong> {action.action_details || '—'}</p>
                          <p><strong>Reason:</strong> {action.verification_reason || '—'}</p>
                          <p><strong>Admin Reviewer:</strong> {action.admin_reviewer || '—'}</p>
                          <p><strong>Reviewer Notes:</strong> {action.admin_review_notes || '—'}</p>
                        </div>
                        <div className="detail-col">
                          <p><strong>Photo GPS:</strong> {action.proof_latitude ? `${action.proof_latitude.toFixed(5)}, ${action.proof_longitude.toFixed(5)}` : 'None'}</p>
                          <p><strong>Farm GPS:</strong> {action.farm_latitude ? `${action.farm_latitude.toFixed(5)}, ${action.farm_longitude.toFixed(5)}` : 'Not configured'}</p>
                          <p><strong>Distance:</strong> {action.distance_meters != null ? `${action.distance_meters.toFixed(0)}m` : '—'} / Radius: {action.allowed_radius_meters != null ? `${action.allowed_radius_meters.toFixed(0)}m` : '—'}</p>
                          <p><strong>Geo Match:</strong> {action.geo_match_passed ? '✅ Yes' : '❌ No'}</p>
                        </div>
                      </div>

                      {/* Image metadata */}
                      {action.image_metadata && (
                        <div className="detail-exif">
                          <strong>📷 EXIF:</strong>
                          {' '}GPS: {action.image_metadata.has_gps ? '✅' : '❌'}
                          {' '}| Taken: {action.image_metadata.exif_datetime || 'N/A'}
                          {' '}| Device: {action.image_metadata.exif_device || 'N/A'}
                        </div>
                      )}

                      {/* Video call info */}
                      {action.video_call_scheduled_at && (
                        <div className="detail-call">
                          📹 Call scheduled: {new Date(action.video_call_scheduled_at).toLocaleString()}
                          {action.verification_phone && ` | 📱 ${action.verification_phone}`}
                        </div>
                      )}

                      {/* Admin notes textarea */}
                      <div className="detail-notes">
                        <label>Admin Notes:</label>
                        <textarea
                          value={reviewNotes[action.id] || ''}
                          onChange={e => setReviewNotes(prev => ({ ...prev, [action.id]: e.target.value }))}
                          placeholder="Add notes before approving/rejecting..."
                          rows="2"
                        />
                      </div>

                      {/* Action Buttons */}
                      <div className="queue-actions">
                        {['pending','awaiting_admin_review','awaiting_video_verification'].includes(action.token_request_status) && (
                          <>
                            <button className="qbtn qbtn-approve" onClick={() => approve(action.id)}>✅ Approve & Mint</button>
                            <button className="qbtn qbtn-reject" onClick={() => reject(action.id)}>❌ Reject</button>
                            
                            {action.verification_level !== 'L4_VIDEO_PENDING' && (
                              <button className="qbtn qbtn-schedule" onClick={() => setScheduleAction(action)}>📅 Schedule Call</button>
                            )}

                            {/* Direct Connect Options */}
                            {action.verification_phone && (
                              <>
                                <a href={`tel:${action.verification_phone}`} className="qbtn qbtn-call" title="Call directly">
                                  📞 Direct Voice Call
                                </a>
                                <a 
                                  href={`https://wa.me/${(action.verification_phone || '').replace('+', '')}?text=Hi! This is Agri-AI Admin regarding your ${action.action_type || 'action'} action. Can we do a quick video verification?`} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="qbtn qbtn-whatsapp"
                                >
                                  💬 WhatsApp Link
                                </a>
                              </>
                            )}
                          </>
                        )}
                        {action.video_verification_status === 'scheduled' && (
                          <>
                            {action.verification_phone && (() => {
                              const cleanPhone = action.verification_phone.replace(/\D/g, ''); // Remove all non-digits
                              return (
                                <>
                                  <a href={`tel:${action.verification_phone}`} className="qbtn qbtn-call">
                                    📞 Normal Voice Call
                                  </a>
                                  <a 
                                    href={`https://wa.me/${cleanPhone}`} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="qbtn qbtn-whatsapp"
                                  >
                                    📹 WhatsApp Video Call Link
                                  </a>
                                </>
                              );
                            })()}

                            <button className="qbtn qbtn-approve" onClick={() => markCall(action.id, 'completed')}>✅ Mark Done</button>
                            <button className="qbtn qbtn-reject" onClick={() => markCall(action.id, 'failed')}>❌ Mark Failed</button>
                            <button className="qbtn qbtn-schedule" onClick={() => setScheduleAction(action)}>🔄 Re-schedule</button>
                          </>
                        )}

                        {action.token_request_status === 'approved' && (
                          <span className="qbtn-done">🌟 Approved — {action.green_tokens_earned} tokens minted</span>
                        )}
                        {action.token_request_status === 'rejected' && (
                          <span className="qbtn-rejected">❌ Rejected</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Farmers Tab */}
      {activeTab === 'farmers' && (
        <div className="admin-tab-content">
          <div className="farmers-header">
            <h3>👨‍🌾 Registered Farmers ({farmers.length})</h3>
            <button className="admin-btn-refresh" onClick={fetchFarmers}>🔄 Refresh</button>
          </div>
          {farmers.length === 0 ? (
            <div className="admin-empty">No farmers found</div>
          ) : (
            <div className="farmers-table-wrap">
              <table className="farmers-table">
                <thead>
                  <tr>
                    <th>Farm ID</th>
                    <th>Name</th>
                    <th>Phone</th>
                    <th>Latitude</th>
                    <th>Longitude</th>
                    <th>Area (ha)</th>
                    <th>Radius (m)</th>
                    <th>Profile</th>
                  </tr>
                </thead>
                <tbody>
                  {farmers.map(f => (
                    <tr key={f.farmer_id}>
                      <td><code>{f.farmer_id}</code></td>
                      <td>{f.name || '—'}</td>
                      <td>{f.phone || '—'}</td>
                      <td>{f.farm_latitude?.toFixed(4) ?? '—'}</td>
                      <td>{f.farm_longitude?.toFixed(4) ?? '—'}</td>
                      <td>{f.farm_size?.toFixed(1) ?? '—'}</td>
                      <td>{f.verification_radius_meters?.toFixed(0) ?? '—'}</td>
                      <td>
                        <button className="qbtn qbtn-schedule" onClick={() => setFarmProfileId(f.farmer_id)}>
                          🗺️ {f.has_profile ? 'Edit' : 'Set'} GPS
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Root Export — handles login gate ─────────────────────────────────────────
export default function AdminPanelRoot({ onLogout }) {
  const [adminSession, setAdminSession] = useState(() => {
    const stored = localStorage.getItem('admin_token');
    const user = localStorage.getItem('admin_user');
    return stored && user ? JSON.parse(user) : null;
  });

  const handleLogin = data => setAdminSession({ username: data.username, role: data.role });

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    setAdminSession(null);
    if (onLogout) onLogout();
  };

  if (!adminSession) return <AdminLogin onLogin={handleLogin} />;
  return <AdminPanel onLogout={handleLogout} />;
}
