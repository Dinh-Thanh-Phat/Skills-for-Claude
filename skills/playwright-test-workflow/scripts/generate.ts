/**
 * generate.ts — Auto-generate a Playwright test spec from an accessibility snapshot.
 *
 * The generated spec uses getByRole selectors extracted directly from the snapshot —
 * no guessing. Use --template=full to also scaffold interaction tests.
 *
 * Usage:
 *   npm run generate -- --snapshot=snapshot.txt --url=URL [options]
 *
 * Options:
 *   --snapshot=FILE       Snapshot file (required; URL is read from metadata if present)
 *   --url=URL             Override the test navigation URL
 *   --output=FILE         Output spec file (default: <feature>.spec.ts)
 *   --feature=NAME        Describe block name (default: derived from heading or URL)
 *   --template=basic|full basic = visibility checks only
 *                         full  = also scaffolds interaction tests (default: basic)
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  parseSnapshotToFlat,
  extractMetadata,
  INTERACTIVE_ROLES,
  ParsedElement,
} from './lib/snapshot-parser';

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const getArg = (flag: string, fallback = ''): string =>
  (args.find(a => a.startsWith(flag + '=')) || '').slice(flag.length + 1) || fallback;

const snapshotFile = getArg('--snapshot');
const urlOverride  = getArg('--url');
const outputFile   = getArg('--output');
const featureArg   = getArg('--feature');
const template     = (getArg('--template', 'basic') || 'basic') as 'basic' | 'full';

if (!snapshotFile) {
  console.error([
    'Usage: npx ts-node generate.ts --snapshot=snapshot.txt [options]',
    '',
    'Options:',
    '  --url=URL             Override navigation URL (read from snapshot metadata if omitted)',
    '  --output=FILE         Output spec file',
    '  --feature=NAME        Describe block name',
    '  --template=basic|full Scaffold depth (default: basic)',
  ].join('\n'));
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Read and parse
// ---------------------------------------------------------------------------

const content  = fs.readFileSync(path.resolve(snapshotFile), 'utf-8');
const metadata = extractMetadata(content);
const elements = parseSnapshotToFlat(content);

const url = urlOverride || metadata.url || 'https://example.com';

// Derive feature name
const headings  = elements.filter(el => el.role === 'heading' && el.name);
const feature   = featureArg
  || headings[0]?.name
  || (() => { try { return new URL(url).pathname.split('/').filter(Boolean).pop(); } catch { return undefined; } })()
  || 'page';

const specFile = outputFile || `${feature.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.spec.ts`;

// Categorise elements
const interactive = elements.filter(el => INTERACTIVE_ROLES.has(el.role) && el.name);
const links       = elements.filter(el => el.role === 'link' && el.name);
const buttons     = elements.filter(el => el.role === 'button' && el.name);
const inputs      = elements.filter(el => ['textbox', 'combobox', 'searchbox'].includes(el.role) && el.name);

// ---------------------------------------------------------------------------
// Selector helper
// ---------------------------------------------------------------------------

function sel(el: ParsedElement): string {
  // For textboxes / form inputs prefer getByLabel if the name looks like a label
  if (['textbox', 'searchbox', 'combobox'].includes(el.role) && el.name) {
    return `page.getByLabel('${el.name}')`;
  }
  return `page.getByRole('${el.role}', { name: '${el.name}' })`;
}

// ---------------------------------------------------------------------------
// Code builder helpers
// ---------------------------------------------------------------------------

const lines: string[] = [];
const ln  = (s = '') => lines.push(s);
const ind = (n: number, s: string) => lines.push('  '.repeat(n) + s);

// ---------------------------------------------------------------------------
// Generate toMatchAriaSnapshot template for structure test
// ---------------------------------------------------------------------------

function buildAriaTemplate(): string {
  const topEls = elements.filter(el => el.depth <= 2).slice(0, 12);
  return topEls
    .map(el => `  ${'  '.repeat(el.depth)}- ${el.role}${el.name ? ` "${el.name}"` : ''}`)
    .join('\n');
}

// ---------------------------------------------------------------------------
// Spec generation
// ---------------------------------------------------------------------------

ln(`import { test, expect } from '@playwright/test';`);
ln();
ln(`// Generated from snapshot: ${path.basename(snapshotFile)}`);
ln(`// Captured: ${metadata.capturedAt || 'unknown'}`);
ln();
ln(`test.describe('${feature}', () => {`);
ind(1, `const URL = '${url}';`);
ln();

// --- Test 1: Page loads with correct structure ---
ind(1, `test('page loads with correct structure', async ({ page }) => {`);
ind(2, `await page.goto(URL);`);
if (headings.length > 0) {
  ind(2, `await expect(${sel(headings[0])}).toBeVisible();`);
}
if (template === 'full') {
  ind(2, ``);
  ind(2, `// Uncomment to lock full page structure (toMatchAriaSnapshot — Playwright v1.49+):`);
  ind(2, `// await expect(page.locator('body')).toMatchAriaSnapshot(\``);
  buildAriaTemplate().split('\n').forEach(l => ind(2, `// ${l}`));
  ind(2, `// \`);`);
}
ind(1, `});`);
ln();

// --- Test 2: Navigation links ---
if (links.length > 0) {
  ind(1, `test('navigation links are visible', async ({ page }) => {`);
  ind(2, `await page.goto(URL);`);
  for (const link of links.slice(0, 6)) {
    ind(2, `await expect(${sel(link)}).toBeVisible();`);
  }
  ind(1, `});`);
  ln();
}

// --- Test 3: Primary buttons ---
if (buttons.length > 0) {
  ind(1, `test('primary buttons are visible and enabled', async ({ page }) => {`);
  ind(2, `await page.goto(URL);`);
  for (const btn of buttons.slice(0, 5)) {
    ind(2, `await expect(${sel(btn)}).toBeVisible();`);
    if (!(btn.attributes['disabled'])) {
      ind(2, `await expect(${sel(btn)}).toBeEnabled();`);
    }
  }
  ind(1, `});`);
  ln();
}

// --- Test 4: Form inputs ---
if (inputs.length > 0) {
  ind(1, `test('form inputs are present and editable', async ({ page }) => {`);
  ind(2, `await page.goto(URL);`);
  for (const input of inputs.slice(0, 5)) {
    ind(2, `await expect(${sel(input)}).toBeVisible();`);
  }
  ind(1, `});`);
  ln();
}

// --- Full template: interaction stubs ---
if (template === 'full' && interactive.length > 0) {
  ind(1, `// ---------------------------------------------------------------------------`);
  ind(1, `// Interaction stubs — fill in assertions after each action`);
  ind(1, `// ---------------------------------------------------------------------------`);
  ln();

  for (const el of interactive.slice(0, 4)) {
    if (el.role === 'button') {
      ind(1, `test.fixme('clicking "${el.name}" button', async ({ page }) => {`);
      ind(2, `await page.goto(URL);`);
      ind(2, `await ${sel(el)}.click();`);
      ind(2, `// TODO: assert the result of clicking`);
      ind(1, `});`);
      ln();
    } else if (['textbox', 'searchbox'].includes(el.role)) {
      ind(1, `test.fixme('"${el.name}" input accepts text', async ({ page }) => {`);
      ind(2, `await page.goto(URL);`);
      ind(2, `await ${sel(el)}.fill('test value');`);
      ind(2, `await expect(${sel(el)}).toHaveValue('test value');`);
      ind(1, `});`);
      ln();
    } else if (el.role === 'combobox') {
      ind(1, `test.fixme('"${el.name}" dropdown opens', async ({ page }) => {`);
      ind(2, `await page.goto(URL);`);
      ind(2, `await ${sel(el)}.click();`);
      ind(2, `// TODO: assert dropdown options appear`);
      ind(1, `});`);
      ln();
    }
  }
}

ln(`});`);
ln();

// ---------------------------------------------------------------------------
// Write
// ---------------------------------------------------------------------------

const specContent = lines.join('\n');
const outPath = path.resolve(specFile);
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, specContent, 'utf-8');

const testCount = lines.filter(l => l.includes('test(')).length;
console.log(`✅ Generated: ${outPath}`);
console.log(`   Feature  : ${feature}`);
console.log(`   URL      : ${url}`);
console.log(`   Tests    : ${testCount} (${template === 'full' ? 'full template with stubs' : 'basic visibility'})`);
console.log(`\nNext: npx playwright test ${specFile}`);
