---
name: property-based-testing-api
description: |
  Property-based testing for APIs using fast-check (JS/TS) or Hypothesis (Python):
  auto-generates hundreds of inputs from invariant rules instead of hand-crafted examples,
  then shrinks failures to the minimal reproducing case. Use when testing API contracts during
  migration/refactor, finding edge cases in data transformations, or validating invariants
  (idempotency, schema compliance, referential integrity). Triggers on: "property-based testing",
  "fast-check", "hypothesis testing", "invariant testing", "fuzz API", "generative testing",
  "shrinking test case", "API contract testing".
---

# Property-Based Testing for APIs

Property-based testing (PBT) defines **invariants** — rules that must always hold — and lets
the framework auto-generate hundreds of random inputs to find violations. When a failure occurs,
the framework **shrinks** the input to the simplest reproducing case automatically.

⚠️ **Test data:** every create-style property runs 50–200+ times against a real API. Use an
isolated test environment, prefix generated data (e.g. `AT-PBT-<timestamp>`), and delete what
each run created (track created ids → delete in teardown) — otherwise PBT floods the database.

## Core API Invariants to Catalogue

Before writing tests, enumerate your invariants:

| Category | Example invariant |
|---|---|
| **Idempotency** | `GET /resource/:id` called twice returns identical bodies |
| **Schema compliance** | Every response conforms to the OpenAPI schema |
| **Referential integrity** | `id` in response body can always be looked up via `GET /:id` |
| **Ordering** | `?sort=asc` list items always non-decreasing |
| **Error handling** | Invalid inputs always return 4xx, never 5xx |
| **Round-trip** | Serialize → deserialize → serialize produces the same output |

## fast-check (JavaScript / TypeScript)

```bash
npm install --save-dev fast-check
```

### Schema-Aware Input Generator

```typescript
import fc from 'fast-check';
import { createUser, getUser } from './api';

// Arbitraries (generators)
const userArb = fc.record({
  name:  fc.string({ minLength: 1, maxLength: 100 }),
  email: fc.emailAddress(),
  age:   fc.integer({ min: 0, max: 130 }),
});

// Property: create → fetch round-trip
const createdIds: string[] = [];
afterAll(async () => { for (const id of createdIds) await deleteUser(id); }); // cleanup

test('created user is always retrievable', async () => {
  await fc.assert(
    fc.asyncProperty(userArb, async (user) => {
      const created = await createUser(user);
      createdIds.push(created.id);
      const fetched = await getUser(created.id);
      expect(fetched.email).toBe(user.email);
    }),
    { numRuns: 200 }
  );
});
```

### Idempotency Property

```typescript
test('GET is idempotent', async () => {
  await fc.assert(
    fc.asyncProperty(fc.uuid(), async (id) => {
      // Compare status + body — don't swallow errors with .catch(() => null):
      // a 500 on both calls would then look "idempotent" and pass silently.
      const r1 = await getUserRaw(id);   // returns { status, body } without throwing on 4xx
      const r2 = await getUserRaw(id);
      expect(r1.status).toBeLessThan(500);
      expect(r2).toEqual(r1);
    }),
    { numRuns: 100 }
  );
});
```

### Error Handling Property

```typescript
const invalidEmailArb = fc.string().filter(s => !s.includes('@'));

test('invalid email always returns 400', async () => {
  await fc.assert(
    fc.asyncProperty(invalidEmailArb, async (badEmail) => {
      const res = await createUser({ name: 'Test', email: badEmail, age: 25 });
      expect(res.status).toBe(400);
    }),
    { numRuns: 150 }
  );
});
```

### Shrinking (Automatic)

When fast-check finds a failure, it automatically reduces the input to the smallest
example that still fails:

```
Property failed after 45 tests
Counterexample: [{ name: 'a', email: 'b@c', age: 0 }]  ← shrunk from a 97-char name
```

No manual bisection — the minimal case is reported directly.

## Hypothesis (Python)

```bash
pip install hypothesis pytest
```

```python
from hypothesis import given, settings, strategies as st
import pytest

@given(
    name=st.text(min_size=1, max_size=100),
    age=st.integers(min_value=0, max_value=130),
)
@settings(max_examples=200)
def test_create_user_round_trip(client, name, age):
    resp = client.post('/users', json={'name': name, 'age': age})
    assert resp.status_code == 201
    user_id = resp.json()['id']

    fetch = client.get(f'/users/{user_id}')
    assert fetch.status_code == 200
    assert fetch.json()['name'] == name
```

Hypothesis maintains a **database of found failures** between runs — previously discovered
edge cases are always re-run first.

## Migration Playbook (adding PBT to existing API tests)

1. **Identify the 3–5 highest-value invariants** — idempotency and schema compliance are
   usually the first wins.
2. **Start with 50 runs** (`numRuns: 50`) to confirm the setup works, then raise to 200+.
3. **Use `fc.oneof` for realistic mixed inputs** — don't generate purely random garbage;
   blend valid and near-invalid inputs.
4. **Seed for reproducibility**: `fc.assert(..., { seed: 42 })` — useful in CI to replay
   the same suite.
5. **Integrate gradually** — one property test per endpoint; don't replace example tests.

## Integration with Vitest / Jest

fast-check works with both:

```typescript
// vitest.config.ts — no special config needed; fast-check is plain async
import { defineConfig } from 'vitest/config';
export default defineConfig({ test: { globals: true } });
```

```bash
npx vitest run                  # runs PBT alongside regular tests
npx vitest run --reporter=verbose  # see shrunk counterexamples in output
```

## When to Prefer PBT Over Example Tests

| Situation | Prefer |
|---|---|
| Well-known input/output pair | Example test |
| "Should work for ALL valid inputs" | Property test |
| API migration / schema change | Property test (regression invariants) |
| Edge cases are hard to enumerate | Property test |
| Debugging a specific bug | Example test (document the fix) |

## Sources

- https://www.sachith.co.uk/property%E2%80%91based-testing-for-apis-migration-playbook-practical-guide-jun-4-2026/
- https://fast-check.dev/docs/introduction/what-is-property-based-testing/
- https://github.com/dubzzz/fast-check
- https://hypothesis.readthedocs.io/en/latest/
