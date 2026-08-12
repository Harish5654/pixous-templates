import { useMemo, useRef, useState } from 'react';
import { X, Copy, FileDown, FileText, Printer, Check } from 'lucide-react';
import { copyText } from '../utils/clipboard';
import DOMPurify from 'dompurify';
import type { Template, SectionData, ChecklistItem } from '../types/template';
import { useVariables } from '../api/queries';

interface FillAndGenerateModalProps {
  template: Template;
  onClose: () => void;
}

const VARIABLE_PATTERN = /\{\{\s*([A-Za-z0-9_]+)\s*\}\}/g;

const extractVariableNames = (...texts: (string | undefined)[]): string[] => {
  const found = new Set<string>();
  texts.forEach((text) => {
    if (!text) return;
    for (const match of text.matchAll(VARIABLE_PATTERN)) {
      found.add(match[1]);
    }
  });
  return Array.from(found);
};

const escapeHtml = (value: string): string =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const stripHtml = (html: string): string => {
  const div = document.createElement('div');
  div.innerHTML = html;
  return div.textContent || div.innerText || '';
};

const slugify = (name: string): string => name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

const LOGO_URL = `${window.location.origin}/pixous_logo.png`;

const LOGO_ASPECT_RATIO = 2550 / 1318;
const LOGO_HEIGHT_PX = 42;
const LOGO_WIDTH_PX = Math.round(LOGO_HEIGHT_PX * LOGO_ASPECT_RATIO);

const buildLetterheadHtml = (branding: Template['branding']): string => {
  if (!branding.logoEnabled && !branding.letterheadEnabled) return '';
  return `<div style="display:flex;align-items:center;justify-content:space-between;padding-bottom:14px;margin-bottom:20px;border-bottom:2px solid #173F5F;">
    ${branding.logoEnabled ? `<img src="${LOGO_URL}" alt="Pixous Technologies" width="${LOGO_WIDTH_PX}" height="${LOGO_HEIGHT_PX}" style="width:${LOGO_WIDTH_PX}px;height:${LOGO_HEIGHT_PX}px;" />` : '<span style="font-weight:700;color:#173F5F;font-size:1.05rem;">PIXOUS TECHNOLOGIES</span>'}
    ${branding.letterheadEnabled ? '<span style="font-size:0.72rem;color:#888;letter-spacing:0.06em;text-transform:uppercase;">Official Communication</span>' : ''}
  </div>`;
};

const buildCompanyDetailsHtml = (branding: Template['branding']): string => {
  if (!branding.companyDetailsEnabled) return '';
  return `<div style="font-size:0.78rem;color:#888;margin-bottom:20px;">Pixous Technologies &middot; pixoustech.com</div>`;
};

const buildSignatureHtml = (branding: Template['branding'], owner: string): string => {
  if (!branding.signatureEnabled) return '';
  return `<div style="margin-top:28px;">
    <p style="margin:0;">Regards,</p>
    <p style="margin:0;font-weight:700;">${escapeHtml(owner)}</p>
    <p style="margin:0;color:#888;">Pixous Technologies</p>
  </div>`;
};

const buildFooterHtml = (branding: Template['branding']): string => {
  if (!branding.footerEnabled) return '';
  return `<div style="margin-top:28px;padding-top:14px;border-top:1px solid #e2e2e2;font-size:0.72rem;color:#999;text-align:center;">
    This message was sent by Pixous Technologies &middot; pixoustech.com &middot; Confidential
  </div>`;
};

const buildTableHtml = (columns: string[]): string => `<table style="width:100%;border-collapse:collapse;margin-top:8px;">
  <tr>${columns.map((c) => `<th style="border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:0.85rem;background:#f7f7f7;">${escapeHtml(c)}</th>`).join('')}</tr>
  <tr>${columns.map(() => `<td style="border:1px solid #ddd;padding:14px 10px;">&nbsp;</td>`).join('')}</tr>
</table>`;

const buildSectionContentHtml = (section: SectionData): string => {
  if (section.type === 'Table' || section.type === 'PeoplePicker') {
    const columns = Array.isArray(section.defaultContent) ? section.defaultContent : [];
    return buildTableHtml(columns);
  }
  const content = typeof section.defaultContent === 'string' ? section.defaultContent : '';
  return content ? `<div>${DOMPurify.sanitize(content)}</div>` : '<p style="color:#999;font-style:italic;margin:0;">To be filled in during the meeting.</p>';
};

const buildSectionsHtml = (sections: SectionData[]): string => {
  const sorted = [...sections].filter((s) => s.enabled).sort((a, b) => a.order - b.order);
  return sorted.map((s) => `<div style="margin-bottom:22px;">
    <h3 style="font-size:1rem;margin:0 0 8px;color:#173F5F;">${escapeHtml(s.name)}${s.required ? ' <span style="color:#dc2626;font-size:0.78rem;">*</span>' : ''}</h3>
    ${buildSectionContentHtml(s)}
  </div>`).join('');
};

const buildChecklistHtml = (items: ChecklistItem[], checkedItems: Record<string, boolean>): string => `<ul style="list-style:none;padding:0;margin:0;">${items.map((item) => {
  const checked = !!checkedItems[item.id];
  return `
  <li style="padding:12px 0;border-bottom:1px solid #eee;">
    <div style="display:flex;align-items:baseline;gap:8px;">
      <span style="width:15px;height:15px;border:1.5px solid #173F5F;border-radius:3px;flex-shrink:0;display:inline-block;text-align:center;line-height:13px;font-size:11px;color:#173F5F;${checked ? 'background:#173F5F;color:#fff;' : ''}">${checked ? '&#10003;' : ''}</span>
      <strong style="${checked ? 'text-decoration:line-through;color:#888;' : ''}">${escapeHtml(item.title)}</strong>
      ${item.mandatory ? '<span style="font-size:0.72rem;color:#dc2626;">Mandatory</span>' : '<span style="font-size:0.72rem;color:#888;">Optional</span>'}
      ${item.evidenceRequired ? '<span style="font-size:0.72rem;color:#888;">&middot; Evidence required</span>' : ''}
    </div>
    ${item.description ? `<p style="margin:4px 0 0 23px;color:#555;font-size:0.9rem;">${escapeHtml(item.description)}</p>` : ''}
    <p style="margin:2px 0 0 23px;color:#999;font-size:0.78rem;">Owner: ${escapeHtml(item.ownerRole)}</p>
  </li>`;
}).join('')}</ul>`;

const FillAndGenerateModal = ({ template, onClose }: FillAndGenerateModalProps) => {
  const { data: variableDefs } = useVariables();
  const [values, setValues] = useState<Record<string, string>>({});
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [copyStatus, setCopyStatus] = useState<'idle' | 'done' | 'error'>('idle');
  const previewRef = useRef<HTMLDivElement>(null);

  const toggleChecklistItem = (id: string) => {
    setCheckedItems((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const enabledChannelKey = Object.keys(template.channels || {}).find((k) => template.channels[k]?.enabled);
  const channel = enabledChannelKey ? template.channels[enabledChannelKey] : null;

  const variableNames = useMemo(
    () => extractVariableNames(channel?.subject, channel?.content, template.description),
    [channel?.subject, channel?.content, template.description]
  );

  const variableMeta = useMemo(() => {
    const byName = new Map((variableDefs || []).map((v) => [v.name, v]));
    return variableNames.map((name) => ({
      name,
      def: byName.get(name),
    }));
  }, [variableNames, variableDefs]);

  const substitute = (text: string | undefined, forExport: boolean): string => {
    if (!text) return '';
    return text.replace(VARIABLE_PATTERN, (_match, name) => {
      const value = values[name]?.trim();
      if (value) return escapeHtml(value);
      if (forExport) return '';
      return `<span style="background:var(--accent-soft,#eaf1f6);color:var(--accent-primary,#173F5F);border-radius:3px;padding:0 3px;">{{${name}}}</span>`;
    });
  };

  // Template content is admin-authored HTML. Sanitize it before rendering so a
  // template containing scripts/event handlers can never execute in a viewer's
  // session (stored XSS). Variables are substituted afterward with escaped values.
  const sanitizedSubject = DOMPurify.sanitize(channel?.subject || '');
  const sanitizedContent = DOMPurify.sanitize(channel?.content || '');
  const previewSubject = substitute(sanitizedSubject, false);
  const previewContent = substitute(sanitizedContent, false) || '<i>No content in this channel.</i>';
  const exportContent = substitute(sanitizedContent, true);
  const exportSubject = substitute(sanitizedSubject, true);

  const hasChecklist = !channel && (template.checklistItems?.length || 0) > 0;
  const hasSections = !channel && !hasChecklist && (template.sections?.length || 0) > 0;
  const hasStructuredContent = hasChecklist || hasSections;
  const structuredContentHtml = hasChecklist
    ? buildChecklistHtml(template.checklistItems, checkedItems)
    : hasSections
      ? buildSectionsHtml(template.sections)
      : '';
  const checkedCount = hasChecklist ? template.checklistItems.filter((i) => checkedItems[i.id]).length : 0;

  const filledCount = variableMeta.filter((v) => values[v.name]?.trim()).length;

  const handleValueChange = (name: string, value: string) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const buildExportHtml = () => {
    const body = channel
      ? `${exportSubject ? `<h2 style="margin:0 0 16px;">${exportSubject}</h2>` : ''}<div>${exportContent}</div>`
      : hasStructuredContent
        ? structuredContentHtml
        : `<p>${escapeHtml(template.description || '')}</p>`;
    return `${buildLetterheadHtml(template.branding)}${buildCompanyDetailsHtml(template.branding)}${body}${buildSignatureHtml(template.branding, template.owner)}${buildFooterHtml(template.branding)}`;
  };

  const handleCopy = async () => {
    const html = buildExportHtml();
    const plain = stripHtml(html);
    const ok = await copyText(plain, html);
    setCopyStatus(ok ? 'done' : 'error');
    setTimeout(() => setCopyStatus('idle'), 2000);
  };

  const handlePrint = () => {
    const win = window.open('', '_blank');
    if (!win) return;
    win.document.write(`<!DOCTYPE html><html><head><title>${template.name}</title>
      <style>body{font-family:Arial,sans-serif;padding:32px;color:#111;line-height:1.6;}</style>
      </head><body>${buildExportHtml()}</body></html>`);
    win.document.close();
    win.focus();
    win.onload = () => { win.print(); };
    setTimeout(() => win.print(), 300);
  };

  const handleDownloadDoc = () => {
    const html = `<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
      <head><meta charset="utf-8"><title>${template.name}</title></head>
      <body style="font-family:Calibri,Arial,sans-serif;">${buildExportHtml()}</body></html>`;
    const blob = new Blob(['﻿', html], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${slugify(template.name)}.doc`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadPdf = async () => {
    const node = previewRef.current;
    if (!node) return;
    const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf'),
    ]);
    const canvas = await html2canvas(node, { scale: 2, backgroundColor: '#ffffff' });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({ unit: 'pt', format: 'a4' });
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const imgWidth = pageWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    let heightLeft = imgHeight;
    let position = 0;
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;
    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }
    pdf.save(`${slugify(template.name)}.pdf`);
  };

  return (
    <div
      style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15,23,42,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200, padding: '24px' }}
      onClick={onClose}
    >
      <div className="card" style={{ width: '960px', maxWidth: '100%', maxHeight: '88vh', display: 'flex', flexDirection: 'column' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', flexShrink: 0 }}>
          <div>
            <h2 style={{ marginBottom: '6px' }}>{template.name}</h2>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className="badge badge-neutral">{template.category}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Owned by {template.owner}</span>
              {variableMeta.length > 0 && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>· {filledCount}/{variableMeta.length} values filled</span>
              )}
              {hasChecklist && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>· {checkedCount}/{template.checklistItems.length} checked off</span>
              )}
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-tertiary)', marginTop: '8px', marginBottom: 0 }}>
              {variableMeta.length > 0
                ? 'Fill in the values on the left — the preview on the right updates as you type.'
                : hasChecklist
                  ? 'Check items off in the preview as you complete them, then export.'
                  : 'This template has no fillable values. Use the actions below to copy or download it.'}
            </p>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div style={{ display: 'flex', gap: '20px', flex: 1, minHeight: 0, overflow: 'hidden' }}>
          {/* Fill Values pane */}
          <div style={{ width: '300px', flexShrink: 0, overflowY: 'auto', paddingRight: '4px' }}>
            <h3 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              Fill Values
            </h3>
            {hasChecklist ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {template.checklistItems.map((item) => {
                  const checked = !!checkedItems[item.id];
                  return (
                    <label key={item.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', padding: '8px 4px', cursor: 'pointer', borderBottom: '1px solid var(--border-color)' }}>
                      <input type="checkbox" checked={checked} onChange={() => toggleChecklistItem(item.id)} style={{ marginTop: '3px', flexShrink: 0 }} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: '0.88rem', fontWeight: 500, color: checked ? 'var(--text-tertiary)' : 'var(--text-primary)', textDecoration: checked ? 'line-through' : 'none' }}>
                          {item.title}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: item.mandatory ? 'var(--danger)' : 'var(--text-tertiary)' }}>
                          {item.mandatory ? 'Mandatory' : 'Optional'}{item.evidenceRequired ? ' · Evidence required' : ''}
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            ) : variableMeta.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>This template has no variables to fill in.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {variableMeta.map(({ name, def }) => (
                  <div className="form-group" key={name} style={{ marginBottom: 0 }}>
                    <label className="form-label">{def?.display_name || name}</label>
                    <input
                      className="form-input"
                      type={def?.type === 'Date' ? 'date' : def?.type === 'Number' ? 'number' : 'text'}
                      placeholder={def?.default_value || `Enter ${def?.display_name || name}`}
                      value={values[name] || ''}
                      onChange={(e) => handleValueChange(name, e.target.value)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Preview pane */}
          <div style={{ flex: 1, minWidth: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              Preview
            </h3>
            <div ref={previewRef} style={{ padding: '28px', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', color: '#111', flex: 1 }}>
              {channel ? (
                <>
                  <div dangerouslySetInnerHTML={{ __html: buildLetterheadHtml(template.branding) }} />
                  <div dangerouslySetInnerHTML={{ __html: buildCompanyDetailsHtml(template.branding) }} />
                  {enabledChannelKey === 'email' && previewSubject && (
                    <div style={{ fontWeight: 700, marginBottom: '12px', color: '#333' }} dangerouslySetInnerHTML={{ __html: `Subject: ${previewSubject}` }} />
                  )}
                  <div dangerouslySetInnerHTML={{ __html: previewContent }} style={{ lineHeight: 1.6 }} />
                  <div dangerouslySetInnerHTML={{ __html: buildSignatureHtml(template.branding, template.owner) }} />
                  <div dangerouslySetInnerHTML={{ __html: buildFooterHtml(template.branding) }} />
                </>
              ) : hasStructuredContent ? (
                <>
                  <div dangerouslySetInnerHTML={{ __html: buildLetterheadHtml(template.branding) }} />
                  <div dangerouslySetInnerHTML={{ __html: buildCompanyDetailsHtml(template.branding) }} />
                  <div dangerouslySetInnerHTML={{ __html: structuredContentHtml }} />
                  <div dangerouslySetInnerHTML={{ __html: buildSignatureHtml(template.branding, template.owner) }} />
                  <div dangerouslySetInnerHTML={{ __html: buildFooterHtml(template.branding) }} />
                </>
              ) : (
                <p style={{ color: '#555' }}>{template.description || 'No preview available for this template type.'}</p>
              )}
            </div>
          </div>
        </div>

        {(channel || hasStructuredContent) && (
          <div style={{ display: 'flex', gap: '10px', marginTop: '18px', paddingTop: '16px', borderTop: '1px solid var(--border-color)', flexShrink: 0 }}>
            <button className="btn btn-outline" onClick={handleCopy}>
              {copyStatus === 'done' ? <Check size={16} /> : <Copy size={16} />}
              {copyStatus === 'done' ? 'Copied' : copyStatus === 'error' ? 'Copy failed' : 'Copy'}
            </button>
            <button className="btn btn-outline" onClick={handleDownloadPdf}>
              <FileDown size={16} /> Download PDF
            </button>
            <button className="btn btn-outline" onClick={handleDownloadDoc}>
              <FileText size={16} /> Download Word
            </button>
            <button className="btn btn-outline" onClick={handlePrint}>
              <Printer size={16} /> Print
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FillAndGenerateModal;
