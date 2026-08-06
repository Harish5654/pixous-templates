import { useMemo, useState } from 'react';
import { useTemplates, useMasterData } from '../api/queries';
import { Megaphone, CheckCircle2, Paperclip, Calendar } from 'lucide-react';
import { useAcknowledgementsStore } from '../store/acknowledgementsStore';
import EmptyState from '../components/EmptyState';
import FillAndGenerateModal from '../components/FillAndGenerateModal';
import type { Template } from '../types/template';

const NoticeCard = ({ notice }: { notice: Template }) => {
  const { data: masterData } = useMasterData();
  const { isAcknowledged, toggleAcknowledge } = useAcknowledgementsStore();
  const [previewOpen, setPreviewOpen] = useState(false);
  const acknowledged = isAcknowledged(notice.id);
  const requiresAck = notice.publishing.notificationBehavior.requireAcknowledgement;
  const { effectiveDate, expiryDate } = notice.publishing;
  const priorityBadgeClass = masterData?.lists.priorities.items.find(p => p.name === notice.publishing.priority)?.badgeClass || 'badge-neutral';

  return (
    <div className="template-card" style={{ padding: 0, overflow: 'hidden' }}>
      {notice.banner ? (
        <img src={notice.banner} alt="" style={{ width: '100%', height: '120px', objectFit: 'cover' }} />
      ) : (
        <div style={{ width: '100%', height: '60px', backgroundColor: 'var(--accent-soft)', display: 'flex', alignItems: 'center', paddingLeft: '20px' }}>
          <Megaphone size={20} color="var(--accent-primary)" />
        </div>
      )}

      <div style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', flex: 1 }}>
        <div style={{ display: 'flex', gap: '6px', marginBottom: '10px' }}>
          <span className="badge badge-neutral">{notice.category}</span>
          <span className={`badge ${priorityBadgeClass}`}>{notice.publishing.priority}</span>
        </div>

        <h3 style={{ fontSize: '1rem', marginBottom: '6px', cursor: 'pointer' }} onClick={() => setPreviewOpen(true)}>{notice.name}</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '12px', flex: 1 }}>{notice.description}</p>

        {(effectiveDate || expiryDate) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-tertiary)', marginBottom: '10px' }}>
            <Calendar size={13} />
            {effectiveDate || '—'} {expiryDate ? `to ${expiryDate}` : '(no end date)'}
          </div>
        )}

        {notice.allowed_attachments.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '12px' }}>
            {notice.allowed_attachments.map(name => (
              <span key={name} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', padding: '3px 8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-hover)', color: 'var(--text-secondary)' }}>
                <Paperclip size={11} /> {name}
              </span>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '14px', marginTop: 'auto' }}>
          <button className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => setPreviewOpen(true)}>Read Notice</button>
          {requiresAck ? (
            <button
              className="btn"
              style={{ padding: '6px 12px', fontSize: '0.8rem', backgroundColor: acknowledged ? 'var(--success)' : 'var(--accent-primary)' }}
              onClick={() => toggleAcknowledge(notice.id)}
            >
              <CheckCircle2 size={14} /> {acknowledged ? 'Acknowledged' : 'Acknowledge'}
            </button>
          ) : (
            <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>No action required</span>
          )}
        </div>
      </div>

      {previewOpen && <FillAndGenerateModal template={notice} onClose={() => setPreviewOpen(false)} />}
    </div>
  );
};

const NoticeBoardPage = () => {
  const { data: templates, isLoading } = useTemplates();
  const { data: masterData } = useMasterData();
  const [category, setCategory] = useState<string | null>(null);

  const priorityOrder = useMemo(() => {
    const order: Record<string, number> = {};
    masterData?.lists.priorities.items.forEach(p => { order[p.name] = p.order; });
    return order;
  }, [masterData]);

  const notices = useMemo(() => {
    const pinned = (templates || []).filter(t => t.status === 'Published' && t.publishing.notificationBehavior.pinToNoticeBoard);
    return pinned.sort((a, b) => (priorityOrder[a.publishing.priority] ?? 9) - (priorityOrder[b.publishing.priority] ?? 9));
  }, [templates, priorityOrder]);

  const categories = useMemo(() => Array.from(new Set(notices.map(n => n.category))), [notices]);
  const filtered = category ? notices.filter(n => n.category === category) : notices;

  if (isLoading) return <div>Loading notice board...</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Notice Board</h1>
          <p className="page-subtitle">Company-wide notices pinned for all employees.</p>
        </div>
      </div>

      {notices.length === 0 ? (
        <EmptyState
          icon={Megaphone}
          title="No active notices"
          description="Notices marked 'Pin to Notice Board' in the template editor will appear here."
        />
      ) : (
        <>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
            <button
              className="btn btn-outline"
              style={{ padding: '6px 14px', fontSize: '0.85rem', backgroundColor: category === null ? 'var(--accent-soft)' : undefined, borderColor: category === null ? 'var(--accent-primary)' : undefined, color: category === null ? 'var(--accent-primary)' : undefined }}
              onClick={() => setCategory(null)}
            >
              All
            </button>
            {categories.map(cat => (
              <button
                key={cat}
                className="btn btn-outline"
                style={{ padding: '6px 14px', fontSize: '0.85rem', backgroundColor: category === cat ? 'var(--accent-soft)' : undefined, borderColor: category === cat ? 'var(--accent-primary)' : undefined, color: category === cat ? 'var(--accent-primary)' : undefined }}
                onClick={() => setCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {filtered.map(n => <NoticeCard key={n.id} notice={n} />)}
          </div>
        </>
      )}
    </div>
  );
};

export default NoticeBoardPage;
