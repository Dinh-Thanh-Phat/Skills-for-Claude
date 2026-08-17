---
name: maestro-visual-testing
description: Use when you need pixel-level visual regression testing in Maestro mobile flows to catch unintended UI changes across releases, React Native / Flutter library upgrades, or theme changes. Triggers on: "maestro assertScreenshot", "maestro visual regression", "maestro screenshot comparison", "maestro visual testing", "mobile visual diff", "maestro baseline screenshot", "catch UI changes maestro".
---

# Maestro Visual Testing

Maestro's `assertScreenshot` command captures a screenshot and compares it to a stored baseline image, failing if the pixel difference exceeds a configurable threshold. This is **pixel-level regression detection** — distinct from `assertNoDefectsWithAI` (layout defect detection via LLM) and `assertWithAI` (natural-language content assertions).

## Basic Usage

```yaml
appId: com.example.app
---
- launchApp
- tapOn: "Products"
- assertScreenshot         # first run saves baseline; subsequent runs compare
```

On the first execution Maestro saves the screenshot as the baseline. Subsequent runs compare against it and fail if the visual difference exceeds the threshold.

## Configuration Options

> 🚨 **`thresholdPercentage` is a MATCH percentage, not a difference percentage.**
> It is the *percentage match required to pass*, default **`95`**. **Higher = stricter.**
> This reads backwards from most diffing tools, and getting it wrong does not produce an error —
> it produces a test that silently passes on everything.

```yaml
- assertScreenshot:
    path: checkout-screen        # baseline filename, no extension
    thresholdPercentage: 98      # require 98% pixel match — STRICTER than the 95 default
    cropOn:
      id: "payment-form"
    label: "Checkout screen visual check"
```

| Option | Type | Default | Notes |
|---|---|---|---|
| `path` | string | — | Baseline filename without extension; may include subdirectories. Supports JS expressions |
| `thresholdPercentage` | number | `95` | **Percentage match required to pass.** Higher = stricter. Accepts a variable or JS expression that resolves to a number |
| `cropOn` | selector | — | Compare only this element's bounds |
| `label` | string | — | Message displayed when the assertion runs |

### Picking a threshold

| Value | Meaning | Use for |
|---|---|---|
| `99` / `98` | Near pixel-perfect | Charts, custom illustrations, brand/logo areas, payment UI |
| `95` (default) | Up to 5% of pixels may differ | Most screens — practical starting point |
| `90` | Loose | Screens with mild anti-aliasing or font-rendering variance |
| `50` or below | **Effectively disabled** | Never — this passes almost any screen |

**The inversion trap.** `thresholdPercentage: 1` does *not* mean "fail if >1% differs". It means
"pass if ≥1% of pixels match" — i.e. the assertion can never realistically fail. A suite full of
low values looks green while testing nothing.

Sanity-check a new baseline before trusting it: deliberately change something visible (swap a
string, change a colour) and confirm the assertion **fails**. An assertion that has never failed
has not been proven to work.

### Variables in the threshold (Maestro 2.8.0+)

`thresholdPercentage` accepts variables and JS expressions, so strictness can be tuned per
environment:

```yaml
env:
  VISUAL_THRESHOLD: 98
---
- assertScreenshot:
    path: home
    thresholdPercentage: ${VISUAL_THRESHOLD}
```

> ⚠️ **Unset variables fail loudly, not silently — but read the message.** If the value resolves to
> something invalid (e.g. an empty string from an unset variable), Maestro raises
> `Invalid thresholdPercentage for assertScreenshot` rather than falling back to the default.
> Treat that error as a *harness* misconfiguration, not a visual regression.

## Isolating Volatile Regions with `cropOn`

Dynamic areas (clocks, user avatars, ad banners, timestamps) change every run and cause false positives. Crop the assertion to a stable UI region:

```yaml
- assertScreenshot:
    path: product-grid
    cropOn:
      id: "product-grid-container"   # any standard selector: id, text, ...
```

This ignores everything outside the cropped region — status bars, system UI, and dynamic content stay out of the comparison.

## Practical Patterns

### After a library/framework upgrade

Catch subtle regressions when upgrading React Native, Flutter, or a UI component library:

```yaml
# flows/visual-smoke.yaml
appId: com.example.app
---
- launchApp
- assertScreenshot            # Home screen baseline

- tapOn: "Products"
- assertScreenshot            # Products listing

- tapOn: "Item 1"
- assertScreenshot            # Product detail

- tapOn: "Add to Cart"
- assertScreenshot:
    path: cart-badge
    cropOn:
      id: "cart-badge"        # Only check the cart counter, not full screen
```

### Per-screen visual suite

```yaml
# flows/visual-checkout.yaml
appId: com.example.app
---
- launchApp
- tapOn: "Cart"
- assertScreenshot:
    thresholdPercentage: 1    # strict — pixel-perfect checkout UI matters

- tapOn: "Proceed to Payment"
- assertScreenshot:
    thresholdPercentage: 3
    cropOn:
      element: "payment-form"
```

### Conditional (only run on release builds)

```yaml
env:
  VISUAL_CHECKS: false    # override to true in release CI pipeline

---
- assertScreenshot:
    enabled: ${VISUAL_CHECKS}
```

## When to Use Which Visual Command

| Need | Command |
|---|---|
| Catch pixel-level UI regressions across releases | `assertScreenshot` |
| Detect layout defects (clipping, overlaps) on a specific screen | `assertNoDefectsWithAI` |
| Assert that a screen "looks correct" in plain English | `assertWithAI` |
| Verify specific text content is present | `assertVisible` / `assertWithAI` |

## Managing Baselines

Baselines are stored in `.maestro/screenshots/` by default. Commit them to source control so CI comparisons are deterministic:

```bash
# After intentional UI changes, delete and re-record baselines
rm .maestro/screenshots/<flow-name>/*.png
maestro test flows/visual-smoke.yaml   # saves new baselines
git add .maestro/screenshots/
git commit -m "update visual baselines: new product card design"
```

## CI Integration

```yaml
# .github/workflows/visual-regression.yml
- name: Run Maestro visual tests
  run: maestro test flows/visual-smoke.yaml
  env:
    VISUAL_CHECKS: "true"

- name: Upload diff report on failure
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: visual-diff-report
    path: .maestro/screenshots/
```

## Sources
- https://maestro.dev/blog/visual-testing
- https://docs.maestro.dev/reference/commands-available/assertscreenshot
