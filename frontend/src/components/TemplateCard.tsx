import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Copy, FileText, Wand2 } from 'lucide-react';
import type { Template } from '../types/template';
import { useFavoritesStore } from '../store/favoritesStore';
import { useAuthStore } from '../store/authStore';
import { useCreateTemplate, useUpdateTemplate } from '../api/queries';
import FillAndGenerateModal from './FillAndGenerateModal';

const STATUS_BADGE: Record<string, string> = {
  Published: 'badge-success',
  'Pending Approval': 'badge-warning',
  Draft: 'badge-warning',
  Archived: 'badge-neutral',
};

type CardMode = 'use' | 'manage' | 'combined';

interface TemplateCardProps {
  template: Template;
  mode?: CardMode;
}

const TemplateCard = ({ template, mode = 'combined' }: TemplateCardProps) => {
  const navigate = useNavigate();
  const { isFavorite, toggleFavorite } = useFavoritesStore();
  const currentUser = useAuthStore((s) => s.user);
  const canAuthor = currentUser?.role === 'Admin' || currentUser?.role === 'Editor';
  const createTemplate = useCreateTemplate();
  const updateTemplate = useUpdateTemplate();
  const showUseAction = mode === 'use' || mode === 'combined';
  const showManageActions = mode === 'manage' || (mode === 'combined' && canAuthor);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(template.name);
  const favorite = isFavorite(template.id);

  const startRename = () => {
    setRenameValue(template.name);
    setIsRenaming(true);
  };

  const commitRename = async () => {
    setIsRenaming(false);
    const name = renameValue.trim();
    if (!name || name === template.name) { setRenameValue(template.name); return; }
    try {
      await updateTemplate.mutateAsync({ id: template.id, payload: { ...template, name } });
    } catch (err: any) {
      alert(`Rename failed: ${err?.response?.data?.detail || err.message}`);
      setRenameValue(template.name);
    }
  };

  const handleDuplicate = async () => {
    try {
      const copy = await createTemplate.mutateAsync({
        ...template,
        name: `Copy of ${template.name}`,
        status: 'Draft',
      });
      navigate(`/templates/${copy.id}/edit`);
    } catch (err: any) {
      alert(`Duplicate failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleEdit = () => navigate(`/templates/${template.id}/edit`);

  return (
    <div className="template-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
          <div style={{ padding: '10px', backgroundColor: 'var(--accent-soft)', borderRadius: 'var(--radius-md)', flexShrink: 0 }}>
            <FileText size={20} color="var(--accent-primary)" />
          </div>
          <div style={{ minWidth: 0 }}>
            {isRenaming ? (
              <input
                autoFocus
                className="form-input"
                style={{ fontSize: '1rem', fontWeight: 600, padding: '2px 6px', height: 'auto' }}
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={commitRename}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); commitRename(); } if (e.key === 'Escape') { setIsRenaming(false); setRenameValue(template.name); } }}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <h3
                style={{ margin: 0, fontSize: '1rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', cursor: showManageActions ? 'text' : 'default' }}
                title={showManageActions ? 'Click to rename' : undefined}
                onClick={showManageActions ? startRename : undefined}
              >
                {template.name}
              </h3>
            )}
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{template.category}</span>
          </div>
        </div>
        <button
          className={`favorite-btn ${favorite ? 'active' : ''}`}
          onClick={() => toggleFavorite(template.id)}
          title={favorite ? 'Remove from favorites' : 'Add to favorites'}
        >
          <Star size={18} fill={favorite ? 'currentColor' : 'none'} />
        </button>
      </div>

      <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '16px', flex: 1, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {template.description}
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid var(--border-color)', paddingTop: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
          <span className={`badge ${STATUS_BADGE[template.status] || 'badge-neutral'}`} style={{ flexShrink: 0 }}>{template.status}</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>v{template.version} · {template.owner}</span>
        </div>

        <div className="template-card-actions" style={{ justifyContent: 'flex-end', flexWrap: 'nowrap' }}>
          {showManageActions && (
            <button className="icon-btn" title="Duplicate" disabled={createTemplate.isPending} onClick={handleDuplicate} style={{ flexShrink: 0 }}>
              <Copy size={16} />
            </button>
          )}
          {showUseAction && (
            <button
              className="btn btn-outline"
              style={{ padding: '6px 14px', fontSize: '0.82rem', whiteSpace: 'nowrap', flexShrink: 0 }}
              title="Fill in the variables and generate your document"
              onClick={() => setPreviewOpen(true)}
            >
              <Wand2 size={15} /> Fill &amp; Generate
            </button>
          )}
          {showManageActions && (
            <button className="btn" style={{ padding: '6px 14px', fontSize: '0.82rem', whiteSpace: 'nowrap', flexShrink: 0 }} onClick={handleEdit}>
              Open
            </button>
          )}
        </div>
      </div>

      {previewOpen && <FillAndGenerateModal template={template} onClose={() => setPreviewOpen(false)} />}
    </div>
  );
};

export default TemplateCard;
