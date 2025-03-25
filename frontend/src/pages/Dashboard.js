import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/api';
import './Dashboard.css';

function Dashboard() {
  const { currentUser } = useAuth();
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch user's strategies when component mounts
    const fetchStrategies = async () => {
      try {
        setLoading(true);
        const response = await api.get('/api/strategies');
        setStrategies(response.data);
      } catch (error) {
        setError('Failed to fetch strategies. Please try again later.');
        console.error('Error fetching strategies:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStrategies();
  }, []);

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>Welcome, {currentUser?.username || currentUser?.email}</h2>
        <p>This is your trading strategy dashboard</p>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="dashboard-cards">
        <div className="dashboard-card">
          <h3>Your Strategies</h3>
          {loading ? (
            <p>Loading strategies...</p>
          ) : strategies.length > 0 ? (
            <ul className="strategy-list">
              {strategies.map(strategy => (
                <li key={strategy.id} className="strategy-item">
                  <div className="strategy-header">
                    <h4>{strategy.name}</h4>
                    <span className={`strategy-status strategy-status-${strategy.status.toLowerCase()}`}>
                      {strategy.status}
                    </span>
                  </div>
                  <p>{strategy.description}</p>
                  <div className="strategy-footer">
                    <span>Created: {new Date(strategy.created_at).toLocaleDateString()}</span>
                    <button className="btn btn-sm btn-primary">View Details</button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">
              <p>You don't have any strategies yet.</p>
              <button className="btn btn-primary">Create New Strategy</button>
            </div>
          )}
        </div>

        <div className="dashboard-card">
          <h3>Recent Activity</h3>
          <div className="activity-list">
            <div className="activity-item">
              <span className="activity-icon">📊</span>
              <div className="activity-content">
                <p>System calculated new indicators for BTC/USD</p>
                <span className="activity-time">2 hours ago</span>
              </div>
            </div>
            <div className="activity-item">
              <span className="activity-icon">🔍</span>
              <div className="activity-content">
                <p>Data integrity check completed</p>
                <span className="activity-time">4 hours ago</span>
              </div>
            </div>
            <div className="activity-item">
              <span className="activity-icon">💡</span>
              <div className="activity-content">
                <p>Strategy validation complete</p>
                <span className="activity-time">Yesterday</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-footer">
        <button className="btn btn-primary">Create New Strategy</button>
        <button className="btn btn-secondary">View All Strategies</button>
      </div>
    </div>
  );
}

export default Dashboard;