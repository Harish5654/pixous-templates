/**
 * Copy text to the clipboard, preferring the modern async Clipboard API when
 * available (secure contexts only) and falling back to the legacy
 * `document.execCommand('copy')` path otherwise.
 *
 * Why: the site is currently served over plain HTTP, which is NOT a secure
 * context — `navigator.clipboard` is `undefined` there, so a naive
 * `navigator.clipboard.writeText()` silently fails. The legacy fallback works
 * on insecure origins (and inside user gestures, like a click handler).
 */
export async function copyText(plain: string, html?: string): Promise<boolean> {
  // Modern path — secure context only.
  try {
    const ClipboardItemCtor = (window as any).ClipboardItem;
    if (window.isSecureContext && navigator.clipboard) {
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
    }
  } catch {
    // Fall through to the legacy path (e.g. permission denied).
  }

  // Legacy path — works on plain HTTP and when the modern API is blocked.
  try {
    const textarea = document.createElement('textarea');
    textarea.value = plain;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.top = '-1000px';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(textarea);
    return ok;
  } catch {
    return false;
  }
}
