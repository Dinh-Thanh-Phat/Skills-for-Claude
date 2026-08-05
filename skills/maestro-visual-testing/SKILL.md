---
name: maestro-visual-testing
description: >-
  Use when you need pixel-level visual regression testing in Maestro mobile flows to catch
  unintended UI changes across releases, React Native / Flutter library upgrades, or theme
  changes. Triggers on: "maestro assertScreenshot", "maestro visual regression", "maestro
  screenshot comparison", "maestro visual testing", "mobile visual diff", "maestro baseline
  screenshot", "catch UI changes maestro".
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

```yaml
- assertScreenshot:
    thresholdPercentage: 2    # fail if >2% of pixels differ (default: 5)
    enabled: true             # set to false to disable in env-specific flows
```

| Option | Default | Notes |
|---|---|---|
| `thresholdPercentage` | `5` | Percentage of differing pixels that triggers failure |

## Isolating Volatile Regions with `cropOn`

Dynamic areas (clocks, user avatars, ad banners, timestamps) change every run and cause false positives. Crop the assertion to a stable UI region:

```yaml
- assertScreenshot:
    cropOn:
      element: "product-grid-container"   # crop to this element's bounds only
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
    cropOn:
      element: "cart-badge"   # Only check the cart counter, not full screen
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
