---
name: playwright-link-audit
description: Write Playwright broken-link checkers that track source pages, handle HEAD/GET fallback, skip bot-protected sites, and report 404/5xx. Use when asked to "check for broken links", "audit links on a site", "find 404 pages", "scan all links", "kiểm tra link hỏng", "tìm 404", "quét links". Always use this when writing ANY link-checking test — it prevents the most common mistakes (HEAD-only, no source tracking, false-positive 403s from Cloudflare).
scope: playwright, link-checking, seo, audit
---

# Playwright Link Audit Skill

Senior QA pattern for checking broken links across a site. The three most common mistakes: using HEAD-only (some servers reject it), not tracking which source page has the broken link, and flagging bot-protected sites as broken.

---

## ⚠️ Critical Rule: Navigate with Browser, Not HTTP Requests

**Never use `request.head()` or `request.get()` to check if an INTERNAL (same-site) link is broken.**
External links (other domains) are the one exception — see `checkUrl` below.

Using HTTP requests checks if the *URL* returns a response — but that is NOT what happens when a user clicks a link:
- Links can have `onclick` handlers that intercept and open email, modal, or new tab
- SPA/Next.js client-side routing means the server might return 200 but show "Not Found" in the page
- JavaScript redirects aren't captured by HTTP requests
- The page title/content is the only reliable 404 indicator — not the HTTP status code

```typescript
// ❌ WRONG — HTTP request to URL. Misses onclick handlers, SPA routing, JS redirects
const res = await request.head(url);
expect(res.status()).toBe(200); // Passes even when clicking shows "Page not found"

// ✅ CORRECT — Real browser navigation, check page content
await page.goto(url, { waitUntil: 'domcontentloaded' });
const is404 = await is404Page(page); // check title/h1/URL for "not found"
expect(is404).toBe(false);
```

### Detect 404 by Page Content, Not Status Code

```typescript
async function is404Page(page: any): Promise<boolean> {
  const title = await page.title().catch(() => '');
  const h1 = await page.locator('h1').first().textContent().catch(() => '');
  const url = page.url();

  return (
    title.toLowerCase().includes('not found') ||
    title.toLowerCase().includes('404') ||
    (h1 || '').toLowerCase().includes('not found') ||
    (h1 || '').toLowerCase().includes('page not found') ||
    url.includes('/404') ||
    url.includes('/not-found')
  );
}
```

**Why page content:** Next.js, Gatsby, and other SSR frameworks serve 200 with a "Page Not Found" page. The HTTP status is 200 but the user sees a 404 page. Only content inspection catches this.

### `checkUrl` (external links only) + `checkLink` dispatcher

External sites are not your SPA, so an HTTP status is the right signal there — and navigating
dozens of third-party pages in the browser is slow. HEAD first; some servers reject HEAD with
405/501, so retry as GET. Network errors are RETURNED as a string (reported), never swallowed.

```typescript
import type { APIRequestContext, Page } from '@playwright/test';

type LinkStatus = number | string; // number = HTTP status, string = error/404-content reason

// External links only — never use for same-site URLs
async function checkUrl(request: APIRequestContext, url: string): Promise<LinkStatus> {
  try {
    let res = await request.head(url, { timeout: 15_000, maxRedirects: 5 });
    if (res.status() === 405 || res.status() === 501) {
      res = await request.get(url, { timeout: 15_000, maxRedirects: 5 });
    }
    return res.status();
  } catch (e) {
    return `NETWORK ERROR: ${(e as Error).message.split('\n')[0]}`; // reported as broken, not hidden
  }
}

// Internal → real browser navigation + content check; external → checkUrl
async function checkLink(page: Page, request: APIRequestContext, url: string): Promise<LinkStatus> {
  if (!url.startsWith(BASE)) return checkUrl(request, url);
  const res = await page.goto(url, { waitUntil: 'domcontentloaded' });
  if (!res) return 'NO RESPONSE';
  if (res.status() >= 400) return res.status();
  return (await is404Page(page)) ? '404 CONTENT (HTTP 200)' : res.status();
}
```

Callers treat anything that is not a number `< 400` as broken.

---

## Always Track Source Pages

The most useful part of a link audit report is knowing WHERE the broken link appears. Without this, the dev team can't fix it.

```typescript
// ❌ Records broken URL only
broken.push(url);

// ✅ Records URL + where it was found
broken.push({ url, foundOn: sourcePagePath });
```

**Implementation: map url → source pages**

```typescript
const sourceMap = new Map<string, string[]>(); // url → pages it appears on

// When crawling page at `currentPath`:
for (const href of hrefs) {
  const normalized = normalizeUrl(href);
  if (normalized) {
    if (!sourceMap.has(normalized)) sourceMap.set(normalized, []);
    sourceMap.get(normalized)!.push(currentPath);
  }
}
```

---

## Bot-Protected Sites: Skip, Don't Report as Broken

These always return 403/429 in automated requests but work fine in real browsers:

```typescript
const BOT_PROTECTED = [
  /linkedin\.com/,
  /facebook\.com/,
  /twitter\.com/,
  /x\.com/,
  /instagram\.com/,
  /youtube\.com/,
  /clutch\.co/,       // Cloudflare bot protection
  /goodfirms\.co/,    // same
  /trustpilot\.com/,  // same
];

function isBotProtected(url: string): boolean {
  return BOT_PROTECTED.some(p => p.test(url));
}
```

**Rule:** Skip these in automated checks. Verify them manually if needed.

---

## URL Normalization

Always normalize before deduplication to avoid checking the same URL twice.

```typescript
function normalizeUrl(href: string, base: string): string | null {
  try {
    if (!href) return null;
    // Skip non-HTTP schemes
    if (/^(mailto:|tel:|javascript:|#)/.test(href)) return null;
    
    const url = new URL(href, base);
    // Strip fragment — #section doesn't change the page response
    return `${url.origin}${url.pathname}`.replace(/\/$/, '') || url.origin;
  } catch {
    return null;
  }
}
```

**Why strip fragments:** `/about#team` and `/about#history` are the same HTTP request. Checking both wastes time and produces duplicate results.

---

## BFS Crawl Pattern (Full Site)

For comprehensive audits, crawl from seed pages and follow all discovered internal links.

```typescript
const BASE = 'https://example.com';
const MAX_PAGES = 300; // safety cap

async function crawlSite(page: any) {
  const queue = [BASE];
  const visited = new Set<string>();
  const sourceMap = new Map<string, string[]>();
  const crawlErrors: string[] = []; // pages that could not be crawled — reported, not hidden

  while (queue.length > 0 && visited.size < MAX_PAGES) {
    const url = queue.shift()!;
    if (visited.has(url)) continue;
    visited.add(url);

    try {
      const res = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
      if (!res || res.status() >= 400) continue; // skip 404 seeds

      const hrefs: string[] = await page.locator('a[href]').evaluateAll(
        (anchors: HTMLAnchorElement[]) => anchors.map(a => a.href)
      );

      for (const href of hrefs) {
        const normalized = normalizeUrl(href, BASE);
        if (!normalized) continue;
        
        // Track source
        if (!sourceMap.has(normalized)) sourceMap.set(normalized, []);
        sourceMap.get(normalized)!.push(url.replace(BASE, '') || '/');

        // Queue internal links for crawling
        if (normalized.startsWith(BASE) && !visited.has(normalized)) {
          queue.push(normalized);
        }
      }
    } catch (e) {
      // Crawl continues, but the failure is recorded and surfaced in the final report
      crawlErrors.push(`${url}: ${(e as Error).message.split('\n')[0]}`);
    }
  }

  return { visited, sourceMap, crawlErrors };
}
```

---

## Use `expect.soft()` for Link Audits

Don't fail the test on the first broken link — collect ALL broken links first, then fail once at the end.

```typescript
const broken: string[] = [];

for (const [url, sources] of sourceMap.entries()) {
  if (isBotProtected(url)) continue;

  const status = await checkLink(page, request, url);

  // Soft assertion: continues checking even after failure
  expect.soft(
    typeof status === 'number' && status < 400,
    `HTTP ${status} → ${url}\n  found on: ${sources.join(', ')}`
  ).toBe(true);

  if (typeof status !== 'number' || status >= 400) {
    broken.push(`HTTP ${status} → ${url} (found on: ${sources[0]})`);
  }
}

// Hard fail at the end with full list
expect(broken, `${broken.length} broken links:\n${broken.join('\n')}`).toHaveLength(0);
```

**Why soft first:** Without soft assertions, the test stops at the first broken link and you never know about the others.

---

## Test Structure Template

```typescript
test.describe('TC-LINK: Link Audit', () => {
  
  // Extend timeout for crawl tests — they take minutes
  test('TC-LINK-CRAWL: BFS crawl + full site check', async ({ page, request }) => {
    test.setTimeout(300_000); // 5 min
    
    const { visited, sourceMap, crawlErrors } = await crawlSite(page);
    console.log(`Crawled: ${visited.size} pages, ${sourceMap.size} unique links`);
    
    const broken: string[] = crawlErrors.map(e => `CRAWL ERROR → ${e}`);
    for (const [url, sources] of sourceMap.entries()) {
      if (isBotProtected(url)) continue;
      const status = await checkLink(page, request, url);
      if (typeof status !== 'number' || status >= 400) {
        broken.push(`HTTP ${status} → ${url.replace(BASE, '')} ← ${sources[0]}`);
      }
    }
    
    expect(broken, `Broken links:\n${broken.join('\n')}`).toHaveLength(0);
  });

  // Quick check: just seed pages
  test('TC-LINK-SEEDS: All known pages return 200', async ({ page, request }) => {
    test.setTimeout(60_000);
    const seeds = ['/', '/about', '/contact', '/services']; // add your pages
    const broken: string[] = [];
    
    for (const path of seeds) {
      const status = await checkLink(page, request, `${BASE}${path}`); // internal → browser + content check
      if (typeof status !== 'number' || status >= 400) {
        broken.push(`${status} → ${path}`);
      }
    }
    
    expect(broken, broken.join('\n')).toHaveLength(0);
  });
});
```

---

## Reporting: Classify Broken Links by Category

When you find broken links, group them to make the report actionable:

| Category | Example | Fix |
|---|---|---|
| Old URL slug (renamed) | `/services/old-name` → currently `/services/new-name` | 301 redirect |
| Deleted content (still linked from articles) | `/blog/old-post` in `href` of blog article | Remove/update link in source |
| Sitemap lists non-existent pages | `/sitemap-html` has dead hrefs | Update sitemap |
| Career/job pages removed | `/careers/job-title` in sitemap | Remove from sitemap |

**Always report:** URL + HTTP status + source page(s) where it appears.

---

## Common False Positives (Not Real Bugs)

| Returns | Why | Action |
|---|---|---|
| 403 on Clutch/GoodFirms/LinkedIn | Bot protection (Cloudflare) | Skip in automation |
| 403 on review sites | Same | Skip |
| 405 from HEAD | Server rejects HEAD method | Retry as GET |
| ERR_CONNECTION_TIMEOUT | Network instability during test | Retry once, then report |
