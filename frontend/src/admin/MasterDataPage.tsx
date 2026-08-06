import { useEffect, useMemo, useState } from 'react';
import { Plus, Search, Save, List as ListIcon, Building2, Languages as LanguagesIcon, AlertTriangle, ArrowUp, ArrowDown, Star, ChevronDown, ChevronRight, Trash2 } from 'lucide-react';
import { useMasterData, useUpdateMasterData, useTemplates, useDeleteTemplate } from '../api/queries';
import type { MasterDataItem, MasterDataLists, PriorityItem } from '../types/masterData';
import type { Template } from '../types/template';

const BADGE_CLASSES = ['badge-danger', 'badge-warning', 'badge-neutral', 'badge-success'];
const makeId = () => `md-${Math.random().toString(36).slice(2, 10)}`;

const Toggle = ({ checked, onChange, title }: { checked: boolean; onChange: (v: boolean) => void; title?: string }) => (
  <label className="switch" title={title}>
    <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    <span className="switch-track" />
    <span className="switch-thumb" />
  </label>
);

interface SimpleListEditorProps {
  noun: string;
  items: MasterDataItem[];
  usageCount: (name: string) => number;
  onChange: (items: MasterDataItem[]) => void;
  defaultName?: string;
  onSetDefault?: (name: string) => void;
  getTemplates?: (name: string) => Template[];
  onDeleteTemplate?: (id: string, name: string) => void;
}

const SimpleListEditor = ({ noun, items, usageCount, onChange, defaultName, onSetDefault, getTemplates, onDeleteTemplate }: SimpleListEditorProps) => {
  const [query, setQuery] = useState('');
  const [newName, setNewName] = useState('');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const filtered = useMemo(
    () => items.filter((i) => i.name.toLowerCase().includes(query.toLowerCase())),
    [items, query]
  );

  const handleAdd = () => {
    const name = newName.trim();
    if (!name) return;
    onChange([...items, { id: makeId(), name, active: true, parentId: null }]);
    setNewName('');
  };

  const handleRename = (id: string, name: string) => {
    onChange(items.map((i) => (i.id === id ? { ...i, name } : i)));
  };

  const handleToggleActive = (id: string, active: boolean) => {
    onChange(items.map((i) => (i.id === id ? { ...i, active } : i)));
  };

  return (
    <div>
      {items.length > 6 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px', maxWidth: '320px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '9px 12px' }}>
          <Search size={15} color="var(--text-tertiary)" />
          <input
            style={{ border: 'none', outline: 'none', background: 'transparent', width: '100%', fontSize: '0.88rem' }}
            placeholder={`Search ${noun.toLowerCase()}...`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
        {filtered.map((item) => {
          const count = usageCount(item.name);
          const isDefault = defaultName === item.name;
          const isExpanded = expanded.has(item.id);
          return (
            <div key={item.id}>
              <div className={`md-row ${item.active ? '' : 'inactive'}`}>
                <input
                  className="md-row-name"
                  style={{ flex: 1 }}
                  value={item.name}
                  onChange={(e) => handleRename(item.id, e.target.value)}
                />
                {isDefault && (
                  <span className="badge" style={{ backgroundColor: 'var(--accent-soft)', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                    <Star size={11} fill="currentColor" /> Default
                  </span>
                )}
                {onSetDefault && !isDefault && item.active && (
                  <button className="btn btn-outline" style={{ padding: '4px 10px', fontSize: '0.76rem', flexShrink: 0 }} onClick={() => onSetDefault(item.name)}>
                    Set as default
                  </button>
                )}
                {getTemplates ? (
                  <button
                    className="icon-btn"
                    style={{ width: 'auto', gap: '4px', padding: '2px 8px', fontSize: '0.78rem', color: 'var(--text-tertiary)', flexShrink: 0 }}
                    onClick={() => count > 0 && toggleExpand(item.id)}
                    disabled={count === 0}
                    title={count > 0 ? 'View templates in this category' : 'No templates in this category'}
                  >
                    {count} template{count === 1 ? '' : 's'}
                    {count > 0 && (isExpanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />)}
                  </button>
                ) : (
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', whiteSpace: 'nowrap', flexShrink: 0 }}>
                    {count} template{count === 1 ? '' : 's'}
                  </span>
                )}
                <Toggle checked={item.active} onChange={(v) => handleToggleActive(item.id, v)} title={item.active ? 'Active — visible for new templates' : 'Inactive — hidden for new templates'} />
              </div>

              {isExpanded && getTemplates && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', margin: '4px 0 4px 20px' }}>
                  {getTemplates(item.name).map((t) => (
                    <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 12px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-hover)' }}>
                      <span style={{ flex: 1, fontSize: '0.85rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.name}</span>
                      <span className={`badge ${t.status === 'Published' ? 'badge-success' : 'badge-warning'}`}>{t.status}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>{t.owner}</span>
                      <button className="icon-btn" title={`Delete "${t.name}"`} style={{ color: 'var(--danger)' }} onClick={() => onDeleteTemplate?.(t.id, t.name)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
        {filtered.length === 0 && (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', padding: '12px 0' }}>No {noun.toLowerCase()} match "{query}".</p>
        )}
      </div>

      <div className="md-add-row">
        <Plus size={16} color="var(--text-tertiary)" />
        <input
          style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', fontSize: '0.88rem' }}
          placeholder={`Add a new ${noun.toLowerCase().replace(/s$/, '')}...`}
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAdd(); } }}
        />
        <button className="btn" style={{ padding: '6px 12px', fontSize: '0.82rem' }} onClick={handleAdd} disabled={!newName.trim()}>
          Add
        </button>
      </div>
    </div>
  );
};

interface PriorityEditorProps {
  items: PriorityItem[];
  usageCount: (name: string) => number;
  onChange: (items: PriorityItem[]) => void;
}

const PriorityEditor = ({ items, usageCount, onChange }: PriorityEditorProps) => {
  const sorted = useMemo(() => [...items].sort((a, b) => a.order - b.order), [items]);

  const update = (id: string, patch: Partial<PriorityItem>) => {
    onChange(items.map((i) => (i.id === id ? { ...i, ...patch } : i)));
  };

  const move = (index: number, direction: 'up' | 'down') => {
    const next = [...sorted];
    const swapWith = direction === 'up' ? index - 1 : index + 1;
    if (swapWith < 0 || swapWith >= next.length) return;
    [next[index], next[swapWith]] = [next[swapWith], next[index]];
    onChange(next.map((item, i) => ({ ...item, order: i })));
  };

  const handleAdd = () => {
    const maxOrder = items.reduce((max, i) => Math.max(max, i.order), -1);
    onChange([
      ...items,
      { id: makeId(), name: 'New Priority', active: true, order: maxOrder + 1, badgeClass: 'badge-neutral', description: '', requiresAcknowledgementDefault: false },
    ]);
  };

  return (
    <div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '14px' }}>
        {sorted.map((item, index) => {
          const count = usageCount(item.name);
          return (
            <div key={item.id} className={`md-row ${item.active ? '' : 'inactive'}`} style={{ alignItems: 'flex-start', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', flexShrink: 0 }}>
                <button className="icon-btn" style={{ width: '24px', height: '20px' }} disabled={index === 0} onClick={() => move(index, 'up')}><ArrowUp size={13} /></button>
                <button className="icon-btn" style={{ width: '24px', height: '20px' }} disabled={index === sorted.length - 1} onClick={() => move(index, 'down')}><ArrowDown size={13} /></button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: '220px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input
                    className="md-row-name"
                    style={{ fontWeight: 600, flex: '0 1 160px' }}
                    value={item.name}
                    onChange={(e) => update(item.id, { name: e.target.value })}
                  />
                  <span className={`badge ${item.badgeClass}`}>{item.name || 'Preview'}</span>
                  <span style={{ fontSize: '0.76rem', color: 'var(--text-tertiary)' }}>{count} template{count === 1 ? '' : 's'}</span>
                </div>
                <input
                  className="md-row-name"
                  style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}
                  placeholder="Description shown to authors"
                  value={item.description}
                  onChange={(e) => update(item.id, { description: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flexShrink: 0 }}>
                <label className="form-label" style={{ marginBottom: 0, fontSize: '0.76rem' }}>Badge color</label>
                <select
                  className="form-input"
                  style={{ padding: '4px 8px', fontSize: '0.8rem', height: '30px' }}
                  value={item.badgeClass}
                  onChange={(e) => update(item.id, { badgeClass: e.target.value })}
                >
                  {BADGE_CLASSES.map((cls) => <option key={cls} value={cls}>{cls.replace('badge-', '')}</option>)}
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)' }}>Ack. default</span>
                <Toggle checked={item.requiresAcknowledgementDefault} onChange={(v) => update(item.id, { requiresAcknowledgementDefault: v })} title="Pre-fill 'Require Acknowledgement' when this priority is chosen" />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)' }}>Active</span>
                <Toggle checked={item.active} onChange={(v) => update(item.id, { active: v })} />
              </div>
            </div>
          );
        })}
      </div>
      <button className="btn btn-outline" onClick={handleAdd}>
        <Plus size={15} /> Add Priority
      </button>
    </div>
  );
};

type TabKey = 'categories' | 'departments' | 'languages' | 'priorities';

const MasterDataPage = () => {
  const { data, isLoading } = useMasterData();
  const { data: templates } = useTemplates();
  const updateMasterData = useUpdateMasterData();
  const deleteTemplate = useDeleteTemplate();
  const [lists, setLists] = useState<MasterDataLists | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('categories');
  const [saveError, setSaveError] = useState('');
  const [saveDone, setSaveDone] = useState(false);

  useEffect(() => {
    if (data) setLists(data.lists);
  }, [data]);

  const dirty = useMemo(() => {
    if (!data || !lists) return false;
    return JSON.stringify(data.lists) !== JSON.stringify(lists);
  }, [data, lists]);

  const categoryUsage = (name: string) => templates?.filter((t) => t.category === name).length || 0;
  const departmentUsage = (name: string) =>
    templates?.filter((t) => t.department === name || t.publishing.audience.departments.includes(name)).length || 0;
  const languageUsage = (name: string) => templates?.filter((t) => t.language === name).length || 0;
  const priorityUsage = (name: string) => templates?.filter((t) => t.publishing.priority === name).length || 0;
  const getTemplatesForCategory = (name: string) => templates?.filter((t) => t.category === name) || [];

  const handleDeleteTemplate = async (id: string, name: string) => {
    if (!window.confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try {
      await deleteTemplate.mutateAsync(id);
    } catch (err: any) {
      alert(`Delete failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleSave = async () => {
    if (!lists) return;
    setSaveError('');
    setSaveDone(false);
    try {
      await updateMasterData.mutateAsync(lists);
      setSaveDone(true);
      setTimeout(() => setSaveDone(false), 2500);
    } catch (err: any) {
      setSaveError(err?.response?.data?.detail || err.message || 'Failed to save master data.');
    }
  };

  if (isLoading || !lists) return <div>Loading master data...</div>;

  const TABS: { key: TabKey; label: string; icon: typeof ListIcon; count: number }[] = [
    { key: 'categories', label: 'Categories', icon: ListIcon, count: lists.categories.items.length },
    { key: 'departments', label: 'Departments', icon: Building2, count: lists.departments.items.length },
    { key: 'languages', label: 'Languages', icon: LanguagesIcon, count: lists.languages.items.length },
    { key: 'priorities', label: 'Notice Priorities', icon: AlertTriangle, count: lists.priorities.items.length },
  ];

  return (
    <div>
      <div className="page-header" style={{ position: 'sticky', top: 0, backgroundColor: 'var(--bg-canvas)', zIndex: 5, paddingTop: '2px' }}>
        <div>
          <h1>Master Data</h1>
          <p className="page-subtitle">
            Organization-wide reference lists used across templates and notices.
            {data && <> Last updated by {data.updatedBy} on {new Date(data.updatedAt).toLocaleString()}.</>}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {dirty && !updateMasterData.isPending && <span style={{ fontSize: '0.8rem', color: 'var(--warning)' }}>Unsaved changes</span>}
          <button className="btn" onClick={handleSave} disabled={!dirty || updateMasterData.isPending}>
            <Save size={16} /> {updateMasterData.isPending ? 'Saving...' : saveDone ? 'Saved' : 'Save Changes'}
          </button>
        </div>
      </div>

      {saveError && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', backgroundColor: 'var(--danger-soft)', color: 'var(--danger)', borderRadius: 'var(--radius-sm)', marginBottom: '18px', fontSize: '0.85rem' }}>
          <AlertTriangle size={16} /> {saveError}
        </div>
      )}

      <div className="md-tabs">
        {TABS.map(({ key, label, icon: Icon, count }) => (
          <button key={key} className={`md-tab ${activeTab === key ? 'active' : ''}`} onClick={() => setActiveTab(key)}>
            <Icon size={15} /> {label} <span className="md-tab-count">{count}</span>
          </button>
        ))}
      </div>

      <div className="card">
        {activeTab === 'categories' && (
          <SimpleListEditor
            noun="Categories"
            items={lists.categories.items}
            usageCount={categoryUsage}
            onChange={(items) => setLists({ ...lists, categories: { items } })}
            getTemplates={getTemplatesForCategory}
            onDeleteTemplate={handleDeleteTemplate}
          />
        )}

        {activeTab === 'departments' && (
          <SimpleListEditor
            noun="Departments"
            items={lists.departments.items}
            usageCount={departmentUsage}
            onChange={(items) => setLists({ ...lists, departments: { items } })}
          />
        )}

        {activeTab === 'languages' && (
          <SimpleListEditor
            noun="Languages"
            items={lists.languages.items}
            usageCount={languageUsage}
            defaultName={lists.languages.default}
            onSetDefault={(name) => setLists({ ...lists, languages: { ...lists.languages, default: name } })}
            onChange={(items) => {
              const oldDefaultItem = lists.languages.items.find((i) => i.name === lists.languages.default);
              const newDefaultName = oldDefaultItem ? (items.find((i) => i.id === oldDefaultItem.id)?.name || lists.languages.default) : lists.languages.default;
              setLists({ ...lists, languages: { ...lists.languages, items, default: newDefaultName } });
            }}
          />
        )}

        {activeTab === 'priorities' && (
          <PriorityEditor
            items={lists.priorities.items}
            usageCount={priorityUsage}
            onChange={(items) => setLists({ ...lists, priorities: { items } })}
          />
        )}
      </div>
    </div>
  );
};

export default MasterDataPage;
