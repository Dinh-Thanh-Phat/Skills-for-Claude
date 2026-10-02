---
name: odoo-tour-testing
description: |
  Odoo 19 module testing framework: Python unit/integration tests (TransactionCase), Tour-based
  browser integration tests (browser_js / start_tour), and HOOT JavaScript unit tests.
  Use when writing tests for a custom Odoo module, debugging a failing Odoo Tour, running tagged
  test subsets, or setting up CI for an Odoo module.
  Triggers on: "odoo test", "odoo tour", "odoo unit test", "TransactionCase odoo",
  "browser_js odoo", "HOOT odoo", "test odoo module", "odoo 19 testing".
---

# Odoo 19 Module Testing

Odoo 19 ships three test layers. Match the layer to what you're testing.

| Layer | What it tests | Runs in |
|---|---|---|
| **Python unit test** | ORM, business logic, constraints, computed fields | Python / `unittest` |
| **Tour (browser integration)** | Full UI flow — Python → JS → DOM | Chromium (via `browser_js`) |
| **HOOT JS unit test** | Isolated JavaScript components, helpers | Browser at `/web/tests` |

---

## Python Unit Tests

Tests live in `<module>/tests/test_*.py`. The module auto-discovers them.

```python
# my_module/tests/test_sale_order.py
from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')   # run after all modules install
class TestSaleOrderMargin(TransactionCase):

    @classmethod
    def setUpClass(cls):
        # Runs once per class; each test then runs inside a savepoint that is rolled back
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Widget',
            'list_price': 100.0,
            'standard_price': 60.0,
        })

    def test_margin_computed_correctly(self):
        order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
        })
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'price_unit': 100.0,
        })
        self.assertAlmostEqual(line.margin, 40.0)
```

```
# Run only your module's tests
python odoo-bin -d testdb --test-enable --stop-after-init -i my_module

# Run only tests tagged 'post_install'  (--test-tags implies --test-enable)
python odoo-bin -d testdb --test-tags post_install -i my_module --stop-after-init

# Run a specific test class
python odoo-bin -d testdb --test-tags /my_module.TestSaleOrderMargin -i my_module --stop-after-init
```

Without `--stop-after-init` the server keeps running after the tests finish (CI job hangs).

### Key test base classes

| Class | Rollback | HTTP | Use when |
|---|---|---|---|
| `TransactionCase` | Class-level `setUpClass` data; each test wrapped in a savepoint and rolled back | No | ORM / business logic (also for expensive shared setup — put it in `setUpClass`) |
| `HttpCase` | Same as TransactionCase | Yes | Controller endpoints, `browser_js`, `start_tour` |

`SavepointCase` no longer exists (absent from `odoo/tests/common.py` on 19.0) — its behaviour was folded into `TransactionCase`. Replace any `SavepointCase` import with `TransactionCase`.

---

## Tour Tests (browser integration)

Tours run inside Odoo's own JavaScript rendering cycle — no arbitrary timeouts needed.
Each step waits for Odoo to finish its own async operations before proceeding.

### Python side — trigger the tour

```python
# my_module/tests/test_sale_tour.py
from odoo.tests import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestSaleTour(HttpCase):

    def test_create_sale_order_tour(self):
        self.start_tour(
            '/odoo/sales',           # URL to open
            'my_module.sale_order_tour',   # tour name (JS)
            login='admin',
        )

    def test_with_debug_window(self):
        # Opens a Chrome window with DevTools — useful for local debugging
        self.start_tour(
            '/odoo/sales',
            'my_module.sale_order_tour',
            login='admin',
            watch=True,    # ← opens browser window; remove for CI
        )
```

`start_tour` signature (19.0 `odoo/tests/common.py`): `start_tour(url_path, tour_name, step_delay=None, **kwargs)`.
Useful kwargs: `login=`, `watch=True` (keep a visible browser), `debug=True` (debug mode, pauses on `break`/`pause` steps), `timeout=` (seconds, default 60). `step_delay` (ms between steps) logs a warning — local debugging only, never in CI.

### JavaScript side — define the tour

```javascript
// my_module/static/src/tours/sale_order_tour.js
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("my_module.sale_order_tour", {
    steps: () => [
        {
            // Step 1: click New
            trigger: "button.o_list_button_add",
            content: "Click New to create a sale order",
            run: "click",
        },
        {
            // Step 2: fill in customer
            trigger: ".o_field_widget[name='partner_id'] input",
            run: "fill Azure Interior",
        },
        {
            // Step 3: save and assert
            trigger: "button[name='action_confirm']",
            run: "click",
        },
        {
            // Final assertion: order confirmed badge visible
            trigger: ".o_status_bar .o_arrow_button_current:contains('Sales Order')",
        },
    ],
});
```

### Tour step anatomy

```javascript
{
    trigger: "<css-selector>",    // REQUIRED — wait until this element is visible + interactive
    content: "human description", // shown in Tour Recorder UI / tooltip
    run: "click",                 // or "fill <text>", "press Tab", a function, or omit to just assert visibility
    timeout: 10000,               // ms, default 10000, max 60000
    isActive: ["desktop"],        // optional: "enterprise" | "community" | "mobile" | "desktop" | selectors
    tooltipPosition: "bottom",    // optional: top | bottom | left | right
}
```

Allowed keys in Odoo 19 (`StepSchema` in `addons/web_tour/static/src/js/tour_service.js`): `id, content, debugHelp, isActive, run, timeout, tooltipPosition, trigger, expectUnloadPage, pause, break`.
**`extra_trigger` was removed** — a step that uses it fails schema validation. To require a second element, add a separate assert-only step before it:

```javascript
// ❌ old: { trigger: "button.o_form_button_save", extra_trigger: ".o_form_dirty", run: "click" }
// ✅ Odoo 19: one trigger per step
{ trigger: ".o_form_dirty" },                                    // assert-only (no run)
{ trigger: "button.o_form_button_save", run: "click" },
```

---

## HOOT JavaScript Unit Tests (Odoo 19)

HOOT is Odoo's JS unit-test framework (replaces QUnit). Test files go in `<module>/static/tests/`.
UNVERIFIED: the exact version HOOT replaced QUnit (believed to be 17.x/18, not 19) — check before citing a version.

```javascript
// my_module/static/tests/utils.test.js
import { describe, expect, test } from "@odoo/hoot";
import { formatCurrency } from "@my_module/utils/format";

describe("formatCurrency", () => {
    test("formats positive amounts", () => {
        expect(formatCurrency(1234.5, "USD")).toBe("$1,234.50");
    });

    test("formats zero", () => {
        expect(formatCurrency(0, "USD")).toBe("$0.00");
    });
});
```

Run at: `http://localhost:8069/web/tests` (dev mode). Filter by module to isolate.

---

## Tagging Strategy

```python
@tagged('post_install', '-at_install')   # most common for integration tests
@tagged('standard')                       # default; included in every test run
@tagged('-standard', 'my_slow_tests')    # opt-in only; skip in normal CI runs
```

Tags compose: `--test-tags post_install,-my_slow_tests` runs post_install tests
that are NOT tagged my_slow_tests.

---

## Module Structure

```
my_module/
├── tests/
│   ├── __init__.py          # import test_* modules here
│   ├── test_models.py       # Python unit tests
│   └── test_tours.py        # HttpCase tour launchers
└── static/
    ├── src/
    │   └── tours/
    │       └── my_tour.js   # tour definitions
    └── tests/
        └── *.test.js        # HOOT unit tests
```

---

## Common Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Tour step never advances | Trigger CSS selector wrong | Use browser DevTools → copy selector from live DOM |
| Tour passes locally, fails CI | `watch=True` left in | Remove `watch=True` for CI runs |
| `KeyError: ref('...')` in setUp | External ID not in test DB | Use `self.env['model'].create(...)` instead of `ref()` for test-created data |
| Tests interfere with each other | Shared state | Use `TransactionCase` (auto-rollback per test) |
| `kanban_state` field missing | Removed in Odoo 19 | Use `state` field instead |

---

## Sources

- [Testing Odoo — Odoo 19.0 official docs](https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html)
- [Safeguard your code with unit tests — Odoo 19.0 tutorial](https://www.odoo.com/documentation/19.0/developer/tutorials/unit_tests.html)
- [HOOT — Odoo 19.0 docs](https://www.odoo.com/documentation/19.0/developer/reference/frontend/unit_testing/hoot.html)
- [Odoo Testing: Types of Tests and Best Practices — dixmit.com](https://www.dixmit.com/en/blog/our-blog-1/testing-in-odoo-knowledge-and-best-practices-49)
- [Odoo 19 Testing Framework: Unit, Integration & Tours — Octura Solutions](https://octurasolutions.com/resources/odoo-19-testing-framework-unit-integration-and-tour-tests-for-custom-modules)
