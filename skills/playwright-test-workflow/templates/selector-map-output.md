# Selector Map — [Page / Component Name]
<!-- Output template from playwright-snapshot-parser Step 6.
     Fill this after parsing the snapshot and paste into qa-test-generation Phase 2. -->

### SELECTOR MAP — [Page Name]

| Intent | Primary Selector | Confidence | A11y Warning |
|--------|----------------|-----------|--------------|
| [what the element does] | `page.getByRole(...)` | HIGH | - |
| [e.g., submit login form] | `page.getByRole('banner').getByRole('button', { name: 'Log in' })` | HIGH | button inside link |
| [e.g., search coin] | `page.getByRole('textbox', { name: 'Search' })` | HIGH | - |

<!-- Add rows for each interactive element on the page -->

BLOCKED (cannot target semantically — fix a11y first):
- [ref=eN] [role] "[name if any]" — [reason] → [required fix]

CRITICAL A11Y (must fix before automation):
- [ref=eN] [description of issue]

---
<!-- Notes section — optional but useful -->
## Notes
- Snapshot taken: [date and time]
- Page URL: [URL]
- Auth state: [logged in / guest]
- Special state: [e.g., "modal was open", "after search query 'BTC'"]
