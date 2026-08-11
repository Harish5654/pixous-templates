import { AlertTriangle } from 'lucide-react';

interface DataErrorProps {
  message?: string;
}

const DataError = ({ message }: DataErrorProps) => (
  <div
    style={{
      padding: '20px 24px',
      border: '1px solid var(--danger-soft)',
      borderRadius: 'var(--radius-md)',
      backgroundColor: 'var(--danger-soft)',
      color: 'var(--danger)',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
    }}
    role="alert"
  >
    <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
    <div>
      <strong>Couldn't load data</strong>
      <div style={{ fontSize: '0.85rem', marginTop: 2 }}>
        {message || 'The server may be unavailable or your session expired. Please try again in a moment.'}
      </div>
    </div>
  </div>
);

export default DataError;
