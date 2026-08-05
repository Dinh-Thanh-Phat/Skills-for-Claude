---
name: pact-contract-testing
description: >-
  Consumer-driven contract testing with Pact for microservices API compatibility — consumer
  writes tests to generate JSON contracts, provider verifies against real API, Pact
  Broker/PactFlow manages contracts, can-i-deploy blocks unsafe deployments in CI/CD. Use when
  testing microservice API compatibility, preventing breaking API changes, or setting up
  deployment safety gates between services. Triggers on: "contract testing", "Pact",
  "consumer-driven contract", "can-i-deploy", "PactFlow", "API compatibility", "pact broker",
  "breaking API change", "microservice testing".
---

# Consumer-Driven Contract Testing with Pact

Contract testing catches breaking API changes between microservices **before** deployment, without spinning up the full system. Each consumer declares its expectations; the provider verifies against them.

## Core Concept

```
Consumer test  →  pact file (JSON)  →  Provider verification
     ↓                  ↓                      ↓
generates contract  stored in broker      verifies real API
```

The contract (pact file) is the shared language: it lists every request the consumer makes and the minimum response shape it requires. The provider verifies its actual API satisfies every contract without coordinating a live integration environment.

---

## 1. Consumer Side — Write Tests, Generate Contracts

```javascript
// JavaScript/Node.js example with @pact-foundation/pact
const { PactV3, MatchersV3 } = require('@pact-foundation/pact');
const { like, eachLike } = MatchersV3;

const provider = new PactV3({
  consumer: 'orders-ui',
  provider: 'orders-api',
  dir: './pacts',              // where contract JSON files are written
});

describe('Orders API contract', () => {
  it('returns order list', async () => {
    await provider
      .given('orders exist for user 42')
      .uponReceiving('GET /users/42/orders')
      .withRequest({ method: 'GET', path: '/users/42/orders' })
      .willRespondWith({
        status: 200,
        body: eachLike({
          id: like(1001),
          status: like('pending'),
          total: like(49.99),
        }),
      })
      .executeTest(async (mockProvider) => {
        const orders = await fetchOrders(mockProvider.url, 42);
        expect(orders[0].status).toBe('pending');
      });
  });
});
// Running this test creates ./pacts/orders-ui-orders-api.json
```

**Key principle:** Only assert fields your code actually reads. A contract that demands the full response shape becomes brittle and blocks provider teams from adding new fields.

---

## 2. Provider Side — Verify Contracts

```javascript
// Provider verification — run against the real API
const { Verifier } = require('@pact-foundation/pact');

describe('Provider verification', () => {
  it('satisfies all consumer contracts', () => {
    return new Verifier({
      providerBaseUrl: 'http://localhost:3001',  // real running service
      pactBrokerUrl: 'https://your-broker.pactflow.io',
      pactBrokerToken: process.env.PACT_BROKER_TOKEN,
      provider: 'orders-api',
      publishVerificationResult: true,
      providerVersion: process.env.GIT_SHA,
      stateHandlers: {
        'orders exist for user 42': async () => {
          await seedOrdersForUser(42);   // set up DB state
        },
      },
    }).verifyProvider();
  });
});
```

`stateHandlers` map the "given" strings from consumer contracts to real test-setup code — this is how the provider prepares the state each consumer scenario requires.

---

## 3. Pact Broker / PactFlow — Share and Version Contracts

The Pact Broker is the central store for all contracts and verification results. PactFlow is the hosted/commercial version with SSO, teams, and a better UI.

```bash
# Publish contracts after consumer CI passes
npx pact-broker publish ./pacts \
  --broker-base-url $PACT_BROKER_URL \
  --broker-token $PACT_BROKER_TOKEN \
  --consumer-app-version $GIT_SHA \
  --tag $BRANCH_NAME
```

```bash
# Record that a version has been deployed (tell the broker what's in prod/staging)
npx pact-broker record-deployment \
  --pacticipant orders-ui \
  --version $GIT_SHA \
  --environment production
```

---

## 4. `can-i-deploy` — Deployment Safety Gate

Before deploying, query the broker: has every consumer of `orders-api` successfully verified against the version you're about to release?

```bash
# Check if it's safe to deploy orders-api@$GIT_SHA to production
npx pact-broker can-i-deploy \
  --pacticipant orders-api \
  --version $GIT_SHA \
  --to-environment production \
  --broker-base-url $PACT_BROKER_URL \
  --broker-token $PACT_BROKER_TOKEN

# Exit code 0 → safe to deploy
# Exit code 1 → incompatible contracts → block the deployment
```

Add to your CI/CD pipeline as a gate step after provider tests and before the deploy step:

```yaml
# GitHub Actions excerpt
- name: Check contract compatibility
  run: |
    npx pact-broker can-i-deploy \
      --pacticipant ${{ env.SERVICE_NAME }} \
      --version ${{ github.sha }} \
      --to-environment staging
  env:
    PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
    PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}

- name: Deploy
  if: success()
  run: ./scripts/deploy.sh staging
```

---

## 5. What Contract Testing Covers (and Doesn't)

| Covered | Not Covered |
|---------|-------------|
| Response field presence and types | Business logic correctness |
| Status codes the consumer handles | Database integrity |
| HTTP method + path compatibility | Performance / load |
| Required vs. optional fields | End-to-end user flows |

**Complement contract tests with:** E2E tests for critical user journeys; integration tests for business logic; load tests for performance.

---

## CI/CD Integration Checklist

- [ ] Consumer CI: run Pact consumer tests → publish pact files to broker on every branch push
- [ ] Provider CI: fetch and verify all consumer contracts → publish results to broker
- [ ] Both pipelines: call `can-i-deploy` before deploy step; fail the build if it returns non-zero
- [ ] Post-deploy: call `record-deployment` so the broker's environment model stays accurate
- [ ] Tag contracts with branch names so feature branches don't block main deployments

---

## Anti-Patterns

```javascript
// ❌ Over-specifying — asserts fields the consumer doesn't use
.willRespondWith({
  status: 200,
  body: {
    id: 1001,
    status: 'pending',
    total: 49.99,
    createdAt: '2026-01-01T00:00:00Z',   // consumer never reads this
    updatedAt: '2026-01-02T00:00:00Z',   // blocks provider from changing date format
    internalTag: 'batch-42',             // internal field leaking into contract
  },
})

// ✅ Minimal — only what the consumer actually parses
.willRespondWith({
  status: 200,
  body: {
    id: like(1001),
    status: like('pending'),
    total: like(49.99),
  },
})
```

## Sources

- [Pact Documentation — docs.pact.io](https://docs.pact.io/)
- [Consumer-Driven Contract Testing with Pact: Microservices QA Guide 2026 — SQAExperts](https://www.sqaexperts.com/consumerdriven-contract-testing-with-pact-microservices-qa-guide-for-2026)
- [Contract Testing for Microservices: A Practical Guide 2026 — Total Shift Left](https://totalshiftleft.ai/blog/contract-testing-for-microservices)
- [can-i-deploy — Pact Docs](https://docs.pact.io/pact_broker/can_i_deploy)
- [Pact Contract Testing Complete Guide 2026 — QA Skills](https://qaskills.sh/blog/pact-contract-testing-complete-guide-2026)
