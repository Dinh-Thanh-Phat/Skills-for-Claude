/**
 * capture.ts — Enhanced Playwright snapshot capturer
 * Supports single page, component scoping, and multi-page batch capture.
 *
 * Usage:
 *   npm run capture -- --url=URL [options]
 *   npm run capture -- --pages=URL1,URL2,URL3 [options]
 *
 * Options:
 *   --url=URL           Single page URL
 *   --pages=URL1,URL2   Comma-separated list of URLs (overrides --url)
 *   --output=FILE       Output file path (default: snapshot-<ts>.txt)
 *   --mode=ai|default   ai=refs included, default=clean YAML (default: ai)
 *   --selector=CSS      Scope capture to element (default: body)
 *   --component=CSS     Alias for --selector
 *   --wait=MS           Wait after networkidle (default: 2000)
 *   --auth=FILE         Auth state JSON file (from storageState)
 *   --viewport=WxH      Viewport size (default: 1280x800)
 */

import { chromium, BrowserContextOptions, Page } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const getArg = (flag: string, fallback = ''): string =>
  (args.find(a => a.startsWith(flag + '=')) || '').slice(flag.length + 1) || fallback;

const singleUrl   = getArg('--url');
const pagesArg    = getArg('--pages');
const output      = getArg('--output', `snapshot-${Date.now()}.txt`);
const mode        = (getArg('--mode', 'ai') || 'ai') as 'ai' | 'default';
const selector    = getArg('--selector') || getArg('--component', 'body');
const waitMs      = parseInt(getArg('--wait', '2000'), 10);
const authFile    = getArg('--auth');
const viewportRaw = getArg('--viewport', '1280x800').split('x').map(Number);
const viewport: [number, number] = [viewportRaw[0] || 1280, viewportRaw[1] || 800];

const pageUrls: string[] = pagesArg
  ? pagesArg.split(',').map(u => u.trim()).filter(Boolean)
  : singleUrl
  ? [singleUrl]
  : [];

if (pageUrls.length === 0) {
  console.error([
    'Usage:',
    '  npx ts-node capture.ts --url=URL [options]',
    '  npx ts-node capture.ts --pages=URL1,URL2 [options]',
    '',
    'Options:',
    '  --url=URL           Single page URL',
    '  --pages=URL1,URL2   Multiple pages (comma-separated)',
    '  --output=FILE       Output file (default: snapshot-<timestamp>.txt)',
    '  --mode=ai|default   Snapshot mode (default: ai)',
    '  --selector=CSS      Scope to element (default: body)',
    '  --component=CSS     Alias for --selector',
    '  --wait=MS           Wait after networkidle (default: 2000)',
    '  --auth=FILE         Auth state JSON file',
    '  --viewport=WxH      Browser viewport (default: 1280x800)',
  ].join('\n'));
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildOutputPath(base: string, index: number, total: number): string {
  if (total === 1) return base;
  const ext = path.extname(base) || '.txt';
  const stem = base.slice(0, base.length - ext.length);
  return `${stem}-${index + 1}${ext}`;
}

function withMetadata(snapshot: string, pageUrl: string): string {
  return [
    `# url: ${pageUrl}`,
    `# captured: ${new Date().toISOString()}`,
    `# mode: ${mode}`,
    `# selector: ${selector}`,
    `# ---`,
    '',
    snapshot,
  ].join('\n');
}

function stats(snapshot: string) {
  const lines = snapshot.split('\n').length;
  const interactive = (snapshot.match(/\b(button|link|textbox|combobox|checkbox|radio|menuitem)\b/g) || []).length;
  const refs = (snapshot.match(/\[ref=e\d+\]/g) || []).length;
  const blocked = (snapshot.match(/generic.*cursor=pointer/g) || []).length;
  return { lines, interactive, refs, blocked };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

(async () => {
  const browser = await chromium.launch({ headless: true });

  const ctxOptions: BrowserContextOptions = {
    viewport: { width: viewport[0], height: viewport[1] },
  };
  if (authFile && fs.existsSync(authFile)) {
    ctxOptions.storageState = authFile;
    console.log(`  Auth     : ${authFile}`);
  }

  const context = await browser.newContext(ctxOptions);
  const page = await context.newPage();

  const captured: { url: string; file: string }[] = [];

  for (let i = 0; i < pageUrls.length; i++) {
    const pageUrl = pageUrls[i];
    const outFile = buildOutputPath(output, i, pageUrls.length);

    console.log(`\n[${i + 1}/${pageUrls.length}] ${pageUrl}`);

    await page.goto(pageUrl, { waitUntil: 'networkidle' });
    if (waitMs > 0) await page.waitForTimeout(waitMs);

    const snapshot = await page.locator(selector).ariaSnapshot({ mode });
    const content = withMetadata(snapshot, pageUrl);

    const outPath = path.resolve(outFile);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, content, 'utf-8');

    const s = stats(snapshot);
    console.log(`  ✅ Saved : ${outPath}`);
    console.log(`     Lines : ${s.lines}  Interactive : ${s.interactive}  Refs : ${s.refs}${s.blocked > 0 ? `  ⚠️ Blocked : ${s.blocked}` : ''}`);

    captured.push({ url: pageUrl, file: outPath });
  }

  if (captured.length > 1) {
    const idxExt  = path.extname(output) || '.txt';
    const idxStem = output.slice(0, output.length - idxExt.length);
    const idxPath = path.resolve(`${idxStem}-index.json`);
    fs.writeFileSync(idxPath, JSON.stringify(captured, null, 2), 'utf-8');
    console.log(`\n📋 Index  : ${idxPath}`);
  }

  await browser.close();
  console.log('\n✅ Done');

  if (mode === 'ai') {
    console.log('\nNext: npm run process -- --input=' + path.resolve(buildOutputPath(output, 0, pageUrls.length)));
  }
})().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});
