import { test as setup, expect } from '@playwright/test';

export const ACCOUNTS = {
  admin: { email: 'admin@pixoustech.com', password: 'password123', file: '.auth/admin.json' },
  editor: { email: 'editor@pixoustech.com', password: 'password123', file: '.auth/editor.json' },
  employee: { email: 'employee@pixoustech.com', password: 'password123', file: '.auth/employee.json' },
};

for (const [role, { email, password, file }] of Object.entries(ACCOUNTS)) {
  setup(`authenticate as ${role}`, async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(password);
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    await page.context().storageState({ path: file });
  });
}
