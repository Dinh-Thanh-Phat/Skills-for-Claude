---
name: maestro-visual-testing
description: Use when you need pixel-level visual regression testing in Maestro mobile flows to catch unintended UI changes across releases, React Native / Flutter library upgrades, or theme changes. Triggers on: "maestro assertScreenshot", "maestro visual regression", "maestro screenshot comparison", "maestro visual testing", "mobile visual diff", "maestro baseline screenshot", "catch UI changes maestro".
---

# Maestro Visual Testing

Maestro's `assertScreenshot` command captures a screenshot and compares it to a stored baseline image, failing if the pixel difference exceeds a configurable threshold. This is **pixel-level regression detection** — distinct from `assertNoDefectsWithAI` (layout defect detection via LLM) and `assertWithAI` (natural-language content assertions).

## Basic Usage

> 🚨 **`assertScreenshot` does NOT create a baseline.** Per the docs it "will fail if the comparison
> image is too dissimilar, **or doesn't exist**." The reference image must already exist — create it
> with `takeScreenshot` in an earlier (recording) run. A bare `- assertScreenshot` with no path is not
> a valid form; always give a path.

**Step 1 — record the reference (one-off, on the pinned baseline device):**

```yaml
# flows/visual-record.yaml
appId: com.example.app
---
- launchApp
- tapOn: "Products"
- takeScreenshot: baselines/products     # writes the reference image
```

**Step 2 — compare on every run:**

```yaml
# flows/visual-check.yaml
appId: com.example.app
---
- launchApp
- tapOn: "Products"
- assertScreenshot: baselines/products.png   # fails if missing OR below threshold
```

The `path` resolves **relative to the flow file** (CHANGELOG: "allow relative paths from flows for
reference images"); the file extension is optional. Whether `takeScreenshot` output lands at exactly
that flow-relative path depends on your output-dir settings (`--test-output-dir`) — UNVERIFIED; check
where the PNG was written after the record run and move it next to the flows if needed.

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
    path: cart
    thresholdPercentage: 99   # strict — pixel-perfect checkout UI matters

- tapOn: "Proceed to Payment"
- assertScreenshot:
    path: payment-form
    thresholdPercentage: 97
    cropOn:
      id: "payment-form"
```

### Tuning strictness per environment

Drive the threshold from an env var rather than hardcoding it, so CI can run stricter than local:

```yaml
env:
  VISUAL_THRESHOLD: 95      # CI overrides to 99 for release builds
---
- assertScreenshot:
    path: home
    thresholdPercentage: ${VISUAL_THRESHOLD}
```

> Prefer this over trying to switch the assertion off. If a screen genuinely cannot be checked in
> some environment, skip it with a documented reason rather than lowering the threshold to a value
> that passes everything — a disabled check is honest, a 10% threshold is a lie.

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

## Audit existing flows for the inversion trap

Any flow written against the "lower = stricter" misreading is silently passing. Find them:

```bash
# List every threshold in the repo
grep -rn "thresholdPercentage" .maestro/ flows/ 2>/dev/null

# Flag suspicious low values (<50 is almost certainly the inverted misreading)
grep -rn "thresholdPercentage" .maestro/ flows/ 2>/dev/null \
  | grep -E "thresholdPercentage:\s*([0-9]|[1-4][0-9])\s*$"
```

For each hit: raise the value, then **prove the assertion can fail** (change something visible and
confirm a red run) before accepting the new baseline.

## Anti-patterns

| Anti-pattern | Why it fails | Do instead |
|---|---|---|
| `thresholdPercentage: 1` meaning "strict" | It means 1% match required → never fails | Higher = stricter; use 98/99 |
| Trusting a baseline that has never failed | An unproven assertion may be asserting nothing | Break it on purpose once, confirm red |
| Lowering the threshold to stop a flaky failure | Converts a real signal into a permanent blind spot | Use `cropOn` to exclude the volatile region |
| Full-screen assertions on screens with clocks/avatars/ads | Guaranteed false positives | `cropOn` a stable element |
| Re-recording baselines to make CI green | Erases the regression you were meant to catch | Re-record only for *intentional* UI changes, in a separate commit |
| Committing baselines from a different device/OS/density | Pixel output differs per device | Pin the baseline device; record and compare on the same profile |

## Sources
- https://maestro.dev/blog/visual-testing — `thresholdPercentage` is the percentage match required to pass; default `95.0`; raise to 98/99 for pixel-sensitive components like charts and custom illustrations
- https://docs.maestro.dev/reference/commands-available/assertscreenshot — params `path`, `cropOn`, `thresholdPercentage`, `label`; threshold accepts a variable or JS expression resolving to a number; invalid resolution raises `Invalid thresholdPercentage for assertScreenshot` instead of using the default
- https://maestro.dev/blog — CLI 2.8.0 (Aug 6, 2026): variables in permissions and screenshot thresholds
