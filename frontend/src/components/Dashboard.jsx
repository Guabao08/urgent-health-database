import React from 'react';
import { HeartPulse, Clock, AlertCircle } from 'lucide-react';

const Dashboard = ({ queue }) => {
  if (!queue || queue.length === 0) {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--text-secondary)' }}>
        <HeartPulse size={48} color="var(--panel-border)" style={{ marginBottom: '1rem' }} />
        <h3>No Patients in Queue</h3>
        <p>The priority queue is currently empty.</p>
      </div>
    );
  }

  const getPriorityInfo = (score) => {
    if (score >= 15) return { label: 'High', class: 'high' };
    if (score >= 8) return { label: 'Medium', class: 'medium' };
    return { label: 'Low', class: 'low' };
  };

  return (
    <div className="queue-grid">
      {queue.map((patient, index) => {
        const priorityInfo = getPriorityInfo(patient.priority);
        return (
          <div key={patient.id} className="glass-panel patient-card" data-priority={priorityInfo.class}>
            <div className="card-header">
              <div>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>{patient.name}</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  ID: {patient.id % 10000}
                </span>
              </div>
              <div className={`priority-badge ${priorityInfo.class}`}>
                Priority {patient.priority}/20
              </div>
            </div>
            
            <div style={{ marginTop: '0.5rem', marginBottom: '0.5rem' }}>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Symptoms:</strong>
              <p style={{ fontSize: '0.95rem' }}>{patient.symptoms || 'None reported'}</p>
            </div>

            <div className="vitals-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="vital-item">
                <Clock size={14} color="var(--text-secondary)" />
                Wait Time: {Math.floor((Date.now() - patient.timestamp) / 60000)} mins
              </div>
            </div>
            
            {index === 0 && (
              <div style={{ position: 'absolute', top: '-1px', right: '-1px', background: 'var(--danger)', color: '#fff', fontSize: '0.7rem', padding: '0.2rem 1rem', borderBottomLeftRadius: '8px', fontWeight: 'bold' }}>
                NEXT UP
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// Extracted mini icon
const ActivityIcon = ({ bp }) => {
  return <AlertCircle size={14} color={bp !== 'Normal' ? 'var(--warning)' : 'var(--success)'} />;
};

export default Dashboard;
