/**
 * Copy text to the clipboard, preferring the modern async Clipboard API when
 * available (secure contexts only) and falling back to the legacy
 * `document.execCommand('copy')` paths otherwise.
 *
 * Why: the site is currently served over plain HTTP, which is NOT a secure
 * context — `navigator.clipboard` is `undefined` there, so a naive
 * `navigator.clipboard.writeText()` silently fails. The legacy paths work on
 * insecure origins (and inside user gestures, like a click handler).
 *
 * When `html` is provided, formatting is preserved: the modern path writes a
 * text/html + text/plain pair, and the legacy path copies a real DOM selection
 * of the rendered HTML so the destination (Word, Google Docs, Outlook, Gmail)
 * receives the structure, spacing, headings and alignment of the original —
 * not a flattened wall of text.
 */
export async function copyText(plain: string, html?: string): Promise<boolean> {
  // Modern path — secure context only.
  if (window.isSecureContext && navigator.clipboard) {
    try {
      const ClipboardItemCtor = (window as any).ClipboardItem;
      if (html && ClipboardItemCtor) {
        await navigator.clipboard.write([
          new ClipboardItemCtor({
            'text/html': new Blob([html], { type: 'text/html' }),
            'text/plain': new Blob([plain], { type: 'text/plain' }),
          }),
        ]);
        return true;
      }
      await navigator.clipboard.writeText(plain);
      return true;
    } catch {
      // Fall through to the legacy paths (e.g. permission denied).
    }
  }

  // Legacy path 1 — rich HTML copy via a real DOM selection. Preserves
  // formatting even on plain HTTP. Must be in the DOM and laid out for the
  // selection to work (no display:none), so it is rendered off-screen.
  if (html) {
    try {
      if (legacyRichCopy(html)) return true;
    } catch {
      // Fall through to the plain-text path.
    }
  }

  // Legacy path 2 — plain text only (used for plain strings, e.g. passwords,
  // or when the rich path is unavailable).
  try {
    return legacyPlainCopy(plain);
  } catch {
    return false;
  }
}

function legacyRichCopy(html: string): boolean {
  const container = document.createElement('div');
  container.contentEditable = 'true';
  container.innerHTML = html;
  container.style.position = 'fixed';
  container.style.left = '-9999px';
  container.style.top = '0';
  container.style.width = '1024px';
  document.body.appendChild(container);

  const range = document.createRange();
  range.selectNodeContents(container);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);

  let ok = false;
  try {
    ok = document.execCommand('copy');
  } finally {
    selection?.removeAllRanges();
    document.body.removeChild(container);
  }
  return ok;
}

function legacyPlainCopy(plain: string): boolean {
  const textarea = document.createElement('textarea');
  textarea.value = plain;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.top = '-1000px';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } finally {
    document.body.removeChild(textarea);
  }
  return ok;
}
