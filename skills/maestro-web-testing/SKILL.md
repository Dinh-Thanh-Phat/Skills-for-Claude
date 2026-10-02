---
name: maestro-web-testing
description: |
  Maestro 2.0 web browser (desktop) testing using the same declarative YAML syntax as Maestro
  mobile flows. Use when a team already uses Maestro for mobile and wants to add web E2E tests
  without adopting a second framework, or when writing cross-platform flows that span mobile and
  web. Triggers on: "maestro web", "maestro browser", "maestro desktop", "web flow maestro",
  "maestro url", "maestro chromium", "single framework mobile and web", "maestro web testing".
---

# Maestro Web Browser Testing (Beta)

Maestro 2.0 extends its declarative YAML syntax from mobile to desktop web browsers.
The same commands (`tapOn`, `inputText`, `assertVisible`) work identically on Android, iOS,
and Chromium. Teams with existing Maestro mobile flows can add web coverage with zero new syntax.

> **Status**: Beta — Chromium only; locale fixed to `en-US`. Docs say viewport is "preset", but the
> CLI (2.11.0) has `maestro test --screen-size <WxH> --headless` to set the headless browser window
> size. Need CLI ≥ 2.9.0 for Chrome 150+ ("Web: fix broken tests on Chrome 150+").

---

## Flow Anatomy

Replace `appId:` with `url:` — everything else is identical to a mobile flow.

```yaml
# flows/web-search.yaml
url: https://example.com        # launches Chromium and navigates here
---
- launchApp                     # opens the browser (downloads Chromium on first run)
- tapOn:
    text: "Search"
- inputText: "Maestro web testing"
- pressKey: Enter
- assertVisible: ".*results.*"  # regex — .* means "contains"
- tapOn:
    text: "First Result"
- assertVisible: "Welcome"
```

`url:` and `appId:` are synonyms internally — `url:` is preferred for readability in web flows.

---

## Commands Available on Web

All standard Maestro commands work on web unless noted:

| Command | Notes |
|---|---|
| `tapOn` | By text, id, or coordinates |
| `inputText` | Clears field and types |
| `pressKey` | `Enter`, `Backspace`, `Tab`, etc. |
| `assertVisible` | Regex supported (`".*partial.*"`) |
| `assertNotVisible` | |
| `scroll` | Scrolls in a direction |
| `openLink` | Navigate to a URL mid-flow |
| `clearState` | Clears cookies/storage for the origin (web support since 2.4.0) |
| `id:` selectors | On Flutter Web, resolve against `flt-semantics-identifier` (2.7.0) |
| `runFlow` | Compose sub-flows exactly as on mobile |
| `evalScript` | Run JavaScript — same engine |

---

## Session & State Management

```yaml
# Clear browser state before sensitive tests (command takes no `true` value)
- clearState

# Or clear state on launchApp
- launchApp:
    clearState: true
```

State is cleared by **origin** (scheme + hostname + port), matching web storage semantics.

> ⚠️ **By default browser state (cookies, local storage) is RETAINED between flows in the same test
> run** (docs). A login in flow A leaks into flow B unless you clear it — order-dependent passes.

---

## Composing Mobile + Web Flows

> ⚠️ **UNVERIFIED — likely does NOT work.** A single `maestro test` run targets one device
> (Android/iOS device OR Chromium); nothing in the docs/CHANGELOG says `runFlow` switches platform
> mid-flow. Treat the example below as hypothetical; the safe pattern is two separate flows run as
> separate invocations (one against the device, one with `--platform web`/Chromium — flag value UNVERIFIED).

```yaml
# flows/checkout-e2e.yaml — mobile app → web confirmation page
appId: com.example.shop
---
- launchApp
- tapOn: "Buy Now"
- runFlow: web-confirm.yaml     # switches to web context mid-flow
```

```yaml
# flows/web-confirm.yaml
url: https://checkout.example.com
---
- assertVisible: "Order Confirmed"
- tapOn: "Download Receipt"
```

---

## Running Web Tests

```bash
# Run a single web flow
maestro test flows/web-search.yaml

# Run all flows (mix of mobile + web) in a folder
maestro test flows/

# Run with Maestro Studio (visual inspection + autocomplete)
maestro studio flows/web-search.yaml
```

Maestro Studio works on web flows and lets you click elements to generate YAML selectors.

---

## Decision: Maestro Web vs Playwright

| Scenario | Use |
|---|---|
| Team already uses Maestro for mobile | **Maestro web** — single framework, same YAML |
| Web-only app with complex auth/API mocking | **Playwright** — richer API, multi-browser |
| Cross-platform mobile + web smoke tests | **Maestro web** — minimal overhead |
| Visual regression, HAR recording, WebSocket | **Playwright** — not available in Maestro beta |
| CI on Maestro Cloud | **Maestro web** — supported natively |
| Firefox / Safari required | **Playwright** — Chromium only in Maestro beta |

---

## Known Beta Limitations (2026)

| Limitation | Status |
|---|---|
| Browser engine | Chromium only (Firefox/Safari: not yet supported) |
| Locale | Fixed to `en-US` |
| Viewport size | Preset (limited configurability) |
| First-run setup | Downloads Chromium on first `launchApp` |
| Multi-tab flows | Not yet supported |
| WebSocket / HAR inspection | Not available (use Playwright for this) |

---

## Sources

- https://docs.maestro.dev/get-started/supported-platform/web-browser
- https://maestro.dev/insights/automate-web-ui-tests-maestro
- https://maestro.dev/blog/introducing-maestro-2-0-0
- https://dev.to/leading-edje/maestro-a-single-framework-for-mobile-and-web-e2e-testing-b98
