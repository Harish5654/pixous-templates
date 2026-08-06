import { test, expect } from '@playwright/test';

test.use({ storageState: '.auth/employee.json', permissions: ['clipboard-read', 'clipboard-write'] });

test('fill a variable and see the live preview update', async ({ page }) => {
  await page.goto('/templates');
  const card = page.locator('.template-card', { hasText: 'Welcome Client' });
  await card.getByRole('button', { name: /fill & generate/i }).click();

  const modal = page.locator('.card', { hasText: 'Welcome Client' }).last();
  await expect(modal.getByText('Fill Values')).toBeVisible();

  const clientNameField = modal.locator('.form-group', { hasText: 'Client Name' }).locator('input');
  await clientNameField.fill('Acme Corp');
  await expect(modal.getByText(/Hello Acme Corp/i)).toBeVisible();

  await modal.getByRole('button', { name: /^copy$/i }).click();
  await expect(modal.getByRole('button', { name: /copied/i })).toBeVisible();
});

test('checking off a checklist item updates progress', async ({ page }) => {
  await page.goto('/templates');
  const card = page.locator('.template-card', { hasText: 'QA Checklist' });
  await card.getByRole('button', { name: /fill & generate/i }).click();

  const modal = page.locator('.card', { hasText: 'QA Checklist' }).last();
  const checkbox = modal.locator('label', { hasText: 'Execute Regression Test Suite' }).locator('input[type="checkbox"]');
  await expect(checkbox).toBeVisible();

  await checkbox.check();
  await expect(checkbox).toBeChecked();
  await expect(modal.getByText(/1\/5 checked off/)).toBeVisible();
});
