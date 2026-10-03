import React, { useState } from 'react';
import { useAuth } from '../auth/AuthContext';

interface LoginProps {
  onSwitchToRegister: () => void;
}

export const LoginPage: React.FC<LoginProps> = ({ onSwitchToRegister }) => {
  const { login, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSubmitting(true);
    try {
      await login({ email, password });
    } catch {
      // Error handled by AuthContext
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '40px auto', padding: 24, border: '1px solid #e2e8f0', borderRadius: 8 }}>
      <h1 style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 8 }}>RentBook Login</h1>
      <p style={{ color: '#64748b', marginBottom: 20 }}>Digital rent register for Indian landlords</p>

      {error && (
        <div style={{ background: '#fee2e2', color: '#991b1b', padding: 10, borderRadius: 6, marginBottom: 16 }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 4 }}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: 6 }}
            placeholder="landlord@example.com"
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 4 }}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: 6 }}
            placeholder="Min 8 characters"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          style={{
            width: '100%',
            padding: 10,
            background: '#2563eb',
            color: '#fff',
            fontWeight: 600,
            borderRadius: 6,
            border: 'none',
            cursor: 'pointer',
          }}
        >
          {submitting ? 'Logging in...' : 'Sign In'}
        </button>
      </form>

      <div style={{ marginTop: 16, textAlign: 'center', fontSize: 14 }}>
        Don't have an account?{' '}
        <button
          type="button"
          onClick={onSwitchToRegister}
          style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', textDecoration: 'underline' }}
        >
          Register
        </button>
      </div>
    </div>
  );
};
