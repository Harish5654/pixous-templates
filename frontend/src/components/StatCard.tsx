import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  accent?: 'default' | 'success' | 'warning' | 'danger';
  onClick?: () => void;
}

const ACCENT_COLORS: Record<string, { bg: string; fg: string }> = {
  default: { bg: 'var(--accent-soft)', fg: 'var(--accent-primary)' },
  success: { bg: 'var(--success-soft)', fg: 'var(--success)' },
  warning: { bg: 'var(--warning-soft)', fg: 'var(--warning)' },
  danger: { bg: 'var(--danger-soft)', fg: 'var(--danger)' },
};

const StatCard = ({ label, value, icon: Icon, accent = 'default', onClick }: StatCardProps) => {
  const colors = ACCENT_COLORS[accent];
  return (
    <div
      className="stat-card"
      onClick={onClick}
      style={onClick ? { cursor: 'pointer', transition: 'box-shadow 0.15s ease, border-color 0.15s ease' } : undefined}
      onMouseEnter={onClick ? (e) => { e.currentTarget.style.boxShadow = 'var(--shadow-md)'; e.currentTarget.style.borderColor = '#d1d5db'; } : undefined}
      onMouseLeave={onClick ? (e) => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.borderColor = 'var(--border-color)'; } : undefined}
    >
      <div className="stat-card-icon" style={{ backgroundColor: colors.bg, color: colors.fg }}>
        <Icon size={20} />
      </div>
      <div>
        <div style={{ fontSize: '1.6rem', fontWeight: 700, lineHeight: 1.1 }}>{value}</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{label}</div>
      </div>
    </div>
  );
};

export default StatCard;
