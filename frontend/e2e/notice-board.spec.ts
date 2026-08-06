import { test, expect } from '@playwright/test';

test.use({ storageState: '.auth/employee.json' });

test('acknowledge a notice and see it persist across reload', async ({ page }) => {
  await page.goto('/notice-board');
  await expect(page.getByRole('heading', { name: 'Notice Board' })).toBeVisible();

  const notice = page.locator('.template-card', { hasText: 'Phishing Awareness Alert' });
  await expect(notice).toBeVisible();

  await notice.getByRole('button', { name: /^acknowledge$/i }).click();
  await expect(notice.getByRole('button', { name: /^acknowledged$/i })).toBeVisible();

  await page.reload();
  const noticeAfterReload = page.locator('.template-card', { hasText: 'Phishing Awareness Alert' });
  await expect(noticeAfterReload.getByRole('button', { name: /^acknowledged$/i })).toBeVisible();
});
