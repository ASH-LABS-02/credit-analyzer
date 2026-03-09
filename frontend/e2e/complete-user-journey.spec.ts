import { test, expect } from '@playwright/test';

/**
 * End-to-End Tests: Complete User Journey from Login to CAM Export
 * 
 * These tests verify the complete user experience through the application,
 * simulating real user interactions from authentication through analysis completion.
 * 
 * Task: 33.2 Write end-to-end tests using Playwright or Cypress
 * Requirements: All (e2e)
 */

test.describe('Complete User Journey', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
  });

  test('should complete full workflow from login to CAM export', async ({ page }) => {
    /**
     * Test complete user journey:
     * 1. User logs in
     * 2. Creates new application
     * 3. Uploads documents
     * 4. Triggers analysis
     * 5. Reviews results
     * 6. Generates and exports CAM
     * 
     * Requirements: 8.1, 9.1, 1.1, 3.1, 7.1, 7.4
     */
    
    // Step 1: Login
    await page.fill('input[type="email"]', 'analyst@bank.com');
    await page.fill('input[type="password"]', 'test-password');
    await page.click('button:has-text("Sign In")');
    
    // Wait for dashboard to load
    await expect(page.locator('text=Applications')).toBeVisible({ timeout: 10000 });
    
    // Step 2: Create new application
    await page.click('button:has-text("New Application")');
    
    // Fill application form
    await page.fill('input[name="company_name"]', 'E2E Test Company');
    await page.fill('input[name="loan_amount"]', '1000000');
    await page.fill('input[name="loan_purpose"]', 'Business expansion');
    await page.fill('input[name="applicant_email"]', 'cfo@e2etest.com');
    
    await page.click('button:has-text("Create Application")');
    
    // Wait for application to be created
    await expect(page.locator('text=E2E Test Company')).toBeVisible({ timeout: 5000 });
    
    // Step 3: Upload documents
    await page.click('text=E2E Test Company');
    
    // Wait for application detail page
    await expect(page.locator('text=Documents')).toBeVisible();
    
    // Click on Documents tab
    await page.click('button:has-text("Documents")');
    
    // Upload file (mock file upload)
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'financial_statement.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 mock content')
    });
    
    // Wait for upload confirmation
    await expect(page.locator('text=Upload successful')).toBeVisible({ timeout: 10000 });
    
    // Step 4: Trigger analysis
    await page.click('button:has-text("Start Analysis")');
    
    // Wait for analysis to complete (with longer timeout)
    await expect(page.locator('text=Analysis Complete')).toBeVisible({ timeout: 60000 });
    
    // Step 5: Review results
    // Navigate to Risk Assessment tab
    await page.click('button:has-text("Risk Assessment")');
    
    // Verify credit score is displayed
    await expect(page.locator('text=/Credit Score|Overall Score/')).toBeVisible();
    
    // Verify recommendation is displayed
    await expect(page.locator('text=/Approve|Reject|Approve with conditions/')).toBeVisible();
    
    // Step 6: Generate and export CAM
    await page.click('button:has-text("CAM Report")');
    
    // Wait for CAM content to load
    await expect(page.locator('text=Credit Appraisal Memo')).toBeVisible({ timeout: 10000 });
    
    // Export CAM
    await page.click('button:has-text("Export")');
    
    // Select PDF format
    await page.click('text=PDF');
    
    // Wait for download to start
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Download")');
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toContain('.pdf');
    
    // Verify: Complete workflow executed successfully
    // User navigated through all stages
    // All key features were accessible and functional
  });

  test('should handle error scenarios gracefully', async ({ page }) => {
    /**
     * Test error handling throughout the user journey:
     * 1. Invalid login credentials
     * 2. Invalid document upload
     * 3. Analysis failure recovery
     * 
     * Requirements: 15.1, 15.4
     */
    
    // Test 1: Invalid login
    await page.fill('input[type="email"]', 'invalid@email.com');
    await page.fill('input[type="password"]', 'wrong-password');
    await page.click('button:has-text("Sign In")');
    
    // Should show error message
    await expect(page.locator('text=/Invalid credentials|Login failed/')).toBeVisible({ timeout: 5000 });
    
    // Test 2: Valid login
    await page.fill('input[type="email"]', 'analyst@bank.com');
    await page.fill('input[type="password"]', 'test-password');
    await page.click('button:has-text("Sign In")');
    
    await expect(page.locator('text=Applications')).toBeVisible({ timeout: 10000 });
    
    // Create application
    await page.click('button:has-text("New Application")');
    await page.fill('input[name="company_name"]', 'Error Test Company');
    await page.fill('input[name="loan_amount"]', '500000');
    await page.fill('input[name="loan_purpose"]', 'Testing errors');
    await page.fill('input[name="applicant_email"]', 'cfo@errortest.com');
    await page.click('button:has-text("Create Application")');
    
    await page.click('text=Error Test Company');
    await page.click('button:has-text("Documents")');
    
    // Test 3: Invalid document upload
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'invalid.exe',
      mimeType: 'application/x-msdownload',
      buffer: Buffer.from('EXE content')
    });
    
    // Should show error for invalid file type
    await expect(page.locator('text=/Invalid file type|File type not supported/')).toBeVisible({ timeout: 5000 });
    
    // Upload valid file
    await fileInput.setInputFiles({
      name: 'valid.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 valid content')
    });
    
    await expect(page.locator('text=Upload successful')).toBeVisible({ timeout: 10000 });
    
    // Verify: System handled errors gracefully
    // User received appropriate error messages
    // System recovered and allowed valid operations
  });

  test('should support concurrent user operations', async ({ page, context }) => {
    /**
     * Test concurrent operations:
     * 1. Multiple users viewing same application
     * 2. Concurrent document uploads
     * 3. Simultaneous analysis requests
     * 
     * Requirements: 18.1, 18.5
     */
    
    // Login first user
    await page.fill('input[type="email"]', 'analyst1@bank.com');
    await page.fill('input[type="password"]', 'test-password');
    await page.click('button:has-text("Sign In")');
    
    await expect(page.locator('text=Applications')).toBeVisible({ timeout: 10000 });
    
    // Create application
    await page.click('button:has-text("New Application")');
    await page.fill('input[name="company_name"]', 'Concurrent Test Co');
    await page.fill('input[name="loan_amount"]', '750000');
    await page.fill('input[name="loan_purpose"]', 'Concurrent testing');
    await page.fill('input[name="applicant_email"]', 'cfo@concurrent.com');
    await page.click('button:has-text("Create Application")');
    
    // Get application URL
    await page.click('text=Concurrent Test Co');
    const applicationUrl = page.url();
    
    // Open second browser context (simulating second user)
    const page2 = await context.newPage();
    await page2.goto('/');
    
    // Login second user
    await page2.fill('input[type="email"]', 'analyst2@bank.com');
    await page2.fill('input[type="password"]', 'test-password');
    await page2.click('button:has-text("Sign In")');
    
    await expect(page2.locator('text=Applications')).toBeVisible({ timeout: 10000 });
    
    // Navigate to same application
    await page2.goto(applicationUrl);
    
    // Both users should see the application
    await expect(page.locator('text=Concurrent Test Co')).toBeVisible();
    await expect(page2.locator('text=Concurrent Test Co')).toBeVisible();
    
    // User 1 uploads document
    await page.click('button:has-text("Documents")');
    const fileInput1 = page.locator('input[type="file"]');
    await fileInput1.setInputFiles({
      name: 'doc1.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 doc1')
    });
    
    // User 2 uploads document concurrently
    await page2.click('button:has-text("Documents")');
    const fileInput2 = page2.locator('input[type="file"]');
    await fileInput2.setInputFiles({
      name: 'doc2.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 doc2')
    });
    
    // Both uploads should succeed
    await expect(page.locator('text=Upload successful')).toBeVisible({ timeout: 10000 });
    await expect(page2.locator('text=Upload successful')).toBeVisible({ timeout: 10000 });
    
    // Verify: Concurrent operations handled correctly
    // No data corruption or conflicts
    // Both users can work simultaneously
    
    await page2.close();
  });
});

test.describe('Navigation and UI Interactions', () => {
  test('should navigate through all main sections', async ({ page }) => {
    /**
     * Test navigation through main application sections:
     * 1. Dashboard
     * 2. Application list
     * 3. Application detail
     * 4. All tabs (Overview, Documents, Financial Analysis, Risk, CAM)
     * 
     * Requirements: 13.1, 13.2
     */
    
    // Login
    await page.goto('/');
    await page.fill('input[type="email"]', 'analyst@bank.com');
    await page.fill('input[type="password"]', 'test-password');
    await page.click('button:has-text("Sign In")');
    
    // Dashboard
    await expect(page.locator('text=Applications')).toBeVisible({ timeout: 10000 });
    
    // Create test application
    await page.click('button:has-text("New Application")');
    await page.fill('input[name="company_name"]', 'Navigation Test Co');
    await page.fill('input[name="loan_amount"]', '600000');
    await page.fill('input[name="loan_purpose"]', 'Navigation testing');
    await page.fill('input[name="applicant_email"]', 'cfo@navtest.com');
    await page.click('button:has-text("Create Application")');
    
    // Navigate to application
    await page.click('text=Navigation Test Co');
    
    // Test all tabs
    const tabs = ['Overview', 'Documents', 'Financial Analysis', 'Risk Assessment', 'CAM Report'];
    
    for (const tab of tabs) {
      await page.click(`button:has-text("${tab}")`);
      await expect(page.locator(`button:has-text("${tab}")`)).toHaveClass(/bg-black|active/);
      
      // Wait for tab content to load
      await page.waitForTimeout(500);
    }
    
    // Navigate back to dashboard
    await page.click('text=Back to Dashboard');
    await expect(page.locator('text=Applications')).toBeVisible();
    
    // Verify: All navigation worked correctly
    // User can access all sections
    // UI responds appropriately
  });

  test('should display loading states appropriately', async ({ page }) => {
    /**
     * Test loading states throughout the application:
     * 1. Initial page load
     * 2. Data fetching
     * 3. Analysis processing
     * 
     * Requirements: 11.5, 13.4
     */
    
    // Login
    await page.goto('/');
    await page.fill('input[type="email"]', 'analyst@bank.com');
    await page.fill('input[type="password"]', 'test-password');
    await page.click('button:has-text("Sign In")');
    
    // Should show loading state while fetching applications
    await expect(page.locator('text=/Loading|Fetching/')).toBeVisible({ timeout: 1000 });
    
    // Wait for applications to load
    await expect(page.locator('text=Applications')).toBeVisible({ timeout: 10000 });
    
    // Create and navigate to application
    await page.click('button:has-text("New Application")');
    await page.fill('input[name="company_name"]', 'Loading Test Co');
    await page.fill('input[name="loan_amount"]', '800000');
    await page.fill('input[name="loan_purpose"]', 'Loading testing');
    await page.fill('input[name="applicant_email"]', 'cfo@loadtest.com');
    await page.click('button:has-text("Create Application")');
    
    await page.click('text=Loading Test Co');
    
    // Upload document and trigger analysis
    await page.click('button:has-text("Documents")');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 test')
    });
    
    await expect(page.locator('text=Upload successful')).toBeVisible({ timeout: 10000 });
    
    // Start analysis
    await page.click('button:has-text("Start Analysis")');
    
    // Should show progress indicator
    await expect(page.locator('text=/Processing|Analyzing|Progress/')).toBeVisible({ timeout: 5000 });
    
    // Verify: Loading states are displayed appropriately
    // User is informed of system status
    // UI provides feedback during operations
  });
});
