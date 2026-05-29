---
name: figma-to-code
description: Use when implementing UI from a Figma file, Figma screenshot, or any visual design spec into React + Tailwind code. Use before writing any component code when a design reference exists.
---

# Figma to Code

Translate a visual design into React + Tailwind systematically — extract first, build second.

## The Rule

**Never write a single line of component code before completing the extraction checklist.**

Skipping extraction causes: wrong navbar behavior, overflow issues, mismatched spacing, wrong font choices — all found late.

## Step 1: Extraction (before any code)

### 1a. Section inventory
List every section top-to-bottom:
```
✓ Navbar
✓ Hero (full-bleed image? teal overlay?)
✓ Search bar (floating? overlaps hero?)
✓ Features (columns? photo?)
...
```

### 1b. Design tokens
Extract from the design before touching Tailwind:

| Token | Value | Tailwind equiv |
|---|---|---|
| Primary color | #F97316 | orange-500 |
| Background | #0A6B78 | custom inline |
| Body font | Inter | font-sans |
| Display font | Dancing Script | custom Google Font |
| Card radius | 16px | rounded-2xl |

### 1c. Navbar behavior — CRITICAL
Answer these before coding:
- Is the navbar transparent (sits ON hero bg) or opaque white?
- Does it scroll with page or stay fixed?
- Text color: white (transparent nav) or dark (white nav)?

**Most common miss:** Navbar looks white in Figma because it's on a white artboard — but the actual page has it transparent over a dark hero. Always check if nav links are white or dark.

### 1d. Floating / overlapping elements
Identify elements that break normal document flow:
- Search bars that overlap hero/content boundary → separate component, use `-mt-N z-20`
- Price cards that float over images → `absolute` inside `relative` container
- Sticky elements

**Most common miss:** Putting a floating search bar INSIDE the hero with `overflow-hidden` → it gets clipped.

## Step 2: Component structure

```
pages/
  HomerunPage.tsx        ← wire all sections

components/[feature]/
  Navbar.tsx
  Hero.tsx               ← background image only, no floating children
  SearchBar.tsx          ← SEPARATE from Hero if it overlaps the boundary
  Features.tsx
  ...
```

Rule: **Each section = one file.** If an element floats between two sections, it gets its own file.

## Step 3: Build order

1. Design tokens → `tailwind.config.js` + `index.html` (Google Fonts)
2. Page shell (`App.tsx` / `Page.tsx`) importing all sections
3. Navbar first (affects all other sections)
4. Hero (background image + overlay)
5. Floating elements (SearchBar etc.)
6. Remaining sections top-to-bottom
7. Footer last

## Background image pattern

```tsx
// Full-cover hero with color overlay
<section className="relative">
  {/* Background */}
  <div
    className="absolute inset-0 bg-cover bg-center"
    style={{ backgroundImage: 'url(...)' }}
  />
  {/* Tint overlay */}
  <div className="absolute inset-0" style={{ backgroundColor: 'rgba(10,107,120,0.82)' }} />
  {/* Content above both layers */}
  <div className="relative z-10 ...">...</div>
</section>
```

## Transparent navbar pattern

```tsx
// Transparent — use when nav is ON a colored hero
<nav className="fixed top-0 left-0 right-0 z-50 flex ...">
  {/* NO bg-white — transparent by default */}
  <span className="text-white">Nav link</span>
</nav>

// Hero accounts for fixed nav with pt-[navHeight]
<section>
  <div className="pt-28 pb-20">...</div>
</section>
```

## Floating search bar pattern

```tsx
// In PageLayout — NEVER inside Hero if Hero has overflow-hidden
<HomerunHero />
<HomerunSearchBar />   {/* separate, -mt-10 z-20 */}
<div className="pt-10">  {/* offset for overlap */}
  <HomerunFeatures />
</div>
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Navbar white when design shows transparent | Check nav link colors in design — white = transparent |
| Search bar clipped | Move outside Hero, use negative margin |
| Font looks wrong | Add Google Font to `index.html` before using in component |
| Image not covering banner | Use `absolute inset-0 bg-cover` layer, not `<img>` tag |
| Sections overlapping wrong | Check `z-index` on floating elements |
