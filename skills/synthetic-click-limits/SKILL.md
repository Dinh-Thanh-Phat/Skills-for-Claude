---
name: synthetic-click-limits
description: "Recognize UI controls that only respond to REAL (trusted) user input, not Playwright synthetic clicks — custom dropdowns/kebab (⋯) menus, overlay-positioned buttons, framework popovers. Use when a click 'succeeds' but the menu/popover never opens, or an element is found but interaction does nothing, after 1-2 attempts. Triggers on: menu won't open, dropdown not opening, ... menu, kebab menu, click does nothing, element not visible overlay, synthetic click, trusted event, popover not showing."
type: qa-practice
triggers:
  - "menu won't open"
  - "dropdown not opening"
  - "kebab menu"
  - "3 dots menu"
  - "... menu"
  - "click does nothing"
  - "popover not showing"
  - "trusted event"
  - "overlay button"
---

# Synthetic-Click Limits

## Why this exists (a real mistake)

I tried ~10 ways to open an agent card's `⋯` (kebab) menu — locator click,
coordinate click dead-center (confirmed by screenshot the cursor was ON the button),
hover-then-click, force click. The click *landed* but the menu **never opened**.
I burned a large budget before accepting that more clicking would not help.

**What is (and isn't) going on.** `locator.click()` is NOT a synthetic DOM event: per the
Playwright docs it scrolls the element into view and uses `page.mouse` to click its center —
real browser input, so the events are `isTrusted: true`. Only `locator.dispatchEvent()` is
programmatic (untrusted, like `element.click()` in JS). So when a real `click()` lands and
nothing opens, the usual cause is that the control's handler is bound to something a single
click doesn't reproduce: `pointerdown`/`mousedown` with a specific button/pointerType, a hover
or focus state that must precede it, a timing guard (open-then-close on the same click via
outside-click listener), or a re-render that swaps the node between mousedown and mouseup.

The lesson: when a click clearly hits the right element but nothing happens, the
problem may not be your selector — the control may need a **different input sequence**, or be
**effectively un-automatable by click**. Recognize it fast, switch technique, or declare it manual.

## Signs you've hit a click-doesn't-open wall

- The element is found and the click reports success, **but no menu/popover/dropdown appears**.
- A screenshot taken right after the click shows the button but **no opened menu**.
- Coordinate click at the verified center still does nothing.
- Works perfectly when a human clicks it (user confirms the manual flow).
- Often: kebab `⋯` menus, custom Listbox/Menu popovers, **absolutely-positioned
  overlay buttons** that are siblings of the visual card (so DOM-ancestor locators miss them).

## The 2-attempt rule (then switch — do NOT keep clicking)

After **2** failed open attempts on the same control, STOP retrying clicks and try,
in order:

1. **Keyboard**: focus the trigger and press `Enter`/`Space`/`ArrowDown` —
   keyboard activation often fires the real handler when click doesn't.
   ```ts
   await trigger.focus();
   await page.keyboard.press('Enter');
   ```
2. **Explicit real-input sequence**: `trigger.hover()` → `page.mouse.down()` → short
   web-first wait → `page.mouse.up()`, or `trigger.click({ delay: 100 })` — this reproduces
   handlers that key on hover/press duration. `trigger.dispatchEvent('pointerdown')` is a LAST
   resort: it is *untrusted* and skips actionability, so it only helps when the handler
   doesn't check `isTrusted` — and a pass obtained that way doesn't prove a user could do it.
3. **Direct route**: skip the menu entirely — use the underlying URL/endpoint the
   menu item triggers (e.g. a `/delete/{id}` link) or an API call, if one exists.
4. **Declare it manual**: if none work, mark the case **un-automatable** and move it
   to the manual test set with a note ("⋯ menu does not open from automated input — tried click / keyboard / hover+press").
   Do not keep grinding — see `ask-when-stuck` (P0).

## Don't confuse this with a selector bug

First rule out the ordinary causes (1 quick check each), because those ARE fixable:
- **Wrong element**: page has two matches (a banner + the real card). Use `.last()`,
  scope to a section heading, or filter by a unique child ("Active" chip).
- **Overlay sibling**: the `⋯` is positioned over the card, not inside it —
  DOM `ancestor::*[.//button]` won't reach it; locate it by its own markup/role.
- **Hidden until hover**: `hover()` the card first.

If after fixing those the click still opens nothing → it's a trusted-event wall.

## Related
- `ask-when-stuck` (P0) — stop after 1–2 failures.
- `dom-inspect-first` — verify you're targeting the right element first.
- `expensive-irreversible-ops` — when the un-clickable control is *delete* and you've
  created data you now can't clean up.
