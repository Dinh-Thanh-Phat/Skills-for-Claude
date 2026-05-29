/**
 * process.ts — Parse Playwright accessibility snapshot into structured JSON
 *
 * Usage:
 *   npm run process -- --input=snapshot.txt [options]
 *
 * Options:
 *   --input=FILE            Snapshot file to parse (required)
 *   --output=FILE           JSON output file (default: stdout)
 *   --filter-role=ROLE      Only elements matching this ARIA role
 *   --filter-name=PATTERN   Name substring filter (case-insensitive)
 *   --interactive-only      Only interactive elements
 *   --format=json|table     Output format (default: json)
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  parseSnapshotToFlat,
  generateSelector,
  extractMetadata,
  isAiMode,
  INTERACTIVE_ROLES,
  LANDMARK_ROLES,
  ParsedElement,
} from './lib/snapshot-parser';

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const getArg = (flag: string, fallback = ''): string =>
  (args.find(a => a.startsWith(flag + '=')) || '').slice(flag.length + 1) || fallback;
const hasFlag = (flag: string): boolean => args.includes(flag);

const inputFile      = getArg('--input');
const outputFile     = getArg('--output');
const filterRole     = getArg('--filter-role').toLowerCase();
const filterName     = getArg('--filter-name').toLowerCase();
const interactiveOnly = hasFlag('--interactive-only');
const format         = (getArg('--format', 'json') || 'json') as 'json' | 'table';

if (!inputFile) {
  console.error([
    'Usage: npx ts-node process.ts --input=snapshot.txt [options]',
    '',
    'Options:',
    '  --output=FILE           JSON output file (omit to print to stdout)',
    '  --filter-role=ROLE      Filter by ARIA role (e.g. button, link)',
    '  --filter-name=PATTERN   Filter by name substring (case-insensitive)',
    '  --interactive-only      Only interactive elements',
    '  --format=json|table     Output format (default: json)',
  ].join('\n'));
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Build result
// ---------------------------------------------------------------------------

const content  = fs.readFileSync(path.resolve(inputFile), 'utf-8');
const metadata = extractMetadata(content);
const aiMode   = isAiMode(content);
const allElements = parseSnapshotToFlat(content);

let elements = allElements;
if (interactiveOnly) elements = elements.filter(el => INTERACTIVE_ROLES.has(el.role));
if (filterRole)      elements = elements.filter(el => el.role === filterRole);
if (filterName)      elements = elements.filter(el => el.name?.toLowerCase().includes(filterName));

interface SelectorResult {
  role: string;
  name?: string;
  ref?: string;
  depth: number;
  pathFromRoot: string[];
  attributes: Record<string, string>;
  selectors: { primary: string; scoped?: string; confidence: string };
  a11yWarning?: string;
}

const results: SelectorResult[] = elements.map(el => {
  const selectors = generateSelector(el);
  const a11yWarning =
    !el.name && INTERACTIVE_ROLES.has(el.role)
      ? `Unnamed ${el.role} — cannot use getByRole; add aria-label`
      : undefined;
  return { role: el.role, name: el.name, ref: el.ref, depth: el.depth,
           pathFromRoot: el.pathFromRoot, attributes: el.attributes, selectors, a11yWarning };
});

const blocked     = results.filter(r => r.selectors.confidence === 'BLOCKED');
const interactive = results.filter(r => INTERACTIVE_ROLES.has(r.role));

const outputData = {
  source: inputFile,
  format: aiMode ? 'ai' : 'default',
  capturedAt: metadata.capturedAt,
  url: metadata.url,
  summary: {
    totalElements: allElements.length,
    matchedElements: results.length,
    interactive: interactive.length,
    blocked: blocked.length,
    landmarks: allElements.filter(el => LANDMARK_ROLES.has(el.role)).length,
    headings: allElements.filter(el => el.role === 'heading').length,
  },
  elements: results,
  selectorMap: results
    .filter(r => INTERACTIVE_ROLES.has(r.role) || r.role === 'heading')
    .map(r => ({
      intent:      r.name ? `${r.role} "${r.name}"` : `unnamed ${r.role}`,
      selector:    r.selectors.primary,
      scoped:      r.selectors.scoped,
      confidence:  r.selectors.confidence,
      a11yWarning: r.a11yWarning || '-',
    })),
  accessibility: {
    critical: results
      .filter(r => r.a11yWarning)
      .map(r => ({ ref: r.ref, role: r.role, issue: r.a11yWarning })),
    warnings: allElements
      .filter(el => el.role === 'generic' && Object.keys(el.attributes).length > 0)
      .map(el => ({ ref: el.ref, role: el.role, issue: 'Generic role — cannot target by getByRole' })),
  },
};

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------

if (format === 'table') {
  console.log('\n### SELECTOR MAP\n');
  console.log('| Intent | Selector | Confidence | A11y |');
  console.log('|--------|----------|------------|------|');
  for (const row of outputData.selectorMap) {
    console.log(`| ${row.intent} | \`${row.selector}\` | ${row.confidence} | ${row.a11yWarning} |`);
  }
  console.log(`\nTotal: ${outputData.summary.totalElements} elements · ${outputData.summary.blocked} blocked · ${outputData.summary.interactive} interactive`);

  if (outputData.accessibility.critical.length > 0) {
    console.log('\n⚠️  Critical A11y Issues:');
    for (const issue of outputData.accessibility.critical) {
      console.log(`  [${issue.ref || '?'}] ${issue.role}: ${issue.issue}`);
    }
  }
} else {
  const json = JSON.stringify(outputData, null, 2);
  if (outputFile) {
    const outPath = path.resolve(outputFile);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, json, 'utf-8');
    console.log(`✅ Saved: ${outPath}`);
    console.log(`   ${outputData.summary.matchedElements} elements · ${outputData.summary.blocked} blocked · ${outputData.summary.interactive} interactive`);
    if (outputData.accessibility.critical.length > 0) {
      console.log(`   ⚠️  ${outputData.accessibility.critical.length} critical a11y issue(s)`);
    }
  } else {
    console.log(json);
  }
}
