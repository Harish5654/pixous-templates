import { test, expect } from '@playwright/test';

test.describe('RBAC — Employee', () => {
  test.use({ storageState: '.auth/employee.json' });

  test('does not see authoring controls', async ({ page }) => {
    await page.goto('/templates');
    await expect(page.getByRole('button', { name: /manage/i })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /new template/i })).toHaveCount(0);
    await expect(page.getByRole('link', { name: /master data/i })).toHaveCount(0);
  });

  test('cannot reach the editor by direct URL', async ({ page }) => {
    await page.goto('/templates/new');
    await page.waitForURL('**/templates');
  });

  test('cannot reach Master Data by direct URL', async ({ page }) => {
    await page.goto('/admin/master-data');
    await page.waitForURL('**/templates');
  });

  test('sees Fill & Generate on every template card', async ({ page }) => {
    await page.goto('/templates');
    await expect(page.getByRole('button', { name: /fill & generate/i }).first()).toBeVisible();
  });
});

test.describe('RBAC — Admin', () => {
  test.use({ storageState: '.auth/admin.json' });

  test('sees authoring controls and Master Data nav', async ({ page }) => {
    await page.goto('/templates');
    await expect(page.getByRole('link', { name: /master data/i })).toBeVisible();
    await page.getByRole('button', { name: /^manage$/i }).click();
    await expect(page.getByRole('button', { name: /new template/i })).toBeVisible();
  });
});

test.describe('RBAC — Editor cannot write Master Data', () => {
  test.use({ storageState: '.auth/editor.json' });

  test('Editor has no Master Data nav item', async ({ page }) => {
    await page.goto('/templates');
    await expect(page.getByRole('link', { name: /master data/i })).toHaveCount(0);
  });
});
