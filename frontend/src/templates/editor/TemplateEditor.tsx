import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import { useTemplate, useVariables, useAIAction, useCreateTemplate, useUpdateTemplate, useMasterData, useUpdateMasterData, useSubmitForApproval } from '../../api/queries';
import DOMPurify from 'dompurify';
import { useAuthStore } from '../../store/authStore';
import {
  Save, ArrowLeft, Settings2, Play, Send, CheckCircle2, ArrowUp, ArrowDown, Trash2, Plus, Zap,
  Undo2, Redo2, PanelRightClose, PanelRightOpen, Search, Layers, Users, Megaphone, Image, Paperclip, Info, X
} from 'lucide-react';
import type { ChannelData, Channels, BrandingConfig, SectionData, ChecklistItem, PublishingConfig, AudienceSelection, NotificationBehavior, EventTrigger, EventType, Variable } from '../../types/template';
import { useRecentStore } from '../../store/recentStore';
import Accordion from '../../components/Accordion';

const AI_ACTIONS = ["Improve", "Professional", "Friendly", "Formal", "Shorter", "Longer", "Grammar", "Translate", "Company Tone"];
const LOCATIONS = ["Bangalore", "Mumbai", "Delhi", "Remote"];
const ROLES = ["Employee", "Manager", "Admin"];
const EVENT_TYPES: EventType[] = ["Birthday", "Anniversary", "Promotion", "New Joiner", "Farewell", "Certification", "Award", "Wedding", "Baby", "Achievement"];
const NOTICE_CATEGORIES = ["Security", "Infrastructure", "IT", "HR", "Facilities", "Projects", "Management", "Support"];

const DEFAULT_PUBLISHING: PublishingConfig = {
  priority: 'Normal',
  publishImmediately: true,
  effectiveDate: '',
  expiryDate: '',
  audience: { allEmployees: true, departments: [], locations: [], roles: [] },
  notificationBehavior: { requireAcknowledgement: false, allowComments: true, pinToNoticeBoard: false }
};

const DEFAULT_EVENT_TRIGGER: EventTrigger = {
  enabled: false,
  eventType: 'Birthday',
  autoGenerate: false,
  autoPublish: false,
  leadTimeDays: 0
};

const TemplateEditor = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = !id;
  
  const { data: template, isLoading: isTemplateLoading } = useTemplate(id || '');
  const { data: variables } = useVariables();
  const { data: masterData } = useMasterData();
  const { addRecent } = useRecentStore();
  const aiAction = useAIAction();
  const createTemplate = useCreateTemplate();
  const updateTemplate = useUpdateTemplate();
  const updateMasterData = useUpdateMasterData();
  const submitForApproval = useSubmitForApproval();
  const currentUser = useAuthStore((s) => s.user);
  const canManageMasterData = currentUser?.role === 'Admin';

  const [activeChannel, setActiveChannel] = useState<string>('email');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [mockChecklistState, setMockChecklistState] = useState<Record<string, string>>({});
  const [panelOpen, setPanelOpen] = useState(true);
  const [variableSearch, setVariableSearch] = useState('');
  const [previewWidth, setPreviewWidth] = useState<'desktop' | 'a4'>('desktop');
  const [pendingTranslate, setPendingTranslate] = useState(false);
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');

  const [metadata, setMetadata] = useState({
    name: 'Untitled Template',
    description: '',
    purpose: '',
    category: 'Client Communication',
    status: 'Draft',
    department: 'General',
    owner: currentUser?.name || 'Unknown',
    tags: [] as string[],
    language: 'English',
    visibility: 'Internal',
    branding: {
      logoEnabled: true,
      signatureEnabled: true,
      footerEnabled: true,
      letterheadEnabled: false,
      companyDetailsEnabled: true,
    } as BrandingConfig,
    channels: {
      email: { enabled: true, subject: '', content: '' },
      whatsapp: { enabled: false, subject: '', content: '' },
      sms: { enabled: false, subject: '', content: '' }
    } as Channels,
    sections: [] as SectionData[],
    checklistItems: [] as ChecklistItem[],
    signoffRole: '',
    publishing: DEFAULT_PUBLISHING,
    eventTrigger: DEFAULT_EVENT_TRIGGER,
    banner: '',
    allowed_attachments: [] as string[],
    variables: [] as string[],
    approval_required: false,
    approved_by: '',
    version: 1,
    created_by: currentUser?.name || '',
    updated_by: currentUser?.name || '',
    created_at: '',
    updated_at: ''
  });

  const [newAttachment, setNewAttachment] = useState('');
  const appliedDefaultLanguage = React.useRef(false);

  useEffect(() => {
    if (isNew && masterData && !appliedDefaultLanguage.current) {
      appliedDefaultLanguage.current = true;
      setMetadata(prev => ({ ...prev, language: masterData.lists.languages.default }));
    }
  }, [isNew, masterData]);

  const activeCategories = masterData?.lists.categories.items.filter(c => c.active || c.name === metadata.category) || [];
  const activeDepartments = masterData?.lists.departments.items.filter(d => d.active || d.name === metadata.department) || [];
  const activeLanguages = masterData?.lists.languages.items.filter(l => l.active || l.name === metadata.language) || [];
  const priorityOptions = [...(masterData?.lists.priorities.items || [])]
    .filter(p => p.active || p.name === metadata.publishing.priority)
    .sort((a, b) => a.order - b.order);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder: 'Start writing your template...' }),
    ],
    content: '',
    onUpdate: ({ editor }) => {
      handleChannelChange(activeChannel, 'content', editor.getHTML());
    }
  });

  // Hydrate the editor exactly once per template load. Channel switching
  // afterwards is handled by switchChannel(), so this deliberately skips
  // re-running when activeChannel changes.
  const hydratedIdRef = React.useRef<string | null>(null);

  useEffect(() => {
    if (template && editor) {
      if (hydratedIdRef.current === template.id) return;
      hydratedIdRef.current = template.id;
      setMetadata({
        name: template.name,
        description: template.description,
        purpose: template.purpose || '',
        category: template.category,
        status: template.status,
        department: template.department,
        owner: template.owner,
        tags: template.tags || [],
        language: template.language,
        visibility: template.visibility,
        branding: template.branding,
        channels: template.channels,
        sections: template.sections || [],
        checklistItems: template.checklistItems || [],
        signoffRole: template.signoffRole || '',
        publishing: template.publishing || DEFAULT_PUBLISHING,
        eventTrigger: template.eventTrigger || DEFAULT_EVENT_TRIGGER,
        banner: template.banner || '',
        allowed_attachments: template.allowed_attachments || [],
        variables: template.variables || [],
        approval_required: template.approval_required ?? false,
        approved_by: template.approved_by || '',
        version: template.version || 1,
        created_by: template.created_by || '',
        updated_by: template.updated_by || '',
        created_at: template.created_at || '',
        updated_at: template.updated_at || ''
      });
      const isNotice = NOTICE_CATEGORIES.includes(template.category);
      // Notice-category templates normally carry a 'notice' channel; when one
      // is missing (e.g. regular document templates that live in those
      // categories), fall back to the first enabled channel so content loads.
      if (isNotice) {
        const hasNotice = !!template.channels['notice']?.enabled;
        const loadChannel = hasNotice
          ? 'notice'
          : (Object.keys(template.channels).find(k => template.channels[k]?.enabled) || activeChannel);
        setActiveChannel(loadChannel);
        editor.commands.setContent(template.channels[loadChannel]?.content || '');
      } else {
        editor.commands.setContent(template.channels[activeChannel]?.content || '');
      }
      if (!isNew) addRecent(template.id);
    }
  }, [template, editor, activeChannel, isNew, addRecent]);

  if (!isNew && isTemplateLoading) return <div>Loading editor...</div>;

  const isMeetingBuilder = metadata.category === 'Meeting Minutes';
  const isChecklistBuilder = metadata.category === 'Checklists';
  const isEventBuilder = metadata.category === 'Employee Announcements';
  const isNoticeBuilder = NOTICE_CATEGORIES.includes(metadata.category);
  const isCommBuilder = !isMeetingBuilder && !isChecklistBuilder && !isNoticeBuilder;

  // --- Comm Builder Methods ---
  const switchChannel = (channel: string) => {
    setActiveChannel(channel);
    if (editor) editor.commands.setContent(metadata.channels[channel]?.content || '');
  };

  const handleChannelChange = (channel: string, field: keyof ChannelData, value: any) => {
    setMetadata(prev => ({
      ...prev,
      channels: {
        ...prev.channels,
        [channel]: { ...prev.channels[channel], [field]: value }
      }
    }));
  };

  // --- Meeting Builder Methods ---
  const moveSection = (index: number, direction: 'up' | 'down') => {
    const newSections = [...metadata.sections];
    if (direction === 'up' && index > 0) {
      [newSections[index], newSections[index - 1]] = [newSections[index - 1], newSections[index]];
    } else if (direction === 'down' && index < newSections.length - 1) {
      [newSections[index], newSections[index + 1]] = [newSections[index + 1], newSections[index]];
    }
    newSections.forEach((s, i) => s.order = i + 1);
    setMetadata(prev => ({ ...prev, sections: newSections }));
  };

  const toggleSection = (id: string, enabled: boolean) => {
    setMetadata(prev => ({
      ...prev,
      sections: prev.sections.map(s => s.id === id ? { ...s, enabled } : s)
    }));
  };

  // --- Checklist Builder Methods ---
  const updateChecklistItem = (id: string, field: keyof ChecklistItem, value: any) => {
    setMetadata(prev => ({
      ...prev,
      checklistItems: prev.checklistItems.map(item => item.id === id ? { ...item, [field]: value } : item)
    }));
  };

  const moveChecklistItem = (index: number, direction: 'up' | 'down') => {
    const newItems = [...metadata.checklistItems];
    if (direction === 'up' && index > 0) {
      [newItems[index], newItems[index - 1]] = [newItems[index - 1], newItems[index]];
    } else if (direction === 'down' && index < newItems.length - 1) {
      [newItems[index], newItems[index + 1]] = [newItems[index + 1], newItems[index]];
    }
    setMetadata(prev => ({ ...prev, checklistItems: newItems }));
  };

  const addChecklistItem = () => {
    const newItem: ChecklistItem = {
      id: `c${Date.now()}`,
      title: 'New Task',
      description: '',
      mandatory: true,
      ownerRole: 'Any',
      evidenceRequired: false
    };
    setMetadata(prev => ({ ...prev, checklistItems: [...prev.checklistItems, newItem] }));
  };

  const removeChecklistItem = (id: string) => {
    setMetadata(prev => ({ ...prev, checklistItems: prev.checklistItems.filter(i => i.id !== id) }));
  };

  // --- Shared Methods ---
  const handleBrandingChange = (field: keyof BrandingConfig, value: boolean) => {
    setMetadata(prev => ({ ...prev, branding: { ...prev.branding, [field]: value } }));
  };

  // --- Notice Board Methods ---
  const addAttachment = () => {
    const name = newAttachment.trim();
    if (!name) return;
    setMetadata(prev => ({ ...prev, allowed_attachments: [...prev.allowed_attachments, name] }));
    setNewAttachment('');
  };

  const removeAttachment = (name: string) => {
    setMetadata(prev => ({ ...prev, allowed_attachments: prev.allowed_attachments.filter(a => a !== name) }));
  };

  // --- Publishing & Lifecycle Methods ---
  const handlePublishingChange = (field: keyof PublishingConfig, value: any) => {
    setMetadata(prev => ({ ...prev, publishing: { ...prev.publishing, [field]: value } }));
  };

  const handlePriorityChange = (priorityName: string) => {
    const priorityDef = masterData?.lists.priorities.items.find(p => p.name === priorityName);
    setMetadata(prev => ({
      ...prev,
      publishing: {
        ...prev.publishing,
        priority: priorityName,
        notificationBehavior: {
          ...prev.publishing.notificationBehavior,
          requireAcknowledgement: priorityDef?.requiresAcknowledgementDefault ?? prev.publishing.notificationBehavior.requireAcknowledgement,
        },
      },
    }));
  };

  const handleAudienceChange = (field: keyof AudienceSelection, value: any) => {
    setMetadata(prev => ({ ...prev, publishing: { ...prev.publishing, audience: { ...prev.publishing.audience, [field]: value } } }));
  };

  const toggleAudienceListItem = (field: 'departments' | 'locations' | 'roles', value: string) => {
    setMetadata(prev => {
      const list = prev.publishing.audience[field];
      const nextList = list.includes(value) ? list.filter(v => v !== value) : [...list, value];
      return { ...prev, publishing: { ...prev.publishing, audience: { ...prev.publishing.audience, [field]: nextList } } };
    });
  };

  const handleNotificationBehaviorChange = (field: keyof NotificationBehavior, value: boolean) => {
    setMetadata(prev => ({ ...prev, publishing: { ...prev.publishing, notificationBehavior: { ...prev.publishing.notificationBehavior, [field]: value } } }));
  };

  // --- Event Trigger Methods ---
  const handleEventTriggerChange = (field: keyof EventTrigger, value: any) => {
    setMetadata(prev => ({ ...prev, eventTrigger: { ...prev.eventTrigger, [field]: value } }));
  };

  const generateNow = () => {
    setPreviewOpen(true);
  };

  const substituteVariables = (content: string) => {
    if (!content) return content;
    // Sanitize authored HTML before rendering the preview (stored-XSS defense).
    return DOMPurify.sanitize(content).replace(/\{\{(\w+)\}\}/g, (match, varName) => {
      const found = variables?.find(v => v.name === varName);
      return found ? found.default_value : match;
    });
  };

  const insertVariable = (varName: string) => {
    editor?.chain().focus().insertContent(`{{${varName}}}`).run();
  };

  const extractPlaceholders = (...texts: (string | undefined)[]): string[] => {
    const found = new Set<string>();
    texts.forEach((text) => {
      if (!text) return;
      for (const match of text.matchAll(/\{\{\s*([A-Za-z0-9_]+)\s*\}\}/g)) {
        found.add(match[1]);
      }
    });
    return Array.from(found);
  };

  const computeVariables = (m: typeof metadata): string[] => {
    const texts: (string | undefined)[] = [m.description];
    Object.values(m.channels).forEach(ch => { texts.push(ch?.subject); texts.push(ch?.content); });
    m.sections.forEach(s => { if (typeof s.defaultContent === 'string') texts.push(s.defaultContent); });
    m.checklistItems.forEach(ci => { texts.push(ci.title); texts.push(ci.description); });
    return extractPlaceholders(...texts);
  };

  const handleSave = async () => {
    if (!metadata.name.trim()) {
      alert('Template name is required before saving.');
      return;
    }
    const payload = {
      ...metadata,
      name: metadata.name.trim(),
      // Defense in depth: strip any script-bearing markup before persisting.
      channels: Object.fromEntries(
        Object.entries(metadata.channels).map(([key, ch]) => [key, {
          ...ch,
          subject: DOMPurify.sanitize(ch?.subject || ''),
          content: DOMPurify.sanitize(ch?.content || ''),
        }])
      ),
      variables: computeVariables(metadata),
    };
    try {
      if (isNew) {
        await createTemplate.mutateAsync(payload);
      } else if (id) {
        await updateTemplate.mutateAsync({ id, payload });
      }
      navigate('/templates');
    } catch (err: any) {
      alert(`Save failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const applyAIAction = async (action: string, targetLanguage?: string) => {
    if (!editor) return;
    try {
      const result = await aiAction.mutateAsync({ action, content: editor.getHTML(), targetLanguage });
      editor.commands.setContent(result);
      handleChannelChange(activeChannel, 'content', result);
    } catch (err: any) {
      alert(`AI action failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleAIActionSelect = (action: string) => {
    if (!action) return;
    if (action === 'Translate') {
      setPendingTranslate(true);
    } else {
      applyAIAction(action);
    }
  };

  const handleTranslateLanguageSelect = (language: string) => {
    setPendingTranslate(false);
    if (language) applyAIAction('Translate', language);
  };

  const handleSubmitForApproval = async () => {
    if (!id) return;
    try {
      await submitForApproval.mutateAsync(id);
      setMetadata(prev => ({ ...prev, status: 'Pending Approval' }));
    } catch (err: any) {
      alert(`Submit failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleAddCategory = async () => {
    const name = newCategoryName.trim();
    if (!name || !masterData) return;
    try {
      await updateMasterData.mutateAsync({
        ...masterData.lists,
        categories: { items: [...masterData.lists.categories.items, { id: `md-${Date.now()}`, name, active: true, parentId: null }] },
      });
      setMetadata(prev => ({ ...prev, category: name }));
      setNewCategoryName('');
      setShowAddCategory(false);
    } catch (err: any) {
      alert(`Couldn't add category: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const filteredVariables = variableSearch.trim()
    ? variables?.filter(v => v.name.toLowerCase().includes(variableSearch.toLowerCase()) || v.display_name.toLowerCase().includes(variableSearch.toLowerCase()))
    : variables;

  const groupedVariables = filteredVariables?.reduce<Record<string, Variable[]>>((acc, curr) => {
    (acc[curr.category] ||= []).push(curr);
    return acc;
  }, {}) || {};

  const activeChannelData = metadata.channels[activeChannel];

  return (
    <div className="editor-container">
      <div className="editor-main">
        {/* Header */}
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', minWidth: 0, flex: '1 1 auto' }}>
            <button className="btn btn-outline" style={{ padding: '8px', flexShrink: 0 }} onClick={() => navigate('/templates')} title="Back to templates" aria-label="Back to templates">
              <ArrowLeft size={18} />
            </button>
            <input
              type="text"
              data-testid="template-name-input"
              value={metadata.name}
              onChange={e => setMetadata({...metadata, name: e.target.value})}
              title="Click to rename this template"
              aria-label="Template name"
              style={{ fontSize: '1.4rem', fontWeight: 'bold', background: 'transparent', border: 'none', borderBottom: '1px dashed transparent', color: 'var(--text-primary)', outline: 'none', padding: '2px 0', transition: 'border-color 0.15s ease', minWidth: 0, flex: '1 1 auto' }}
              onFocus={e => e.currentTarget.style.borderBottomColor = 'var(--accent-primary)'}
              onBlur={e => e.currentTarget.style.borderBottomColor = 'transparent'}
              onMouseEnter={e => { if (document.activeElement !== e.currentTarget) e.currentTarget.style.borderBottomColor = 'var(--border-color)'; }}
              onMouseLeave={e => { if (document.activeElement !== e.currentTarget) e.currentTarget.style.borderBottomColor = 'transparent'; }}
            />
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', flexShrink: 0 }}>
            {isCommBuilder && (
              <button className="btn btn-outline" onClick={() => alert('Testing Communication via ' + activeChannel)}>
                <Send size={16} /> Test Comm
              </button>
            )}
            {isEventBuilder && metadata.eventTrigger.autoGenerate && (
              <button className="btn btn-outline" onClick={generateNow} title={`Simulate the ${metadata.eventTrigger.eventType} trigger firing with sample employee data`}>
                <Zap size={16} /> Generate Now
              </button>
            )}
            <button className="btn btn-outline" onClick={() => setPreviewOpen(true)}>
              <Play size={16} /> Preview
            </button>
            {!isNew && metadata.approval_required && metadata.status === 'Draft' && (
              <button className="btn btn-outline" onClick={handleSubmitForApproval} disabled={submitForApproval.isPending}>
                <Send size={16} /> {submitForApproval.isPending ? 'Submitting...' : 'Submit for Approval'}
              </button>
            )}
            <button className="btn" onClick={handleSave} disabled={createTemplate.isPending || updateTemplate.isPending}>
              <Save size={16} /> {createTemplate.isPending || updateTemplate.isPending ? 'Saving...' : 'Save'}
            </button>
            <button className="icon-btn" style={{ border: '1px solid var(--border-color)' }} title={panelOpen ? 'Collapse panel' : 'Expand panel'} onClick={() => setPanelOpen(o => !o)}>
              {panelOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
            </button>
          </div>
        </div>

        {metadata.status === 'Pending Approval' && (
          <div style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent-primary)', color: 'var(--accent-primary)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '16px', fontSize: '0.9rem', fontWeight: 500 }}>
            ⏳ This template is submitted for approval — it will be published once a reviewer signs off.
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px', paddingLeft: '58px' }}>
          {isNew ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label htmlFor="template-category" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Category</label>
                {showAddCategory ? (
                  <>
                    <input
                      autoFocus
                      className="form-input"
                      style={{ width: 'auto', minWidth: '160px' }}
                      placeholder="New category name"
                      value={newCategoryName}
                      onChange={e => setNewCategoryName(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddCategory(); } if (e.key === 'Escape') { setShowAddCategory(false); setNewCategoryName(''); } }}
                    />
                    <button className="btn" style={{ padding: '6px 10px' }} disabled={updateMasterData.isPending} onClick={handleAddCategory}>Add</button>
                    <button className="btn btn-outline" style={{ padding: '6px 10px' }} onClick={() => { setShowAddCategory(false); setNewCategoryName(''); }}>Cancel</button>
                  </>
                ) : (
                  <select
                    className="form-input"
                    data-testid="template-category-select"
                    id="template-category"
                    style={{ width: 'auto', minWidth: '180px' }}
                    value={metadata.category}
                    onChange={e => { if (e.target.value === '__add_new__') setShowAddCategory(true); else setMetadata({ ...metadata, category: e.target.value }); }}
                  >
                    {activeCategories.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
                    {canManageMasterData && <option value="__add_new__">+ Add new category...</option>}
                  </select>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label htmlFor="template-language" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Language</label>
                <select id="template-language" className="form-input" data-testid="template-language-select" style={{ width: 'auto', minWidth: '140px' }} value={metadata.language} onChange={e => setMetadata({ ...metadata, language: e.target.value })}>
                  {activeLanguages.map(l => <option key={l.id} value={l.name}>{l.name}</option>)}
                </select>
              </div>
            </>
          ) : (
            <span style={{ fontSize: '0.82rem', color: 'var(--text-tertiary)' }}>{metadata.category} &middot; {metadata.language}</span>
          )}
        </div>

        {isChecklistBuilder ? (
          /* Checklist Template Builder Mode */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', flex: 1, paddingRight: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div>
                <h2 style={{ fontSize: '1.2rem', marginBottom: '4px' }}>Checklist Engine</h2>
                <p style={{ color: 'var(--text-secondary)' }}>Design the tasks, requirements, and evidence needed for this checklist.</p>
              </div>
              <button className="btn" onClick={addChecklistItem}><Plus size={16}/> Add Task</button>
            </div>
            
            {metadata.checklistItems.map((item, index) => (
              <div key={item.id} className="card" style={{ padding: '16px', display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                  <button className="btn btn-outline" style={{ padding: '4px' }} disabled={index === 0} onClick={() => moveChecklistItem(index, 'up')}><ArrowUp size={14}/></button>
                  <button className="btn btn-outline" style={{ padding: '4px' }} disabled={index === metadata.checklistItems.length - 1} onClick={() => moveChecklistItem(index, 'down')}><ArrowDown size={14}/></button>
                </div>
                
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <input type="text" className="form-input" style={{ flex: 2, fontSize: '1.05rem', fontWeight: 600 }} value={item.title} onChange={e => updateChecklistItem(item.id, 'title', e.target.value)} placeholder="Task Title" />
                    <select className="form-input" style={{ flex: 1 }} value={item.ownerRole} onChange={e => updateChecklistItem(item.id, 'ownerRole', e.target.value)}>
                      <option value="Any">Owner: Any Role</option>
                      <option value="Dev">Owner: Developer</option>
                      <option value="QA">Owner: QA</option>
                      <option value="Manager">Owner: Manager</option>
                      <option value="DevOps">Owner: DevOps</option>
                    </select>
                    <button className="btn btn-outline" style={{ padding: '8px', color: 'var(--danger)', borderColor: 'var(--danger)' }} onClick={() => removeChecklistItem(item.id)}><Trash2 size={16}/></button>
                  </div>
                  
                  <input type="text" className="form-input" value={item.description} onChange={e => updateChecklistItem(item.id, 'description', e.target.value)} placeholder="Detailed description of what needs to be checked..." />
                  
                  <div style={{ display: 'flex', gap: '24px', background: 'var(--bg-primary)', padding: '12px', borderRadius: '6px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem' }}>
                      <input type="checkbox" checked={item.mandatory} onChange={e => updateChecklistItem(item.id, 'mandatory', e.target.checked)} />
                      Is Mandatory?
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem' }}>
                      <input type="checkbox" checked={item.evidenceRequired} onChange={e => updateChecklistItem(item.id, 'evidenceRequired', e.target.checked)} />
                      Evidence Required (Upload)
                    </label>
                  </div>
                </div>
              </div>
            ))}
          </div>

        ) : isMeetingBuilder ? (
          /* Meeting Template Builder Mode */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', flex: 1, paddingRight: '12px' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Meeting Block Builder</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Arrange the structure of this meeting. When users create minutes from this template, they will fill out these blocks.
            </p>
            {metadata.sections.sort((a,b) => a.order - b.order).map((section, index) => (
              <div key={section.id} className="card" style={{ opacity: section.enabled ? 1 : 0.5, padding: '16px', display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                  <button className="btn btn-outline" style={{ padding: '4px' }} disabled={index === 0} onClick={() => moveSection(index, 'up')}><ArrowUp size={14}/></button>
                  <button className="btn btn-outline" style={{ padding: '4px' }} disabled={index === metadata.sections.length - 1} onClick={() => moveSection(index, 'down')}><ArrowDown size={14}/></button>
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{section.name}</h3>
                      <span style={{ fontSize: '0.75rem', padding: '2px 6px', background: 'var(--bg-primary)', borderRadius: '4px', color: 'var(--accent-primary)' }}>{section.type}</span>
                    </div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem' }}>
                      <input type="checkbox" checked={section.enabled} onChange={(e) => toggleSection(section.id, e.target.checked)} />
                      Enabled
                    </label>
                  </div>
                  
                  {section.enabled && (
                    <div style={{ background: 'var(--bg-primary)', padding: '12px', borderRadius: '6px' }}>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>Default Configuration</h4>
                      
                      {section.type === 'RichText' && (
                        <textarea style={{ width: '100%', height: '80px', background: 'var(--bg-surface)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '8px', borderRadius: '4px' }} defaultValue={section.defaultContent} readOnly />
                      )}
                      
                      {section.type === 'Table' && (
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          {(section.defaultContent as string[]).map(col => (
                            <span key={col} style={{ background: 'var(--bg-secondary)', padding: '4px 10px', borderRadius: '16px', fontSize: '0.85rem', border: '1px solid var(--border-color)' }}>{col}</span>
                          ))}
                        </div>
                      )}

                      {section.type === 'PeoplePicker' && (
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Columns: {(section.defaultContent as string[]).join(', ')}</div>
                      )}
                      
                      {['Date', 'FileUpload', 'Checklist'].includes(section.type) && (
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Standard {section.type} input block will be rendered.</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : isNoticeBuilder ? (
          /* Notice Board Builder Mode (Phase 6) */
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="notice-banner-main">Banner Image URL</label>
              <input
                id="notice-banner-main"
                type="text"
                className="form-input"
                placeholder="https://..."
                value={metadata.banner}
                onChange={(e) => setMetadata({ ...metadata, banner: e.target.value })}
              />
            </div>
            {metadata.banner && (
              <img src={metadata.banner} alt="Notice banner" style={{ width: '100%', maxHeight: '180px', objectFit: 'cover', borderRadius: 'var(--radius-md)', marginBottom: '16px', border: '1px solid var(--border-color)' }} />
            )}

            {editor && (
              <div className="editor-toolbar" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className={`btn btn-outline ${editor.isActive('bold') ? 'active' : ''}`} onClick={() => editor.chain().focus().toggleBold().run()} style={{ padding: '4px 8px' }}>B</button>
                  <button className={`btn btn-outline ${editor.isActive('italic') ? 'active' : ''}`} onClick={() => editor.chain().focus().toggleItalic().run()} style={{ padding: '4px 8px' }}>I</button>
                  <div style={{ width: '1px', backgroundColor: 'var(--border-color)', margin: '2px 4px' }} />
                  <button className="btn btn-outline" style={{ padding: '4px 8px' }} onClick={() => editor.chain().focus().undo().run()} title="Undo"><Undo2 size={14} /></button>
                  <button className="btn btn-outline" style={{ padding: '4px 8px' }} onClick={() => editor.chain().focus().redo().run()} title="Redo"><Redo2 size={14} /></button>
                </div>
                <div style={{ position: 'relative', display: 'flex', gap: '6px' }}>
                  {pendingTranslate && (
                    <select
                      autoFocus
                      className="form-input"
                      style={{ padding: '4px 8px', height: '32px' }}
                      disabled={aiAction.isPending}
                      onChange={(e) => handleTranslateLanguageSelect(e.target.value)}
                    >
                      <option value="">Translate to...</option>
                      {activeLanguages.filter(l => l.name !== metadata.language).map(l => <option key={l.id} value={l.name}>{l.name}</option>)}
                    </select>
                  )}
                  <select
                    className="form-input"
                    style={{ padding: '4px 8px', height: '32px' }}
                    disabled={aiAction.isPending}
                    onChange={(e) => { const action = e.target.value; e.target.value = ''; handleAIActionSelect(action); }}
                  >
                    <option value="">{aiAction.isPending ? 'Applying...' : '✨ AI Actions'}</option>
                    {AI_ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
                  </select>
                </div>
              </div>
            )}
            <div style={{ flex: 1, overflowY: 'auto' }}>
              <EditorContent editor={editor} />
            </div>
          </div>
        ) : (
          /* Communication Builder Mode (Phase 1) */
          <>
            <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid var(--border-color)', marginBottom: '16px' }}>
              {['email', 'whatsapp', 'sms'].map(ch => (
                <button 
                  key={ch} onClick={() => switchChannel(ch)}
                  style={{ 
                    padding: '10px 24px', background: activeChannel === ch ? 'var(--bg-hover)' : 'transparent', 
                    border: 'none', borderBottom: activeChannel === ch ? '2px solid var(--accent-primary)' : '2px solid transparent',
                    color: activeChannel === ch ? 'var(--text-primary)' : 'var(--text-secondary)',
                    cursor: 'pointer', fontWeight: 500, textTransform: 'capitalize'
                  }}
                >
                  {ch} {metadata.channels[ch]?.enabled && <CheckCircle2 size={12} color="var(--success)" style={{ marginLeft: '4px' }}/>}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
               <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                 <input type="checkbox" checked={activeChannelData?.enabled || false} onChange={(e) => handleChannelChange(activeChannel, 'enabled', e.target.checked)} />
                 Enable {activeChannel} Channel
               </label>
            </div>

            {activeChannelData?.enabled ? (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                {activeChannel === 'email' && (
                  <div className="form-group">
                    <input type="text" className="form-input" placeholder="Subject Line" aria-label="Email subject" value={activeChannelData.subject || ''} onChange={(e) => handleChannelChange(activeChannel, 'subject', e.target.value)} style={{ fontSize: '1.1rem', padding: '12px 16px' }} />
                  </div>
                )}
                {editor && (
                  <div className="editor-toolbar" style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button className={`btn btn-outline ${editor.isActive('bold') ? 'active' : ''}`} onClick={() => editor.chain().focus().toggleBold().run()} style={{ padding: '4px 8px' }} disabled={activeChannel !== 'email'}>B</button>
                      <button className={`btn btn-outline ${editor.isActive('italic') ? 'active' : ''}`} onClick={() => editor.chain().focus().toggleItalic().run()} style={{ padding: '4px 8px' }} disabled={activeChannel !== 'email'}>I</button>
                      <div style={{ width: '1px', backgroundColor: 'var(--border-color)', margin: '2px 4px' }} />
                      <button className="btn btn-outline" style={{ padding: '4px 8px' }} onClick={() => editor.chain().focus().undo().run()} disabled={activeChannel !== 'email'} title="Undo"><Undo2 size={14} /></button>
                      <button className="btn btn-outline" style={{ padding: '4px 8px' }} onClick={() => editor.chain().focus().redo().run()} disabled={activeChannel !== 'email'} title="Redo"><Redo2 size={14} /></button>
                    </div>
                    <div style={{ position: 'relative', display: 'flex', gap: '6px' }}>
                      {pendingTranslate && (
                        <select
                          autoFocus
                          className="form-input"
                          style={{ padding: '4px 8px', height: '32px' }}
                          disabled={aiAction.isPending}
                          onChange={(e) => handleTranslateLanguageSelect(e.target.value)}
                        >
                          <option value="">Translate to...</option>
                          {activeLanguages.filter(l => l.name !== metadata.language).map(l => <option key={l.id} value={l.name}>{l.name}</option>)}
                        </select>
                      )}
                      <select
                        className="form-input"
                        style={{ padding: '4px 8px', height: '32px' }}
                        disabled={aiAction.isPending}
                        onChange={(e) => { const action = e.target.value; e.target.value = ''; handleAIActionSelect(action); }}
                      >
                        <option value="">{aiAction.isPending ? 'Applying...' : '✨ AI Actions'}</option>
                        {AI_ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
                      </select>
                    </div>
                  </div>
                )}
                <div style={{ flex: 1, overflowY: 'auto' }}>
                  <EditorContent editor={editor} />
                  {activeChannel === 'sms' && <div style={{ textAlign: 'right', fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '8px' }}>SMS Character limit applies.</div>}
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>This channel is disabled. Enable it to edit content.</div>
            )}
          </>
        )}
      </div>

      {/* Sidebar */}
      {panelOpen && (
      <div className="editor-sidebar" style={{ width: '360px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Settings2 size={20} color="var(--accent-primary)" />
          <h2 style={{ margin: 0, fontSize: '1.1rem' }}>Configuration</h2>
        </div>

        <Accordion title="Details & Metadata" icon={<Info size={15} color="var(--accent-primary)" />} defaultOpen>
          <div className="form-group">
            <label className="form-label" htmlFor="template-description">Description</label>
            <textarea
              id="template-description"
              className="form-input"
              rows={2}
              placeholder="What does this template contain?"
              value={metadata.description}
              onChange={e => setMetadata({ ...metadata, description: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="template-purpose">Purpose</label>
            <textarea
              id="template-purpose"
              className="form-input"
              rows={2}
              placeholder="What is this template used for?"
              value={metadata.purpose}
              onChange={e => setMetadata({ ...metadata, purpose: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="template-department">Department</label>
            <select id="template-department" className="form-input" value={metadata.department} onChange={e => setMetadata({ ...metadata, department: e.target.value })}>
              {activeDepartments.map(d => <option key={d.id} value={d.name}>{d.name}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="template-owner">Owner</label>
            <input id="template-owner" type="text" className="form-input" value={metadata.owner} onChange={e => setMetadata({ ...metadata, owner: e.target.value })} />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="template-status">Status</label>
            <select id="template-status" className="form-input" value={metadata.status} onChange={e => setMetadata({ ...metadata, status: e.target.value })}>
              <option value="Draft">Draft</option>
              <option value="Pending Approval">Pending Approval</option>
              <option value="Published">Active / Published</option>
              <option value="Archived">Archived</option>
            </select>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer', marginBottom: '10px' }}>
            <input type="checkbox" checked={metadata.approval_required} onChange={e => setMetadata({ ...metadata, approval_required: e.target.checked })} />
            Approval Required
          </label>

          {metadata.approval_required && (
            <div className="form-group">
              <label className="form-label" htmlFor="template-approved-by">Approved By</label>
              <input id="template-approved-by" type="text" className="form-input" placeholder="Name of approver" value={metadata.approved_by} onChange={e => setMetadata({ ...metadata, approved_by: e.target.value })} />
            </div>
          )}

          {!isNew && (
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '8px' }}>
              <div>Version <strong>{metadata.version}</strong></div>
              <div>Created by {metadata.created_by || '—'} · {metadata.created_at ? new Date(metadata.created_at).toLocaleDateString() : '—'}</div>
              <div>Last updated {metadata.updated_at ? new Date(metadata.updated_at).toLocaleDateString() : '—'}</div>
            </div>
          )}

          <h4 style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '16px', marginBottom: '8px' }}>Variables / Placeholders</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {metadata.variables.length > 0 ? metadata.variables.map(name => (
              <span key={name} className="chip" title="Auto-detected from template content">{`{{${name}}}`}</span>
            )) : (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>No placeholders detected yet — add {'{{VariableName}}'} tags to your content.</p>
            )}
          </div>
        </Accordion>

        {isEventBuilder && (
          <Accordion title="Auto-Generation Trigger" icon={<Zap size={15} color="var(--accent-primary)" />} defaultOpen>
            <div className="form-group">
              <label className="form-label" htmlFor="template-event-type">Triggering Event</label>
              <select id="template-event-type" className="form-input" value={metadata.eventTrigger.eventType} onChange={e => handleEventTriggerChange('eventType', e.target.value)}>
                {EVENT_TYPES.map(et => <option key={et} value={et}>{et}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '12px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={metadata.eventTrigger.autoGenerate} onChange={e => handleEventTriggerChange('autoGenerate', e.target.checked)} />
                Auto-generate from employee data
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: metadata.eventTrigger.autoGenerate ? 'pointer' : 'not-allowed', opacity: metadata.eventTrigger.autoGenerate ? 1 : 0.5 }}>
                <input type="checkbox" disabled={!metadata.eventTrigger.autoGenerate} checked={metadata.eventTrigger.autoPublish} onChange={e => handleEventTriggerChange('autoPublish', e.target.checked)} />
                Auto-publish without review
              </label>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="template-lead-time">Lead Time (days before event)</label>
              <input id="template-lead-time" type="number" min={0} className="form-input" value={metadata.eventTrigger.leadTimeDays} onChange={e => handleEventTriggerChange('leadTimeDays', Number(e.target.value))} />
            </div>

            {!metadata.eventTrigger.autoPublish && metadata.eventTrigger.autoGenerate && (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
                Content will be auto-generated and queued for manual review before publishing.
              </p>
            )}
          </Accordion>
        )}

        {isNoticeBuilder && (
          <Accordion title="Notice Details" icon={<Image size={15} color="var(--accent-primary)" />} defaultOpen>
            <div className="form-group">
              <label className="form-label" htmlFor="notice-banner-sidebar">Banner Image URL</label>
              <input id="notice-banner-sidebar" type="text" className="form-input" placeholder="https://..." value={metadata.banner} onChange={(e) => setMetadata({ ...metadata, banner: e.target.value })} />
            </div>

            <label className="form-label" htmlFor="notice-attachments" style={{ marginTop: '16px', display: 'block' }}>Attachments</label>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
              <input
                id="notice-attachments"
                type="text"
                className="form-input"
                placeholder="e.g. Policy.pdf"
                value={newAttachment}
                onChange={(e) => setNewAttachment(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addAttachment(); } }}
              />
              <button className="btn btn-outline" onClick={addAttachment}><Plus size={16} /></button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {metadata.allowed_attachments.map(name => (
                <div key={name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'var(--bg-hover)', borderRadius: 'var(--radius-sm)', padding: '6px 10px', fontSize: '0.85rem' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Paperclip size={13} /> {name}</span>
                  <button className="icon-btn" style={{ width: '24px', height: '24px' }} onClick={() => removeAttachment(name)}><X size={13} /></button>
                </div>
              ))}
              {metadata.allowed_attachments.length === 0 && (
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>No attachments added yet.</p>
              )}
            </div>
          </Accordion>
        )}

        {isChecklistBuilder ? (
          <Accordion title="Signoff Required" icon={<CheckCircle2 size={15} color="var(--accent-primary)" />} defaultOpen>
            <div className="form-group">
              <label className="form-label" htmlFor="template-signoff-role">Require digital signoff by:</label>
              <select id="template-signoff-role" className="form-input" value={metadata.signoffRole} onChange={e => setMetadata({...metadata, signoffRole: e.target.value})}>
                <option value="">None (Auto-complete)</option>
                <option value="Manager">Manager</option>
                <option value="Admin">Admin</option>
                <option value="QA Lead">QA Lead</option>
              </select>
            </div>
          </Accordion>
        ) : !isNoticeBuilder && (
          <Accordion title="Branding & Rendering" icon={<Layers size={15} color="var(--accent-primary)" />} defaultOpen>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
               {Object.entries(metadata.branding).map(([key, val]) => (
                 <label key={key} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer' }}>
                   <input type="checkbox" checked={val as boolean} onChange={(e) => handleBrandingChange(key as keyof BrandingConfig, e.target.checked)} />
                   {key.replace('Enabled', '').replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                 </label>
               ))}
            </div>
          </Accordion>
        )}

        <Accordion title="Publishing & Lifecycle" icon={<Megaphone size={15} color="var(--accent-primary)" />}>
          <div className="form-group">
            <label className="form-label">Priority</label>
            <select className="form-input" value={metadata.publishing.priority} onChange={e => handlePriorityChange(e.target.value)}>
              {priorityOptions.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
            </select>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer', marginBottom: '12px' }}>
            <input type="checkbox" checked={metadata.publishing.publishImmediately} onChange={e => handlePublishingChange('publishImmediately', e.target.checked)} />
            Publish Immediately
          </label>

          {(!metadata.publishing.publishImmediately || isNoticeBuilder) && (
            <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">{isNoticeBuilder ? 'Start Date' : 'Effective Date'}</label>
                <input type="date" className="form-input" value={metadata.publishing.effectiveDate} onChange={e => handlePublishingChange('effectiveDate', e.target.value)} />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">{isNoticeBuilder ? 'End Date' : 'Expiry Date'}</label>
                <input type="date" className="form-input" value={metadata.publishing.expiryDate} onChange={e => handlePublishingChange('expiryDate', e.target.value)} />
              </div>
            </div>
          )}

          <h4 style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '16px', marginBottom: '8px' }}>Audience</h4>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer', marginBottom: '10px' }}>
            <input type="checkbox" checked={metadata.publishing.audience.allEmployees} onChange={e => handleAudienceChange('allEmployees', e.target.checked)} />
            All Employees
          </label>

          {!metadata.publishing.audience.allEmployees && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '12px' }}>
              {([
                { field: 'departments' as const, label: 'Departments', options: activeDepartments.map(d => d.name) },
                { field: 'locations' as const, label: 'Locations', options: LOCATIONS },
                { field: 'roles' as const, label: 'Roles', options: ROLES },
              ]).map(({ field, label, options }) => (
                <div key={field}>
                  <label className="form-label" style={{ display: 'block', marginBottom: '6px' }}>{label}</label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {options.map(opt => {
                      const selected = metadata.publishing.audience[field].includes(opt);
                      return (
                        <button
                          key={opt}
                          type="button"
                          className="btn btn-outline"
                          style={{
                            padding: '4px 10px', fontSize: '0.8rem', borderRadius: '16px',
                            backgroundColor: selected ? 'var(--accent-primary)' : 'var(--bg-surface)',
                            color: selected ? 'white' : 'var(--text-primary)',
                            borderColor: selected ? 'var(--accent-primary)' : 'var(--border-color)'
                          }}
                          onClick={() => toggleAudienceListItem(field, opt)}
                        >
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          <h4 style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '16px', marginBottom: '8px' }}>Notification Behavior</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={metadata.publishing.notificationBehavior.requireAcknowledgement} onChange={e => handleNotificationBehaviorChange('requireAcknowledgement', e.target.checked)} />
              Require Acknowledgement
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={metadata.publishing.notificationBehavior.allowComments} onChange={e => handleNotificationBehaviorChange('allowComments', e.target.checked)} />
              Allow Comments
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={metadata.publishing.notificationBehavior.pinToNoticeBoard} onChange={e => handleNotificationBehaviorChange('pinToNoticeBoard', e.target.checked)} />
              Pin to Notice Board
            </label>
          </div>
        </Accordion>

        {isCommBuilder && (
          <Accordion title="Variables" icon={<Users size={15} color="var(--accent-primary)" />} defaultOpen>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: 'var(--bg-hover)', borderRadius: 'var(--radius-sm)', padding: '8px 10px', marginBottom: '14px' }}>
              <Search size={14} color="var(--text-tertiary)" />
              <input
                type="text"
                placeholder="Search variables..."
                value={variableSearch}
                onChange={(e) => setVariableSearch(e.target.value)}
                style={{ background: 'transparent', border: 'none', outline: 'none', width: '100%', fontSize: '0.85rem', color: 'var(--text-primary)' }}
              />
            </div>
            {Object.entries(groupedVariables).map(([category, vars]) => (
              <div key={category} style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '8px' }}>{category}</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {vars.map(v => (
                    <button key={v.id} className="chip" onClick={() => insertVariable(v.name)} title={v.description}>
                      {`{{${v.name}}}`}
                      {v.required && <span style={{ color: 'var(--danger)', marginLeft: '2px' }}>*</span>}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            {Object.keys(groupedVariables).length === 0 && (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>No variables match "{variableSearch}".</p>
            )}
          </Accordion>
        )}
      </div>
      )}

      {/* Preview Modal */}
      {previewOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15,23,42,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
           <div className="card" style={{ width: previewWidth === 'a4' ? '794px' : '800px', maxHeight: '90vh', overflowY: 'auto', transition: 'width 0.2s ease' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                 <h2 style={{ marginBottom: 0 }}>Sample-Filled Preview</h2>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                   {isCommBuilder && (
                     <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--bg-hover)', borderRadius: 'var(--radius-sm)', padding: '3px' }}>
                       {['email', 'whatsapp', 'sms'].filter(ch => metadata.channels[ch]?.enabled).map(ch => (
                         <button
                           key={ch}
                           onClick={() => switchChannel(ch)}
                           style={{
                             padding: '6px 12px', borderRadius: 'var(--radius-sm)', border: 'none', fontSize: '0.8rem', fontWeight: 500, textTransform: 'capitalize', cursor: 'pointer',
                             backgroundColor: activeChannel === ch ? 'var(--bg-surface)' : 'transparent',
                             color: activeChannel === ch ? 'var(--text-primary)' : 'var(--text-secondary)',
                             boxShadow: activeChannel === ch ? 'var(--shadow-sm)' : 'none'
                           }}
                         >
                           {ch}
                         </button>
                       ))}
                     </div>
                   )}
                   {(isMeetingBuilder || isChecklistBuilder) && (
                     <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--bg-hover)', borderRadius: 'var(--radius-sm)', padding: '3px' }}>
                       {(['desktop', 'a4'] as const).map(w => (
                         <button
                           key={w}
                           onClick={() => setPreviewWidth(w)}
                           style={{
                             padding: '6px 12px', borderRadius: 'var(--radius-sm)', border: 'none', fontSize: '0.8rem', fontWeight: 500, textTransform: 'capitalize', cursor: 'pointer',
                             backgroundColor: previewWidth === w ? 'var(--bg-surface)' : 'transparent',
                             color: previewWidth === w ? 'var(--text-primary)' : 'var(--text-secondary)',
                             boxShadow: previewWidth === w ? 'var(--shadow-sm)' : 'none'
                           }}
                         >
                           {w === 'a4' ? 'A4 Document' : 'Desktop'}
                         </button>
                       ))}
                     </div>
                   )}
                   <button className="btn btn-outline" onClick={() => { setPreviewOpen(false); setMockChecklistState({}); }}>Close</button>
                 </div>
              </div>

              <div style={{ padding: '32px', backgroundColor: 'white', color: 'black', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                 {/* ... Branding Logo ... */}
                 {!isChecklistBuilder && metadata.branding.logoEnabled && <img src="/pixous_logo.png" alt="Pixous Technologies" style={{ height: '46px', marginBottom: '24px' }} />}

                 {isNoticeBuilder && metadata.banner && (
                   <img src={metadata.banner} alt="Notice banner" style={{ width: '100%', maxHeight: '220px', objectFit: 'cover', borderRadius: '8px', marginBottom: '24px' }} />
                 )}
                 {isNoticeBuilder && (
                   <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', marginBottom: '16px' }}>
                     <span style={{ padding: '3px 10px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, backgroundColor: '#eff6ff', color: '#2563eb' }}>{metadata.category}</span>
                     <span style={{ padding: '3px 10px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, backgroundColor: '#fef2f2', color: '#dc2626' }}>{metadata.publishing.priority} Priority</span>
                   </div>
                 )}

                 <h1 style={{ textAlign: 'center', color: '#111', marginBottom: '32px' }}>{metadata.name}</h1>

                 {isChecklistBuilder ? (
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                     {/* Progress Bar */}
                     {(() => {
                       const total = metadata.checklistItems.length;
                       const completed = Object.values(mockChecklistState).filter(s => s === 'Completed' || s === 'Skipped').length;
                       const pct = total === 0 ? 0 : Math.round((completed / total) * 100);
                       return (
                         <div style={{ marginBottom: '16px' }}>
                           <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', color: '#555' }}>
                             <span>Checklist Progress</span>
                             <span>{pct}% Completed</span>
                           </div>
                           <div style={{ width: '100%', height: '12px', background: '#e2e8f0', borderRadius: '6px', overflow: 'hidden' }}>
                             <div style={{ width: `${pct}%`, height: '100%', background: pct === 100 ? '#10b981' : '#3b82f6', transition: 'width 0.3s ease' }}></div>
                           </div>
                         </div>
                       );
                     })()}

                     {metadata.checklistItems.map(item => {
                       const state = mockChecklistState[item.id] || 'Pending';
                       const isCompleted = state === 'Completed';
                       
                       return (
                         <div key={item.id} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', background: isCompleted ? '#f0fdf4' : '#fff' }}>
                           <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                             <div>
                               <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                 <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#1e293b' }}>{item.title}</h3>
                                 {item.mandatory && <span style={{ color: '#ef4444', fontWeight: 'bold' }}>*</span>}
                                 <span style={{ fontSize: '0.75rem', padding: '2px 6px', background: '#f1f5f9', color: '#64748b', borderRadius: '4px' }}>{item.ownerRole}</span>
                               </div>
                               <p style={{ margin: 0, fontSize: '0.9rem', color: '#64748b' }}>{item.description}</p>
                             </div>
                             
                             <select 
                               style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #cbd5e1', background: 'white', fontWeight: 500, color: isCompleted ? '#16a34a' : '#475569' }}
                               value={state}
                               onChange={(e) => setMockChecklistState(prev => ({ ...prev, [item.id]: e.target.value }))}
                             >
                               <option value="Pending">Pending</option>
                               <option value="Completed">Completed</option>
                               <option value="Skipped">Skipped</option>
                               <option value="Rejected">Rejected</option>
                             </select>
                           </div>

                           <div style={{ display: 'flex', gap: '16px', marginTop: '16px', borderTop: '1px solid #e2e8f0', paddingTop: '16px' }}>
                             <div style={{ flex: 1 }}>
                               <label style={{ display: 'block', fontSize: '0.8rem', color: '#64748b', marginBottom: '4px' }}>Remarks (Optional)</label>
                               <input type="text" style={{ width: '100%', padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px' }} placeholder="Add a note..." />
                             </div>
                             {item.evidenceRequired && (
                               <div style={{ flex: 1 }}>
                                 <label style={{ display: 'block', fontSize: '0.8rem', color: '#ef4444', marginBottom: '4px', fontWeight: 500 }}>Evidence Required *</label>
                                 <button style={{ width: '100%', padding: '8px', border: '1px dashed #cbd5e1', background: '#f8fafc', borderRadius: '4px', color: '#64748b', cursor: 'pointer' }}>📎 Upload File / Image</button>
                               </div>
                             )}
                           </div>
                         </div>
                       );
                     })}

                     {metadata.signoffRole && (
                       <div style={{ marginTop: '24px', padding: '16px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', textAlign: 'center' }}>
                         <p style={{ color: '#475569', fontSize: '0.9rem', marginBottom: '8px' }}>This checklist requires digital signoff by: <strong>{metadata.signoffRole}</strong></p>
                         <button style={{ padding: '8px 24px', background: '#10b981', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 500, cursor: 'not-allowed', opacity: 0.5 }}>Digitally Sign & Approve</button>
                       </div>
                     )}
                   </div>
                 ) : isMeetingBuilder ? (
                   /* Meeting Blocks Preview */
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                     {metadata.sections.filter(s => s.enabled).sort((a,b) => a.order - b.order).map(section => (
                       <div key={section.id}>
                         <h3 style={{ borderBottom: '2px solid #eee', paddingBottom: '8px', marginBottom: '16px', color: '#222' }}>{section.name}</h3>
                         
                         {section.type === 'PeoplePicker' && (
                           <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                             <thead><tr style={{ background: '#f8f9fa' }}>{(section.defaultContent as string[]).map(c => <th key={c} style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>{c}</th>)}</tr></thead>
                             <tbody>
                               <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>John Doe</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Client</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>ABC Ltd</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Present</td></tr>
                             </tbody>
                           </table>
                         )}
                         {section.type === 'RichText' && (
                           <div style={{ color: '#444', lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: typeof section.defaultContent === 'string' ? DOMPurify.sanitize(section.defaultContent) : '<p><i>Meeting notes go here...</i></p>' }} />
                         )}
                         {section.type === 'Table' && (
                           <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                             <thead><tr style={{ background: '#f8f9fa' }}>{(section.defaultContent as string[]).map(c => <th key={c} style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>{c}</th>)}</tr></thead>
                             <tbody>
                               <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Setup CI/CD</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Pradeep</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>High</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Aug 15</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Pending</td></tr>
                             </tbody>
                           </table>
                         )}
                         {section.type === 'Date' && (
                           <div style={{ color: '#444' }}><strong>Scheduled for:</strong> Aug 20, 2026 at 10:00 AM</div>
                         )}
                         {section.type === 'FileUpload' && (
                           <div style={{ padding: '16px', background: '#f8f9fa', border: '1px dashed #ccc', color: '#666', textAlign: 'center' }}>📎 Attachments (e.g. Architecture.pdf)</div>
                         )}
                       </div>
                     ))}
                   </div>
                 ) : (
                   /* Comm Channels Preview */
                   <div>
                     {isEventBuilder && metadata.eventTrigger.autoGenerate && (
                       <div style={{ marginBottom: '16px', padding: '8px 12px', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', color: '#1e40af', fontSize: '0.85rem' }}>
                         ⚡ Auto-generated for the "{metadata.eventTrigger.eventType}" event using sample employee data.
                       </div>
                     )}
                     {activeChannel === 'email' && <div style={{ marginBottom: '16px', fontWeight: 'bold', fontSize: '1.1rem', color: '#333' }}>Subject: {substituteVariables(activeChannelData.subject || '')}</div>}
                     <div dangerouslySetInnerHTML={{ __html: substituteVariables(activeChannelData.content) || '<i>No content</i>' }} style={{ color: '#444', lineHeight: 1.6 }} />

                     {isNoticeBuilder && metadata.allowed_attachments.length > 0 && (
                       <div style={{ marginTop: '24px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                         {metadata.allowed_attachments.map(name => (
                           <span key={name} style={{ fontSize: '0.8rem', padding: '4px 10px', borderRadius: '6px', background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' }}>📎 {name}</span>
                         ))}
                       </div>
                     )}
                     {isNoticeBuilder && metadata.publishing.notificationBehavior.requireAcknowledgement && (
                       <div style={{ marginTop: '24px', padding: '12px 16px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px', color: '#92400e', fontSize: '0.85rem' }}>
                         This notice requires employee acknowledgement.
                       </div>
                     )}
                   </div>
                 )}
                 
                 {!isChecklistBuilder && metadata.branding.signatureEnabled && <div style={{ marginTop: '40px', borderTop: '1px solid #ccc', paddingTop: '16px', color: '#444' }}>John Doe<br/>Sales Executive</div>}
                 {!isChecklistBuilder && metadata.branding.footerEnabled && <div style={{ marginTop: '20px', fontSize: '0.8rem', color: '#888', textAlign: 'center' }}>© 2026 Pixous Technologies. All rights reserved.</div>}
              </div>
           </div>
        </div>
      )}
    </div>
  );
};

export default TemplateEditor;
