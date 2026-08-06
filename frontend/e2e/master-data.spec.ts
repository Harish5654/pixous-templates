import { test, expect } from '@playwright/test';

test.use({ storageState: '.auth/admin.json' });

test('add a category, save, and confirm it persists after reload', async ({ page }) => {
  const categoryName = `E2E Category ${Date.now()}`;

  await page.goto('/admin/master-data');
  await expect(page.getByRole('heading', { name: 'Master Data' })).toBeVisible();

  await page.locator('.md-add-row input').fill(categoryName);
  await page.locator('.md-add-row').getByRole('button', { name: /^add$/i }).click();

  const nameInput = page.locator('.md-row input.md-row-name').last();
  await expect(nameInput).toHaveValue(categoryName);

  await page.getByRole('button', { name: /save changes/i }).click();
  await expect(page.getByRole('button', { name: /^saved$/i })).toBeVisible();

  await page.reload();
  await expect(page.locator(`.md-row-name[value="${categoryName}"]`)).toHaveCount(1);

  // Deactivate rather than delete — Master Data has no hard-delete for taxonomy
  // entries by design, so leave this test entry disabled instead of live forever.
  // Click the visible switch (label wraps the input), not the covered input itself.
  const row = page.locator('.md-row').filter({ has: page.locator(`input[value="${categoryName}"]`) });
  await row.locator('.switch').click();
  await expect(row.locator('input[type="checkbox"]')).not.toBeChecked();
  await page.getByRole('button', { name: /save changes/i }).click();
  await expect(page.getByRole('button', { name: /^saved$/i })).toBeVisible();
});

test('a known seeded category appears in the Templates sidebar', async ({ page }) => {
  await page.goto('/templates');
  await expect(page.locator('li', { hasText: 'Business Documents' }).first()).toBeVisible();
});
