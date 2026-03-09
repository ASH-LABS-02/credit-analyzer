# End-to-End Testing with Playwright

This directory contains end-to-end tests for the Intelli-Credit platform using Playwright.

## Setup

Install Playwright and browsers:

```bash
npm install -D @playwright/test
npx playwright install
```

## Running Tests

Run all E2E tests:
```bash
npm run test:e2e
```

Run tests in UI mode (interactive):
```bash
npm run test:e2e:ui
```

Run tests in headed mode (see browser):
```bash
npm run test:e2e:headed
```

Run specific test file:
```bash
npx playwright test e2e/complete-user-journey.spec.ts
```

## Test Structure

- `complete-user-journey.spec.ts` - Tests complete user workflows from login to CAM export
- Tests cover:
  - Authentication flow
  - Application creation
  - Document upload
  - Analysis triggering
  - Results review
  - CAM generation and export
  - Error scenarios
  - Concurrent operations

## Prerequisites

Before running E2E tests:

1. **Backend must be running** on `http://localhost:8000`
2. **Frontend dev server must be running** on `http://localhost:5173` (or configure in playwright.config.ts)
3. **Firebase emulators** should be running for authentication and database operations
4. **Test data** should be seeded if required

## Configuration

Edit `playwright.config.ts` to:
- Change base URL
- Adjust timeouts
- Configure browsers
- Set up test reporters
- Configure screenshots and traces

## Debugging

Debug a specific test:
```bash
npx playwright test --debug e2e/complete-user-journey.spec.ts
```

View test report:
```bash
npx playwright show-report
```

## CI/CD Integration

Tests are configured to run in CI with:
- Automatic retries (2 retries on failure)
- Single worker (no parallel execution)
- HTML reporter for results
- Screenshots on failure
- Traces on first retry

## Best Practices

1. **Use data-testid attributes** for reliable element selection
2. **Wait for elements** using `waitFor` methods instead of fixed timeouts
3. **Mock external services** when possible to avoid flaky tests
4. **Clean up test data** after each test
5. **Use page object model** for complex pages (future enhancement)

## Task Reference

Task: 33.2 Write end-to-end tests using Playwright or Cypress
Requirements: All (e2e)
