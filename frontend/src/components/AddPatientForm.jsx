import React, { useState } from 'react';
import { UserPlus } from 'lucide-react';

const AddPatientForm = ({ onAdded }) => {
  const [formData, setFormData] = useState({
    name: '',
    priority: '10',
    symptoms: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const newPatient = {
      ...formData,
      priority: parseInt(formData.priority, 10)
    };

    try {
      await fetch('/api/patients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPatient)
      });
      // Reset form
      setFormData({ name: '', priority: '10', symptoms: '' });
      if (onAdded) onAdded();
    } catch (err) {
      console.error('Failed to add patient', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ flex: 1, overflowY: 'auto' }}>
      <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <UserPlus size={20} color="var(--accent)" />
        New Patient Intake
      </h3>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Full Name</label>
          <input type="text" name="name" value={formData.name} onChange={handleChange} required placeholder="e.g. John Doe" />
        </div>
        
        <div className="form-group">
          <label>Priority (1-20)</label>
          <input type="number" name="priority" min="1" max="20" value={formData.priority} onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label>Symptoms</label>
          <textarea 
            name="symptoms" 
            value={formData.symptoms} 
            onChange={handleChange} 
            required 
            placeholder="Describe symptoms... (e.g. chest pain, mild headache)"
            rows={3}
          />
        </div>

        <button type="submit" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
          {loading ? 'Adding...' : 'Add to Triage Queue'}
        </button>
      </form>
    </div>
  );
};

export default AddPatientForm;
