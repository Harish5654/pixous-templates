import { test, expect } from '@playwright/test';

test.use({ storageState: '.auth/admin.json' });

const TEMPLATE_NAME = `E2E Test Template ${Date.now()}`;
const RENAMED_NAME = `${TEMPLATE_NAME} (renamed)`;

test('create, rename, duplicate, and delete a template', async ({ page }) => {
  await test.step('create a new template', async () => {
    await page.goto('/templates');
    await page.getByRole('button', { name: /^manage$/i }).click();
    await page.getByRole('button', { name: /new template/i }).click();
    await page.waitForURL('**/templates/new');

    await page.getByTestId('template-category-select').selectOption('Business Documents');
    await page.getByTestId('template-name-input').fill(TEMPLATE_NAME);
    await page.getByRole('button', { name: /^save$/i }).click();
    await page.waitForURL('**/templates');
  });

  await test.step('verify it appears in the library', async () => {
    await page.goto('/templates?view=manage');
    await expect(page.getByRole('heading', { name: TEMPLATE_NAME, level: 3 })).toBeVisible();
  });

  await test.step('rename it inline from the card', async () => {
    // Once clicked, the heading is replaced by an <input> — the card's own name
    // is no longer in textContent, so re-querying by hasText would find nothing.
    // Only one card is ever in rename mode at a time, so a page-wide input is safe.
    await page.getByRole('heading', { name: TEMPLATE_NAME, level: 3 }).click();
    const renameInput = page.locator('.template-card input').first();
    await renameInput.fill(RENAMED_NAME);
    await renameInput.press('Enter');
    await expect(page.getByRole('heading', { name: RENAMED_NAME, level: 3 })).toBeVisible();
  });

  await test.step('duplicate it', async () => {
    const card = page.locator('.template-card', { hasText: RENAMED_NAME });
    await card.getByRole('button', { name: /duplicate/i }).click();
    await page.waitForURL(/\/templates\/.+\/edit/);
    await expect(page.getByTestId('template-name-input')).toHaveValue(`Copy of ${RENAMED_NAME}`);
    await page.goto('/templates?view=manage');
    await expect(page.getByRole('heading', { name: `Copy of ${RENAMED_NAME}`, level: 3 })).toBeVisible();
  });

  await test.step('delete both via Master Data category drill-down', async () => {
    page.on('dialog', (dialog) => dialog.accept());
    await page.goto('/admin/master-data');
    // Category names live in an <input value>, not text content — filter by value, not hasText.
    const categoryRow = page.locator('.md-row').filter({ has: page.locator('input[value="Business Documents"]') });
    await categoryRow.getByRole('button', { name: /templates?$/i }).click();

    await page.locator(`button[title='Delete "${RENAMED_NAME}"']`).click();
    await page.locator(`button[title='Delete "Copy of ${RENAMED_NAME}"']`).click();

    await expect(page.locator(`button[title='Delete "${RENAMED_NAME}"']`)).toHaveCount(0);
  });
});
