import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('unauthenticated visitor is redirected to login', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL('**/login');
  });

  test('wrong password shows an error and does not log in', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('admin@pixoustech.com');
    await page.locator('input[type="password"]').fill('wrong-password');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('correct credentials log in and land on the dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('employee@pixoustech.com');
    await page.locator('input[type="password"]').fill('Employee@123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('logout returns to login and blocks further access', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('employee@pixoustech.com');
    await page.locator('input[type="password"]').fill('Employee@123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');

    await page.getByRole('button', { name: /logout/i }).click();
    await page.waitForURL('**/login');

    await page.goto('/dashboard');
    await page.waitForURL('**/login');
  });
});
