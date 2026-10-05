# Worked Example

A full run from a one-line request to a filed ticket, showing what each step produces.

## The request

> "Log a bug for HVS on Odoo — the date filter on the bookings page shows wrong results."

The user gave a symptom and a project name. Everything else is context this skill fills in.

## Step 1 — Resolve

- `registry.md` → slug `hvs`, disk `D:\HK8\Learning\DQ\HVS`, stack Playwright + TypeScript.
- Read `knowledge/hvs.md` and `memories/hvs/` → note any existing date-filter issues and the Odoo project name HVS maps to.

## Step 2 — Flow (disk)

Dispatch Explore against `D:\HK8\Learning\DQ\HVS`:

> "Find how the bookings page date filter is implemented — the component, the route, where the filter query is built, and the expected filtering behavior. Return file:line anchors."

Result: route `/bookings`, filter built in `BookingsFilter.tsx:88`, query param `?from=&to=`, expected to filter inclusive of both endpoints.

## Step 3 — Odoo

- `search_records` `project.project` ilike "HVS" → project + id.
- Stages via `project.task.type` → e.g. BACKLOG / TODO / IN PROGRESS / DONE with ids.
- Assignees + tags the project actually uses.
- **Dedup:** `search_records` `project.task` in this project for "date filter" / "bookings filter" → none open. Confirmed new.

## Step 4 — Bug detail (isolated + reproducible)

- **Steps:** 1) Go to `/bookings` 2) Set From = 2026-06-01, To = 2026-06-01 3) Apply.
- **Expected:** bookings on 2026-06-01 are shown (endpoints inclusive — per `BookingsFilter.tsx:88`).
- **Actual:** zero results; same-day range returns nothing.
- **Isolation:** changed only the To date (06-01 → 06-02) as a control → results appear → the bug is the inclusive-end boundary, not the From date. One variable changed.
- **Technical context:** `page_url=/bookings`, `element_selector` of the To input, `network_request: GET /api/bookings?from=2026-06-01&to=2026-06-01 → []`.
- **Visual:** screenshot of the empty grid, viewed at native resolution.

## Step 5 — Hand off

Invoke `odoo-project-automation` with: project HVS, type `bug`, English title "Bookings date filter excludes same-day range (end date not inclusive)", the steps/expected/actual + technical context, tag `bug`, target stage. Show the user: *"New bug (no existing match), HVS project, BACKLOG stage, root cause isolated to inclusive-end boundary."* Confirm → created.

## Step 6 — Write back

Append to `knowledge/hvs.md`: "Bookings filter end-date is exclusive in API — boundary bug class to watch." Faster next time.
