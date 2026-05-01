import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import AddPatientForm from './components/AddPatientForm';
import HeapVisualizer from './components/HeapVisualizer';
import { Activity } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [queue, setQueue] = useState([]);
  const [heapData, setHeapData] = useState(null);

  const fetchState = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/state`);
      const data = await res.json();
      setQueue(data.queue);
      setHeapData(data.visualTree);
    } catch (e) {
      console.error('Failed to fetch state', e);
    }
  };

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, []);

  const handleProcessPatient = async () => {
    try {
      await fetch(`${API_BASE}/api/patients/process`, {
        method: 'POST'
      });
      fetchState(); // Immediately fetch state after processing
    } catch (e) {
      console.error('Failed to process patient', e);
    }
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Activity color="var(--accent)" size={32} />
          <h1>VitalTriage</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '-1rem' }}>
          Real-time Priority Queue & 4-ary Heap Visualizer
        </p>
        
        <AddPatientForm onAdded={fetchState} />
      </div>
      
      <div className="main-content">
        <div className="header-actions">
          <h2>Active Priority Queue</h2>
          {queue.length > 0 && (
            <button className="danger" onClick={handleProcessPatient}>
              Process Next Patient ({queue[0].name})
            </button>
          )}
        </div>
        
        {/* Heap Visualizer Section */}
        <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--panel-border)', background: 'rgba(255,255,255,0.02)' }}>
            <h3 style={{ fontSize: '1rem' }}>Live 4-ary Max-Heap</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Complete tree where each node has up to 4 children. Patients ordered by Priority Score.
            </p>
          </div>
          <HeapVisualizer data={heapData} />
        </div>

        {/* Queue Grid Section */}
        <Dashboard queue={queue} />
      </div>
    </div>
  );
}

export default App;
