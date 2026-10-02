---
name: figma-design-tokens
description: Figma → design token pipeline using Token Studio + Style Dictionary to generate CSS custom properties, Tailwind config, and TypeScript definitions for React. Use when syncing Figma design tokens to a React codebase, setting up a design-system token pipeline, or eliminating design-to-code drift. Triggers on: "design tokens", "Figma to React", "Token Studio", "Style Dictionary", "sync Figma with code", "design system tokens".
---

# Figma Design Tokens Pipeline

You are a **Frontend Engineer** building a design token pipeline that keeps Figma and React code in sync automatically — eliminating Slack messages about hex codes and QA tickets about mismatched padding.

## Architecture

```
Figma (source of truth)
  └─ Token Studio plugin  ──→  tokens.json (GitHub)
       └─ Style Dictionary  ──→  CSS custom properties
                             ──→  Tailwind config
                             ──→  TypeScript token types
                                  └─ React components consume tokens
```

## Step 1: Set Up Token Studio in Figma

1. Install **Tokens Studio for Figma** (Figma Community plugin).
2. Connect to GitHub: Settings → Sync → GitHub → enter repo + branch + file path (e.g., `tokens/tokens.json`).
3. Use **semantic naming** — never raw values:
   - ✅ `color.background.primary`, `color.text.muted`, `spacing.md`, `radius.button`
   - ❌ `blue-500`, `14px`, `#3b82f6`
4. Map Figma Variables / Styles to tokens. Tokens Studio's default export is its **own** JSON format (W3C/DTCG `$value` format is an opt-in setting) — Style Dictionary needs `@tokens-studio/sd-transforms` to read it correctly (math, references, typography/shadow composites). Source: https://docs.tokens.studio/transform-tokens/style-dictionary

### API limits — read before scripting against Figma
- **Variables REST API (`GET /v1/files/:key/variables/local|published`) is Enterprise-only** (scope `file_variables:read`) — https://developers.figma.com/docs/rest-api/variables/. On Starter/Professional/Organization, export via the Tokens Studio plugin or read variables with the official Figma MCP `get_variable_defs`.
- REST rate limits depend on plan **and seat** (effective 2025-11-17, https://developers.figma.com/docs/rest-api/rate-limits/); View/Collab seats get very low caps. Local lesson: Starter + View seat locked for ~4.6 days after ~8 REST calls. Never poll Figma REST from CI — let Tokens Studio push `tokens.json` to Git and build from that.

## Step 2: Style Dictionary Config

```bash
npm install --save-dev style-dictionary @tokens-studio/sd-transforms
```

```js
// sd.config.js  (Style Dictionary v4, ESM)
// Register Tokens Studio transforms per @tokens-studio/sd-transforms README
// (e.g. register(StyleDictionary) + transformGroup 'tokens-studio') when tokens come from Tokens Studio.
export default {
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      prefix: 'ds',
      buildPath: 'src/styles/',
      files: [{ destination: 'tokens.css', format: 'css/variables' }],
    },
    tailwind: {
      transformGroup: 'js',
      buildPath: 'src/styles/',
      // javascript/module = CommonJS with FULL token objects (value + attributes metadata) — unusable as Tailwind theme values.
      // javascript/esm + stripMeta → plain ESM object; or use javascript/module-flat for flat key → value.
      files: [{ destination: 'tailwind-tokens.js', format: 'javascript/esm', options: { stripMeta: true } }],
    },
    ts: {
      transformGroup: 'js',
      buildPath: 'src/styles/',
      // .d.ts for the CommonJS module format; docs: "does not generate 100% accurate d.ts"
      files: [{ destination: 'tokens.d.ts', format: 'typescript/module-declarations' }],
    },
  },
};
```
Format reference: https://styledictionary.com/reference/hooks/formats/predefined/

```bash
npx style-dictionary build --config sd.config.js
```

Output (`src/styles/tokens.css`):
```css
:root {
  --ds-color-background-primary: #ffffff;
  --ds-color-text-muted: #6b7280;
  --ds-spacing-md: 16px;
  --ds-radius-button: 6px;
}
```

## Step 3: Tailwind Integration

Check `package.json` for the Tailwind major version first.

### Tailwind v4 (CSS-first — default for new projects)
v4 defines theme values in CSS with `@theme`; a `tailwind.config.js` is not read unless loaded with `@config`. Generate the `@theme` block with a CSS-variables file (no prefix, Tailwind namespaces) and import it:

```js
// sd.config.js — extra platform for Tailwind v4
tailwind4: {
  transformGroup: 'css',
  buildPath: 'src/styles/',
  files: [{
    destination: 'theme.css',
    format: 'css/variables',
    options: { selector: '@theme', outputReferences: true },
  }],
},
```

```css
/* src/index.css */
@import "tailwindcss";
@import "./styles/theme.css";   /* emits @theme { --color-background-primary: …; --spacing-md: …; } */
```
Name tokens so the variables land in Tailwind namespaces (`--color-*`, `--spacing-*`, `--radius-*`, `--font-*`) → utilities like `bg-background-primary`, `rounded-button`. The `selector: '@theme'` trick is UNVERIFIED against every SD version — check the generated file once. Source: https://tailwindcss.com/docs/theme

### Tailwind v3 (legacy `tailwind.config.js`)

```js
// tailwind.config.js
import tokens from './src/styles/tailwind-tokens.js';

export default {
  theme: {
    extend: {
      colors: tokens.color,
      spacing: tokens.spacing,
      borderRadius: tokens.radius,
    },
  },
};
```

React usage:
```tsx
// Uses Tailwind class — guaranteed to match Figma token
<button className="bg-color-background-primary rounded-radius-button px-spacing-md">
  Submit
</button>
```

## Step 4: Automate with GitHub Actions

```yaml
# .github/workflows/tokens.yml
name: Sync Design Tokens
on:
  push:
    paths: ['tokens/**']   # only runs when Token Studio pushes
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx style-dictionary build --config sd.config.js
      - name: Commit generated tokens
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: sync design tokens"
          file_pattern: "src/styles/tokens.*"
```

Every time a designer updates a token in Figma and syncs via Token Studio, the pipeline auto-generates fresh CSS/Tailwind/TS and commits — zero manual steps for developers.

## Component Naming Convention

Map Figma component variants directly to React props to enable accurate code generation:

| Figma layer name | React prop |
|---|---|
| `Button / Large / Primary` | `<Button size="lg" variant="primary">` |
| `Input / Error` | `<Input state="error">` |
| `Badge / Neutral / Sm` | `<Badge color="neutral" size="sm">` |

Tools like **Builder.io Visual Copilot** and **Locofy** can scaffold the React component from the Figma frame when naming is consistent.

## Code Review Checklist for Generated Code

Generated Figma-to-React code ships faster but must be reviewed before merging:

- [ ] Accessibility: `alt` text on images, `aria-label` on icon buttons
- [ ] Token usage: no hardcoded hex values or px numbers — must reference `--ds-*` or Tailwind token class
- [ ] Responsive: is the layout fluid or does it break at mobile breakpoints?
- [ ] Performance: no unused inline styles; no unnecessary re-renders
- [ ] Semantic HTML: `<button>` not `<div onClick>`, `<ul>` for lists

## Sources
- Token Studio + Style Dictionary pipeline (Apr 2026): https://medium.com/@alexdev82/how-we-built-a-reliable-design-token-pipeline-from-figma-to-react-fddf4725cdbe
- Style Dictionary docs: https://docs.tokens.studio/transform-tokens/style-dictionary
- Figma to React workflow 2026: https://www.superdevacademy.com/en/blogs/figma-to-react-workflow-2026
- Figma Dev Mode + Code Connect: https://inhaq.com/blog/figma-to-code-design-engineer-workflow
