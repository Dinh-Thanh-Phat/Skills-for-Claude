---
name: maestro-visual-testing
description: >-
  Use when you need pixel-level visual regression testing in Maestro mobile flows to catch
  unintended UI changes across releases, React Native / Flutter library upgrades, or theme
  changes. Triggers on: "maestro assertScreenshot", "maestro visual regression", "maestro
  screenshot comparison", "maestro visual testing", "mobile visual diff", "maestro baseline
  screenshot", "catch UI changes maestro", "maestro dark mode test", "maestro setDarkMode",
  "maestro assertDarkMode", "maestro theme testing".
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

### Per-Environment Threshold via Variables (CLI 2.8.0+)

`thresholdPercentage` now accepts a `${VAR}` env-var reference instead of only a hardcoded
number — useful for a looser threshold on CI emulators (font-rendering/anti-aliasing noise)
and a stricter one for a local run against a physical device, without maintaining two flows:

```yaml
appId: com.example.app
env:
  SCREENSHOT_THRESHOLD: 5     # override with --env SCREENSHOT_THRESHOLD=2 for a strict run
---
- assertScreenshot:
    path: ./checkout.png
    thresholdPercentage: ${SCREENSHOT_THRESHOLD}
```

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

## Dark Mode / Light Mode Testing (Core CLI 2.9.0+)

Theme bugs (unreadable text, a light-mode-only icon, a modal that keeps a white background in dark
mode) only show up when the screen is actually rendered in that theme. The core Maestro CLI's
2.9.0 release added explicit theme control so a flow can force each mode instead of depending on
the test device's OS setting:

```yaml
- setDarkMode          # force dark theme (iOS + Android)
- assertDarkMode       # fails if the OS-reported theme isn't dark
- toggleDarkMode       # flip whatever the current theme is
- setDarkMode: false   # back to light
- assertLightMode
```

> Not to be confused with the separate dark-mode support the community `maestro-runner` project
> shipped in its own v1.1.23 (see `maestro-real-ios-device`) — same command names, different
> projects/implementations (core CLI here uses `cmd uimode night`/`simctl ui appearance`
> internally; `maestro-runner` adds physical-device and Web-driver support on top).

Combine with `assertScreenshot` to get a baseline **per theme**, not just per screen — a screen
that passes its light-mode baseline can still be broken in dark mode, and a single baseline set
recorded under the device's default theme will never catch that:

```yaml
# flows/visual-theme-smoke.yaml
appId: com.example.app
---
- launchApp
- setDarkMode: false
- assertLightMode
- assertScreenshot: home-light

- setDarkMode
- assertDarkMode
- assertScreenshot: home-dark
```

Keep light and dark baselines as separate `path` values (e.g. `home-light` / `home-dark`) in the
same `.maestro/screenshots/` tree — treat a theme switch as a distinct screen state, not a variant
of the same baseline.

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
- https://github.com/mobile-dev-inc/maestro/blob/main/CHANGELOG.md — `thresholdPercentage` variable support (2.8.0), verified against the `034_assertScreenshot_threshold_env.yaml` test fixture in the `mobile-dev-inc/maestro` source repo
- https://raw.githubusercontent.com/mobile-dev-inc/maestro/main/CHANGELOG.md — core CLI 2.9.0: `setDarkMode`/`toggleDarkMode`/`assertDarkMode`/`assertLightMode` commands, iOS + Android
