---
name: vitest-unit-testing
description: Vitest unit and component testing patterns for TypeScript/React projects. Use when writing unit tests, component tests, setting up Vitest, configuring coverage, or mocking modules with Vitest. Triggers on: "vitest", "unit test", "component test", "jest.mock", "vi.mock", "test coverage", "React Testing Library", "viết unit test", "viết component test".
triggers:
  - "vitest"
  - "unit test"
  - "component test"
  - "vi.mock"
  - "vi.fn"
  - "test coverage"
  - "React Testing Library"
  - "viết unit test"
  - "viết component test"
  - "coverage threshold"
scope:
  - qa
  - unit
  - vitest
  - react
  - typescript
---

# Vitest Unit Testing Skill

You are a **Senior QA Engineer** writing fast, isolated unit and component tests with Vitest.

## Why Vitest

Vitest is **~2.7x faster than Jest** — 500 tests in ~3s vs ~8s. Uses the same `describe/it/expect` API, runs in same Vite pipeline as your source code, and supports TypeScript natively.

---

## Setup

### Vitest 5 (v5.0.x, Sep 2026) — upgrade gotchas
- Requires **Node ≥ 22.12** + **Vite ≥ 6.4** (`vite` is a peer dep — Yarn: `yarn add -D vite`)
- `clearMocks: true` is now **default** → call history reset before each test. Calls made in setup files / `beforeAll` / module top level are gone before the test runs. `clearMocks: false` restores v4 behaviour.
- `vi.mock` / `vi.unmock` / `vi.hoisted` inside `describe`/`it`/functions now **throw** — keep them top-level (`vi.doMock` is fine anywhere).
- Un-awaited `expect(p).resolves/rejects` (and `toMatchFileSnapshot`) now **fails** the test (was a warning) — always `await`. `expect.poll` fails on timeout.
- `coverage.include: ['src']` = `src/**` only (root-relative, stricter matching) — re-check the reported file set after upgrading.
- Config files are no longer searched in parent folders — pass `--config ../vitest.config.ts`.
- `-t` matches the full name joined with ` > `; `test.sequential` / `describe.sequential` removed.
- Reports default to `.vitest/` (add to `.gitignore`); html reporter uses `outputDir`; json/junit write files, not stdout.
- `vitest --ui` → open the printed `?token=` URL. `toThrow("")` now matches any message.
- Source: https://vitest.dev/guide/migration · https://github.com/vitest-dev/vitest/releases/tag/v5.0.0

```bash
npm install -D vitest @vitest/ui @testing-library/react @testing-library/user-event jsdom
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
});
```

```typescript
// tests/setup.ts
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

afterEach(() => {
  cleanup(); // unmount React components after each test
});
```

---

## Basic Unit Test Pattern

```typescript
// utils/formatCurrency.ts
export function formatCurrency(amount: number, currency = 'VND'): string {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency }).format(amount);
}
```

```typescript
// utils/formatCurrency.test.ts
import { describe, it, expect } from 'vitest';
import { formatCurrency } from './formatCurrency';

describe('formatCurrency', () => {
  it('formats VND correctly', () => {
    expect(formatCurrency(100000)).toBe('100.000 ₫');
  });

  it('handles zero', () => {
    expect(formatCurrency(0)).toBe('0 ₫');
  });

  it('handles negative values', () => {
    expect(formatCurrency(-50000)).toContain('50.000');
  });

  it('accepts custom currency', () => {
    const result = formatCurrency(100, 'USD');
    expect(result).toContain('$');
  });
});
```

---

## Component Testing with React Testing Library

```typescript
// components/UserCard.tsx
export function UserCard({ user }: { user: { name: string; email: string } }) {
  return (
    <div data-testid="user-card">
      <h2>{user.name}</h2>
      <span>{user.email}</span>
    </div>
  );
}
```

```typescript
// components/UserCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { UserCard } from './UserCard';

describe('UserCard', () => {
  const user = { name: 'Nguyen Van A', email: 'a@example.com' };

  it('renders user name', () => {
    render(<UserCard user={user} />);
    expect(screen.getByRole('heading')).toHaveTextContent('Nguyen Van A');
  });

  it('renders user email', () => {
    render(<UserCard user={user} />);
    expect(screen.getByText('a@example.com')).toBeInTheDocument();
  });
});
```

---

## Mocking — `vi.mock`

### Mock a module
```typescript
import { describe, it, expect, vi } from 'vitest';
import { sendEmail } from '../services/email';
import { notifyUser } from './notifications';

// Mock the entire email module
vi.mock('../services/email', () => ({
  sendEmail: vi.fn().mockResolvedValue({ success: true }),
}));

describe('notifyUser', () => {
  it('calls sendEmail with correct args', async () => {
    await notifyUser('user@example.com', 'Welcome!');

    expect(sendEmail).toHaveBeenCalledWith({
      to: 'user@example.com',
      subject: 'Welcome!',
    });
  });
});
```

### Partial mock (keep real implementation for some exports)
```typescript
vi.mock('../utils/date', async () => {
  const actual = await vi.importActual('../utils/date');
  return {
    ...actual,
    getCurrentDate: vi.fn().mockReturnValue(new Date('2026-01-01')), // override only this
  };
});
```

### Mock environment variables
```typescript
beforeEach(() => {
  vi.stubEnv('API_URL', 'https://api.test.example.com');
});

afterEach(() => {
  vi.unstubAllEnvs();
});
```

---

## Spying — `vi.spyOn`

```typescript
import { vi } from 'vitest';
import * as api from '../api/users';

it('calls deleteUser and refreshes list', async () => {
  const deleteSpy = vi.spyOn(api, 'deleteUser').mockResolvedValue(undefined);
  const refreshSpy = vi.spyOn(api, 'getUsers').mockResolvedValue([]);

  await userStore.removeUser('user-123');

  expect(deleteSpy).toHaveBeenCalledWith('user-123');
  expect(refreshSpy).toHaveBeenCalledOnce();
});
```

---

## Testing Async Functions

```typescript
it('fetches user data', async () => {
  vi.mocked(fetch).mockResolvedValueOnce({
    json: async () => ({ id: '1', name: 'Test User' }),
    ok: true,
  } as Response);

  const user = await getUser('1');

  expect(user.name).toBe('Test User');
});

it('throws on fetch failure', async () => {
  vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'));

  await expect(getUser('1')).rejects.toThrow('Network error');
});
```

---

## Snapshot Testing (Use Sparingly)

```typescript
it('renders user list snapshot', () => {
  const { container } = render(<UserList users={TEST_USERS} />);

  // ✅ OK for stable, simple components
  expect(container.firstChild).toMatchSnapshot();
});
```

**When NOT to use snapshots:**
- Dynamic content (dates, IDs, random data) → use specific assertions
- Large complex components → snapshot becomes noise
- Frequently changing UI → snapshot fails every change, reduces trust

---

## Coverage Commands

```bash
# Run tests with coverage
npx vitest run --coverage

# Watch mode with coverage
npx vitest --coverage

# UI mode (visual test runner)
npx vitest --ui            # Vitest 5: open the printed ?token= URL
```

**Coverage output:**
```
 % Stmts | % Branch | % Funcs | % Lines | Uncovered Lines
---------|----------|---------|---------|----------------
   87.5  |    75.0  |   90.0  |   87.5  | 45-48, 62
```

---

## Test File Naming Conventions

```
src/
  utils/
    formatCurrency.ts
    formatCurrency.test.ts      # ✅ co-located
  components/
    UserCard.tsx
    UserCard.test.tsx           # ✅ co-located
tests/
  unit/
    formatCurrency.test.ts      # ✅ also fine — centralized
```

---

## Anti-Patterns to Avoid

```typescript
// ❌ Testing implementation detail — breaks on refactor
expect(component.state.isLoading).toBe(false);

// ✅ Test observable behavior — what the user sees
expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();

// ❌ Global state mutation — poisons other tests
let users: User[] = [];
test('adds user', () => { users.push(newUser); });

// ✅ Fresh state per test
let users: User[];
beforeEach(() => { users = []; });
test('adds user', () => { users.push(newUser); expect(users).toHaveLength(1); });

// ℹ️ Vitest 5: call history is auto-cleared (clearMocks defaults to true).
// ❌ Still a bleed risk: spies/implementations are NOT restored automatically
vi.spyOn(api, 'get').mockResolvedValue(data);
// ✅ Restore explicitly (or `restoreMocks: true` in config)
afterEach(() => { vi.restoreAllMocks(); });
```

---

## Checklist — Before Submitting Unit Tests

- [ ] Tests isolated — no shared mutable state between tests
- [ ] Spies restored in afterEach (or `restoreMocks: true`) — call history auto-clears in Vitest 5
- [ ] Async tests use `await` (not `.then()` chains without return)
- [ ] Testing behavior (what user sees) not implementation (internal state)
- [ ] No snapshots for dynamic content
- [ ] Coverage meets 80% threshold (`npx vitest run --coverage`)
- [ ] Test names describe the scenario: `'returns empty array when no users found'`

---

## Hooks Testing (renderHook)

```typescript
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

it('increments counter', () => {
  const { result } = renderHook(() => useCounter(0));
  act(() => result.current.increment());
  expect(result.current.count).toBe(1);
});
```

## Context Provider Wrap

```typescript
const wrapper = ({ children }) => (
  <ThemeProvider value="dark">{children}</ThemeProvider>
);
const { result } = renderHook(() => useTheme(), { wrapper });
expect(result.current).toBe('dark');
```

## Async / Suspense Components

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { Suspense } from 'react';

it('shows data after suspense resolves', async () => {
  render(
    <Suspense fallback={<div>Loading...</div>}>
      <AsyncComponent />
    </Suspense>
  );
  expect(screen.getByText('Loading...')).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText('Done')).toBeInTheDocument());
});
```

## MSW for Unit / Component Tests

```typescript
// MSW v2+/v3 API (v1 `rest` + `ctx` is obsolete). v3: ESM-only, Node >= 22.
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
  http.get('/api/users', () => HttpResponse.json([{ id: 1, name: 'Test' }]))
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Fake Timers (`vi.useFakeTimers`)

```typescript
beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

it('debounce fires after 300ms', () => {
  const cb = vi.fn();
  const debounced = debounce(cb, 300);
  debounced(); debounced();
  vi.advanceTimersByTime(300);
  expect(cb).toHaveBeenCalledOnce();
});
```

## Parametrized Tests (`it.each`)

```typescript
it.each([
  [1, 1, 2],
  [2, 3, 5],
  [10, -5, 5],
])('add(%i, %i) → %i', (a, b, expected) => {
  expect(add(a, b)).toBe(expected);
});
```

## Sources
- Vitest docs: vitest.dev
- Vitest vs Jest benchmark: vitest.dev/guide/comparisons
- React Testing Library: testing-library.com/docs/react-testing-library/intro
- claude-code-handbook vitest example: github.com/ThamJiaHe/claude-code-handbook
