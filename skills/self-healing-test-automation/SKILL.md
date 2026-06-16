---
name: self-healing-test-automation
description: |
  AI-driven self-healing test automation: how to implement automatic test repair for Playwright/E2E suites using locator fallback chains and LLM-based intent resolution. Covers the 6 failure categories (selector, timing, runtime, test data, visual, interaction), rule-based vs AI-driven healing, the Detection→Diagnosis→Remediation pipeline, and Playwright-specific implementation. Use when tests break frequently from UI changes and you want to reduce maintenance burden beyond what manual quarantining or selector best-practices alone can achieve.
  Triggers on: "self-healing test", "auto-healing test", "locator fallback", "AI test repair", "test maintenance automation", "LLM locator healing", "playwright self-healing", "automated test fix".
---

# Self-Healing Test Automation

Self-healing automatically detects and repairs broken tests without manual intervention. In 2026, the approach has split into two tiers: **rule-based fallback** (fast, predictable) and **AI-driven intent resolution** (handles larger changes).

> **Key insight:** Selector-only healing fixes only ~28% of failures. Timing failures account for ~30%. Comprehensive self-healing must cover all six root-cause categories.

---

## The 6 Failure Categories

| Category | ~% of Failures | What Breaks | Self-Healing Response |
|---|---|---|---|
| **Selector** | 28% | DOM restructure, attribute rename | Locator fallback chain → LLM regeneration |
| **Timing** | 30% | Slow API, animation, cold start | Insert resilient wait / polling via network trace analysis |
| **Runtime error** | ~15% | JS exception, memory pressure | Retry with environment reset; log for diagnosis |
| **Test data** | ~12% | Stale fixtures, missing seed data | Re-seed from canonical source; flag data drift |
| **Visual assertion** | ~10% | Layout shift, new element | Re-baseline screenshot; flag for human review |
| **Interaction change** | ~5% | Button removed, scroll target moved | Re-map interaction to equivalent semantic action |

---

## Tier 1: Rule-Based Locator Fallback (Start Here)

Maintain a priority-ordered list of fallback selectors per element. When the primary locator fails, try alternatives before calling an LLM.

```typescript
// playwright-helpers/resilient-locator.ts
const LOCATOR_PRIORITY = [
  (page: Page, meta: ElementMeta) => page.getByTestId(meta.testId),
  (page: Page, meta: ElementMeta) => page.getByRole(meta.role as any, { name: meta.name }),
  (page: Page, meta: ElementMeta) => page.getByLabel(meta.label),
  (page: Page, meta: ElementMeta) => page.getByText(meta.text, { exact: true }),
];

async function resilientLocator(page: Page, meta: ElementMeta): Promise<Locator> {
  for (const strategy of LOCATOR_PRIORITY) {
    const loc = strategy(page, meta);
    if (await loc.count() > 0) return loc;
  }
  throw new Error(`No locator resolved for element: ${JSON.stringify(meta)}`);
}
```

**Ceiling:** Covers ~40–70% of selector failures. Falls short when DOM is substantially restructured.

---

## Tier 2: AI-Driven Intent Resolution

When the fallback chain exhausts all candidates, capture a lightweight DOM snapshot and ask an LLM to generate a new locator based on the test step's semantic intent.

```typescript
// playwright-helpers/ai-healer.ts
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

async function healLocator(
  page: Page,
  failedSelector: string,
  stepDescription: string,
): Promise<string> {
  // Capture accessibility tree (lighter than full DOM)
  const snapshot = await page.accessibility.snapshot();
  const domContext = JSON.stringify(snapshot, null, 2).slice(0, 8000); // token budget

  const response = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 300,
    messages: [{
      role: 'user',
      content: `A Playwright test step failed. The test intends to: "${stepDescription}".
The previously working selector was: "${failedSelector}".
Current accessibility tree: ${domContext}
Return ONLY a valid Playwright locator call (e.g. getByRole('button', { name: '...' })), no explanation.`,
    }],
  });

  return (response.content[0] as { text: string }).text.trim();
}
```

**Coverage:** Intent-based healing reaches 75–90%+ of selector failures. Has latency cost (~1–3s per heal); run healing paths only on failures, never preemptively.

---

## Detection → Diagnosis → Remediation Pipeline

```
Test action throws ──► DETECT (catch ActionError)
         │
         ▼
  Classify failure ──► DIAGNOSE
  - Selector miss?     → capture DOM snapshot
  - Timing miss?       → inspect network trace + DOM mutation log
  - Runtime error?     → inspect console logs
  - Test data miss?    → check fixture state
         │
         ▼
  Apply category fix ──► REMEDIATE
  - Selector: fallback chain → AI regeneration
  - Timing:   insert polling / increase timeout
  - Runtime:  retry with reset
  - Data:     re-seed
         │
         ▼
  Re-run step → if passes, persist healed locator to registry
```

---

## Playwright Fixture for Self-Healing

```typescript
// fixtures/healing-fixture.ts
import { test as base, Page } from '@playwright/test';
import { healLocator } from '../helpers/ai-healer';

type HealingFixtures = { healingPage: Page };

export const test = base.extend<HealingFixtures>({
  healingPage: async ({ page }, use) => {
    // Wrap page.locator to add healing on failure
    const origLocator = page.locator.bind(page);
    page.locator = (selector: string, options?: any) => {
      const loc = origLocator(selector, options);
      // Override click to add AI healing on error
      const origClick = loc.click.bind(loc);
      loc.click = async (opts?: any) => {
        try {
          return await origClick(opts);
        } catch (e) {
          const healed = await healLocator(page, selector, `click on ${selector}`);
          console.warn(`[self-heal] ${selector} → ${healed}`);
          return await page.locator(healed).click(opts);
        }
      };
      return loc;
    };
    await use(page);
  },
});
```

---

## When to Use Each Approach

| Situation | Approach |
|---|---|
| Small team, <100 specs | Rule-based fallback chain (Tier 1 only) |
| Large suite with frequent UI changes | Tier 1 + Tier 2 AI healing |
| Flakiness from timing, not selectors | Don't use self-healing — fix root cause (see `flaky-test-prevention`) |
| Visual layout changes | Separate visual baseline review, not self-healing |

---

## Guard Rails

- **Always log and review healed locators** — approve or reject before they are permanently stored. AI can generate plausible-but-wrong selectors.
- **Never heal a timing failure with a longer `waitForTimeout`** — diagnose the API and use `waitForResponse` instead (see `flaky-test-prevention`).
- **Selector healing ≠ test maintenance** — if the same element heals repeatedly, the test design or the UI's testability needs work.
- **Gate healing to CI only** — local dev runs should fail loud so engineers see problems immediately.

---

## Sources
- [The 6 Types of AI Self-Healing in Test Automation — QA Wolf Blog (Mar 2026)](https://www.qawolf.com/blog/self-healing-test-automation-types)
- [AI Self-Healing Test Automation: Beyond Locator Fallback — Autonoma AI](https://getautonoma.com/blog/ai-self-healing-test-automation)
- [How to Implement Playwright Self-Healing Locators at Scale (Feb 2026)](https://software-testing-tutorials-automation.com/2026/02/implement-playwright-self-healing-locators-enterprise-framework.html)
- [Self-Healing Tests in 2026: How Auto-Repair Cuts Maintenance by 80% — Wopee.io](https://wopee.io/blog/self-healing-in-sw-test-automation/)
- [Playwright AI Ecosystem 2026: MCP, Agents & Self-Healing Tests — TestDino](https://testdino.com/blog/playwright-ai-ecosystem)
