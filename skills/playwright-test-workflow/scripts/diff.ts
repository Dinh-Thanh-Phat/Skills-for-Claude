/**
 * diff.ts — Compare two Playwright accessibility snapshots
 *
 * Detects UI changes (added / removed / modified elements) and produces an
 * impact report highlighting which existing Playwright selectors are at risk.
 *
 * Usage:
 *   npm run diff -- --before=snap-v1.txt --after=snap-v2.txt [options]
 *
 * Options:
 *   --before=FILE     Baseline snapshot (required)
 *   --after=FILE      Current snapshot (required)
 *   --output=FILE     Output report file (omit to print to stdout)
 *   --format=md|json  Output format (default: md)
 */

import * as fs from 'fs';
import * as path from 'path';
import { parseSnapshotToFlat, generateSelector, INTERACTIVE_ROLES, ParsedElement } from './lib/snapshot-parser';

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const getArg = (flag: string, fallback = ''): string =>
  (args.find(a => a.startsWith(flag + '=')) || '').slice(flag.length + 1) || fallback;

const beforeFile = getArg('--before');
const afterFile  = getArg('--after');
const outputFile = getArg('--output');
const format     = (getArg('--format', 'md') || 'md') as 'md' | 'json';

if (!beforeFile || !afterFile) {
  console.error([
    'Usage: npx ts-node diff.ts --before=snap1.txt --after=snap2.txt [options]',
    '',
    'Options:',
    '  --output=FILE     Output report file (omit for stdout)',
    '  --format=md|json  Output format (default: md)',
  ].join('\n'));
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ChangeType = 'added' | 'removed' | 'modified';

interface DiffChange {
  type: ChangeType;
  element: ParsedElement;
  before?: ParsedElement;
  after?: ParsedElement;
  detail: string;
}

interface ImpactItem {
  selector: string;
  issue: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  recommendation: string;
}

// ---------------------------------------------------------------------------
// Diff logic
// ---------------------------------------------------------------------------

function diffElements(before: ParsedElement[], after: ParsedElement[]): DiffChange[] {
  const changes: DiffChange[] = [];
  const bMap = new Map<string, ParsedElement>(before.map(el => [el.signature, el]));
  const aMap = new Map<string, ParsedElement>(after.map(el => [el.signature, el]));

  // Removed
  for (const [sig, el] of bMap) {
    if (!aMap.has(sig)) {
      changes.push({ type: 'removed', element: el, before: el,
        detail: `${el.role}${el.name ? ` "${el.name}"` : ''} removed from UI` });
    }
  }

  // Added
  for (const [sig, el] of aMap) {
    if (!bMap.has(sig)) {
      changes.push({ type: 'added', element: el, after: el,
        detail: `${el.role}${el.name ? ` "${el.name}"` : ''} added to UI` });
    }
  }

  // Modified (same signature, different attributes)
  for (const [sig, afterEl] of aMap) {
    const beforeEl = bMap.get(sig);
    if (!beforeEl) continue;
    if (JSON.stringify(beforeEl.attributes) !== JSON.stringify(afterEl.attributes)) {
      const changedKeys = Object.keys({ ...beforeEl.attributes, ...afterEl.attributes })
        .filter(k => beforeEl.attributes[k] !== afterEl.attributes[k]);
      changes.push({ type: 'modified', element: afterEl, before: beforeEl, after: afterEl,
        detail: `${afterEl.role}${afterEl.name ? ` "${afterEl.name}"` : ''} — attributes changed: ${changedKeys.join(', ')}` });
    }
  }

  return changes;
}

function analyzeImpact(changes: DiffChange[]): ImpactItem[] {
  const impact: ImpactItem[] = [];

  for (const { type, element, before: b, after: a } of changes) {
    const isInteractive = INTERACTIVE_ROLES.has(element.role);
    const sel = element.name ? `page.getByRole('${element.role}', { name: '${element.name}' })` : null;
    if (!sel) continue;

    if (type === 'removed' && isInteractive) {
      impact.push({
        selector: sel,
        issue: 'Element removed — selector will throw "locator not found"',
        severity: 'HIGH',
        recommendation: 'Delete or update this selector. If element moved, re-scope with parent landmark.',
      });
    }

    if (type === 'modified' && isInteractive) {
      const changedAttrs = Object.keys({ ...b?.attributes, ...a?.attributes })
        .filter(k => b?.attributes[k] !== a?.attributes[k]);
      impact.push({
        selector: sel,
        issue: `Attributes changed: ${changedAttrs.join(', ')}`,
        severity: 'MEDIUM',
        recommendation: `Check if tests assert these attributes (disabled, checked, expanded, selected).`,
      });
    }

    if (type === 'added' && isInteractive) {
      impact.push({
        selector: sel,
        issue: 'New element added — verify no duplicate names cause ambiguous matches',
        severity: 'LOW',
        recommendation: 'Run tests to confirm getByRole still resolves to the intended element.',
      });
    }
  }

  return impact;
}

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------

function toMarkdown(
  changes: DiffChange[], impact: ImpactItem[],
  beforePath: string, afterPath: string,
  beforeCount: number, afterCount: number,
): string {
  const added    = changes.filter(c => c.type === 'added');
  const removed  = changes.filter(c => c.type === 'removed');
  const modified = changes.filter(c => c.type === 'modified');
  const highRisk = impact.filter(i => i.severity === 'HIGH');
  const riskLabel = highRisk.length > 0 ? '🔴 HIGH' : impact.length > 0 ? '🟡 MEDIUM' : '🟢 LOW';

  const lines: string[] = [];
  lines.push('# Snapshot Diff Report');
  lines.push('');
  lines.push(`| | |`);
  lines.push(`|---|---|`);
  lines.push(`| **Before** | \`${beforePath}\` (${beforeCount} elements) |`);
  lines.push(`| **After**  | \`${afterPath}\` (${afterCount} elements) |`);
  lines.push(`| **Risk**   | ${riskLabel} |`);
  lines.push(`| **Generated** | ${new Date().toISOString()} |`);

  lines.push('');
  lines.push('## Change Summary');
  lines.push('');
  lines.push('| Type | Count |');
  lines.push('|------|-------|');
  lines.push(`| ➕ Added   | ${added.length} |`);
  lines.push(`| ❌ Removed | ${removed.length} |`);
  lines.push(`| ✏️ Modified | ${modified.length} |`);

  if (removed.length > 0) {
    lines.push('');
    lines.push('## Removed Elements');
    lines.push('');
    for (const c of removed) {
      const el = c.element;
      const depth = '  '.repeat(Math.min(el.depth, 3));
      lines.push(`${depth}- \`${el.role}${el.name ? ` "${el.name}"` : ''}\`${el.ref ? ` [${el.ref}]` : ''}`);
    }
  }

  if (added.length > 0) {
    lines.push('');
    lines.push('## Added Elements');
    lines.push('');
    for (const c of added) {
      const el = c.element;
      lines.push(`- \`${el.role}${el.name ? ` "${el.name}"` : ''}\``);
    }
  }

  if (modified.length > 0) {
    lines.push('');
    lines.push('## Modified Elements');
    lines.push('');
    for (const c of modified) {
      const el = c.element;
      lines.push(`### \`${el.role}${el.name ? ` "${el.name}"` : ''}\``);
      lines.push('');
      lines.push('| Attribute | Before | After |');
      lines.push('|-----------|--------|-------|');
      const allKeys = new Set([...Object.keys(c.before?.attributes || {}), ...Object.keys(c.after?.attributes || {})]);
      for (const k of allKeys) {
        const bv = c.before?.attributes[k] ?? '—';
        const av = c.after?.attributes[k] ?? '—';
        if (bv !== av) lines.push(`| \`${k}\` | ${bv} | ${av} |`);
      }
      lines.push('');
    }
  }

  lines.push('## Impact on Tests');
  lines.push('');
  if (impact.length === 0) {
    lines.push('No breaking changes detected. Existing selectors should continue to work.');
  } else {
    lines.push('| Severity | Selector | Issue | Recommendation |');
    lines.push('|----------|----------|-------|----------------|');
    for (const item of impact) {
      const sev = item.severity === 'HIGH' ? '🔴 HIGH' : item.severity === 'MEDIUM' ? '🟡 MED' : '🟢 LOW';
      lines.push(`| ${sev} | \`${item.selector}\` | ${item.issue} | ${item.recommendation} |`);
    }
  }

  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const beforeContent  = fs.readFileSync(path.resolve(beforeFile), 'utf-8');
const afterContent   = fs.readFileSync(path.resolve(afterFile), 'utf-8');
const beforeElements = parseSnapshotToFlat(beforeContent);
const afterElements  = parseSnapshotToFlat(afterContent);

const changes = diffElements(beforeElements, afterElements);
const impact  = analyzeImpact(changes);

const added    = changes.filter(c => c.type === 'added').length;
const removed  = changes.filter(c => c.type === 'removed').length;
const modified = changes.filter(c => c.type === 'modified').length;
const riskLevel = impact.some(i => i.severity === 'HIGH') ? 'HIGH'
  : impact.some(i => i.severity === 'MEDIUM') ? 'MEDIUM' : 'LOW';

console.log(`\nDiff: ${beforeFile} → ${afterFile}`);
console.log(`  Added: ${added}  Removed: ${removed}  Modified: ${modified}  Risk: ${riskLevel}`);

let outputContent: string;
if (format === 'json') {
  outputContent = JSON.stringify(
    { beforeFile, afterFile, beforeCount: beforeElements.length, afterCount: afterElements.length,
      riskLevel, changes, impact },
    null, 2
  );
} else {
  outputContent = toMarkdown(changes, impact, beforeFile, afterFile, beforeElements.length, afterElements.length);
}

if (outputFile) {
  const outPath = path.resolve(outputFile);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, outputContent, 'utf-8');
  console.log(`\n✅ Report: ${outPath}`);
} else {
  console.log('\n' + outputContent);
}
