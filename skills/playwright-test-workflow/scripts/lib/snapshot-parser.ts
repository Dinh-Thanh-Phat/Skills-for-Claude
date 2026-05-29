/**
 * lib/snapshot-parser.ts — Shared types and parser for Playwright aria snapshots.
 * Used by: process.ts, diff.ts, generate.ts
 */

export const INTERACTIVE_ROLES = new Set([
  'button', 'link', 'textbox', 'combobox', 'checkbox', 'radio',
  'menuitem', 'tab', 'slider', 'spinbutton', 'searchbox', 'switch',
]);

export const LANDMARK_ROLES = new Set([
  'banner', 'navigation', 'main', 'complementary', 'contentinfo',
  'form', 'dialog', 'alertdialog', 'region', 'search',
]);

export interface ParsedElement {
  role: string;
  name?: string;
  ref?: string;
  depth: number;
  pathFromRoot: string[];
  attributes: Record<string, string>;
  /** role:name:nearestNamedAncestor — used for diffing */
  signature: string;
}

export interface SelectorOptions {
  primary: string;
  scoped?: string;
  confidence: 'HIGH' | 'MED' | 'LOW' | 'BLOCKED';
}

export interface SnapshotMetadata {
  url?: string;
  capturedAt?: string;
  mode?: string;
  selector?: string;
}

// ---------------------------------------------------------------------------

function parseSingleLine(
  line: string
): { role: string; name?: string; ref?: string; attrs: Record<string, string> } | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith('- ')) return null;
  const content = trimmed.slice(2);
  if (content.startsWith('/')) return null; // /url: or /children: directives

  const attrs: Record<string, string> = {};
  let ref: string | undefined;

  const bracketRe = /\[([^\]]+)\]/g;
  let m: RegExpExecArray | null;
  while ((m = bracketRe.exec(content)) !== null) {
    for (const part of m[1].split(',')) {
      const eq = part.trim().indexOf('=');
      if (eq === -1) {
        attrs[part.trim()] = 'true';
      } else {
        const k = part.trim().slice(0, eq).trim();
        const v = part.trim().slice(eq + 1).trim();
        if (k === 'ref') ref = v;
        else attrs[k] = v;
      }
    }
  }

  const stripped = content.replace(/\[([^\]]+)\]/g, '').replace(/:$/, '').trim();
  const nameMatch = stripped.match(/^([a-z][a-z-]*)\s+"([^"]+)"$/);
  const roleOnly = stripped.match(/^([a-z][a-z-]*)$/);

  if (nameMatch) return { role: nameMatch[1], name: nameMatch[2], ref, attrs };
  if (roleOnly) return { role: roleOnly[1], ref, attrs };
  return null;
}

export function parseSnapshotToFlat(content: string): ParsedElement[] {
  const lines = content.split('\n');
  const elements: ParsedElement[] = [];
  const stack: { role: string; name?: string; indent: number }[] = [];

  for (const raw of lines) {
    if (raw.trimStart().startsWith('#')) continue;
    if (!raw.includes('- ')) continue;

    const indent = raw.search(/\S/);
    if (indent === -1) continue;

    const parsed = parseSingleLine(raw);
    if (!parsed) continue;

    while (stack.length > 0 && stack[stack.length - 1].indent >= indent) {
      stack.pop();
    }

    const parentPath = stack.map(s => s.role + (s.name ? `[${s.name}]` : ''));
    const pathFromRoot = [...parentPath, parsed.role + (parsed.name ? `[${parsed.name}]` : '')];

    const namedAncestor = [...stack].reverse().find(s => s.name);
    const ctx = namedAncestor ? `${namedAncestor.role}[${namedAncestor.name}]` : 'root';

    elements.push({
      role: parsed.role,
      name: parsed.name,
      ref: parsed.ref,
      depth: Math.floor(indent / 2),
      pathFromRoot,
      attributes: parsed.attrs,
      signature: `${parsed.role}:${parsed.name || ''}:${ctx}`,
    });

    stack.push({ role: parsed.role, name: parsed.name, indent });
  }

  return elements;
}

export function generateSelector(el: ParsedElement): SelectorOptions {
  if (!el.name) {
    return {
      primary: `/* BLOCKED: unnamed ${el.role} — add aria-label */`,
      confidence: 'BLOCKED',
    };
  }

  const primary = `page.getByRole('${el.role}', { name: '${el.name}' })`;

  const ancestorPath = el.pathFromRoot.slice(0, -1);
  const landmarkAncestor = [...ancestorPath].reverse().find(p => {
    const r = p.match(/^([a-z-]+)/)?.[1];
    return r && LANDMARK_ROLES.has(r);
  });

  let scoped: string | undefined;
  if (landmarkAncestor) {
    const lmRole = landmarkAncestor.match(/^([a-z-]+)/)?.[1];
    const lmName = landmarkAncestor.match(/\[([^\]]+)\]/)?.[1];
    if (lmRole && lmName) {
      scoped = `page.getByRole('${lmRole}', { name: '${lmName}' }).getByRole('${el.role}', { name: '${el.name}' })`;
    }
  }

  return { primary, scoped, confidence: 'HIGH' };
}

export function extractMetadata(content: string): SnapshotMetadata {
  return {
    url: content.match(/# url: (.+)/)?.[1]?.trim(),
    capturedAt: content.match(/# captured: (.+)/)?.[1]?.trim(),
    mode: content.match(/# mode: (.+)/)?.[1]?.trim(),
    selector: content.match(/# selector: (.+)/)?.[1]?.trim(),
  };
}

export function isAiMode(content: string): boolean {
  return content.includes('[ref=');
}
