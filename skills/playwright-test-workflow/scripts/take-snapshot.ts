/**
 * take-snapshot.ts — Playwright aria snapshot capture utility
 * Run: npx ts-node take-snapshot.ts <url> [output-file] [options]
 *
 * Requires: npm install (playwright, ts-node, typescript, @types/node)
 *
 * Options:
 *   --mode=ai|default   ai = with refs (for playwright-snapshot-parser)
 *                       default = clean YAML (for toMatchAriaSnapshot)
 *   --selector=<css>    Scope to element (default: body)
 *   --wait=<ms>         Extra wait after load (default: 2000)
 *   --auth=<json>       Auth state file from page.context().storageState()
 *   --depth=<n>         Limit snapshot depth
 *   --viewport=<WxH>    e.g. 1280x800 (default: 1280x800)
 *
 * Examples:
 *   # AI mode — refs included, use with playwright-snapshot-parser (default)
 *   npx ts-node take-snapshot.ts https://app.example.com/login login.txt
 *
 *   # Default YAML — clean output, paste into toMatchAriaSnapshot()
 *   npx ts-node take-snapshot.ts https://app.example.com/login login.yml --mode=default
 *
 *   # Scope to a section
 *   npx ts-node take-snapshot.ts https://app.example.com snap.txt --selector=main
 *
 *   # With saved auth state
 *   npx ts-node take-snapshot.ts https://app.example.com/dashboard dash.txt --auth=auth.json
 */

import { chromium, BrowserContextOptions } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

const args = process.argv.slice(2);
const url = args[0];
const outputFile = args[1] || `snapshot-${Date.now()}.txt`;

const getArg = (prefix: string, fallback: string): string =>
  (args.find(a => a.startsWith(prefix + '=')) || '').replace(prefix + '=', '') || fallback;

const mode     = getArg('--mode', 'ai') as 'ai' | 'default';
const selector = getArg('--selector', 'body');
const waitMs   = parseInt(getArg('--wait', '2000'), 10);
const authFile = getArg('--auth', '');
const depthStr = getArg('--depth', '');
const viewport = getArg('--viewport', '1280x800').split('x').map(Number);

if (!url) {
  console.error([
    'Usage: npx ts-node take-snapshot.ts <url> [output-file] [options]',
    '',
    'Options:',
    '  --mode=ai|default   ai = refs included (for selector extraction)',
    '                      default = clean YAML (for toMatchAriaSnapshot)',
    '  --selector=<css>    Scope to element (default: body)',
    '  --wait=<ms>         Extra wait ms after networkidle (default: 2000)',
    '  --auth=<json>       Auth state file (storageState)',
    '  --depth=<n>         Limit snapshot depth',
    '  --viewport=<WxH>    Browser viewport (default: 1280x800)',
    '',
    'Examples:',
    '  npx ts-node take-snapshot.ts https://app.example.com/login login.txt',
    '  npx ts-node take-snapshot.ts https://app.example.com snap.yml --mode=default',
    '  npx ts-node take-snapshot.ts https://app.example.com dash.txt --auth=auth.json --selector=main',
  ].join('\n'));
  process.exit(1);
}

(async () => {
  console.log(`Capturing ${mode === 'ai' ? 'AI mode (with refs)' : 'default YAML'} snapshot`);
  console.log(`   URL      : ${url}`);
  console.log(`   Selector : ${selector}`);
  console.log(`   Mode     : ${mode}`);
  console.log(`   Output   : ${outputFile}`);

  const browser = await chromium.launch({ headless: true });

  const contextOptions: BrowserContextOptions = {
    viewport: { width: viewport[0] || 1280, height: viewport[1] || 800 },
  };
  if (authFile && fs.existsSync(authFile)) {
    contextOptions.storageState = authFile;
    console.log(`   Auth     : ${authFile}`);
  }

  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();

  await page.goto(url, { waitUntil: 'networkidle' });
  if (waitMs > 0) await page.waitForTimeout(waitMs);

  const snapshotOptions: { mode: 'ai' | 'default'; depth?: number } = { mode };
  if (depthStr) snapshotOptions.depth = parseInt(depthStr, 10);

  const snapshot = await page.locator(selector).ariaSnapshot(snapshotOptions);

  const outputPath = path.resolve(outputFile);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, snapshot, 'utf-8');

  const lines = snapshot.split('\n').length;
  const interactive = (snapshot.match(/\b(button|link|textbox|combobox|checkbox|radio|menuitem)\b/g) || []).length;
  const refs = (snapshot.match(/\[ref=e\d+\]/g) || []).length;
  const blocked = (snapshot.match(/generic.*cursor=pointer/g) || []).length;

  console.log(`\nSnapshot saved: ${outputPath}`);
  console.log(`   Lines               : ${lines}`);
  console.log(`   Interactive elements: ${interactive}`);

  if (mode === 'ai') {
    console.log(`   Refs (for parsing)  : ${refs}`);
    if (blocked > 0) console.log(`   Roleless clickables (BLOCKED): ${blocked} — needs aria-label`);
    console.log(`\nNext: paste into Claude with skill playwright-snapshot-parser`);
  } else {
    const baseName = path.basename(outputFile, path.extname(outputFile));
    console.log(`\nNext: use as toMatchAriaSnapshot() template:`);
    console.log(`   await expect(page.locator('${selector}')).toMatchAriaSnapshot(\`...\`);`);
    console.log(`   Or store in file:`);
    console.log(`   await expect(page.locator('${selector}')).toMatchAriaSnapshot({ name: '${baseName}.aria.yml' });`);
    console.log(`   Then update: npx playwright test --update-snapshots`);
  }

  await browser.close();
})().catch((e: Error) => {
  console.error('Error:', e.message);
  if (e.message.includes("Cannot find module 'playwright'")) {
    console.error('   Fix: npm install  (run in scripts/ directory)');
  }
  process.exit(1);
});
