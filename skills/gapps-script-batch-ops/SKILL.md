---
name: gapps-script-batch-ops
description: Google Apps Script performance and quota patterns for Sheets automation — batch reads/writes, parallel HTTP, trigger design, and Cloud Logging. Use when writing Apps Script code for Google Sheets, hitting 6-minute execution limits, needing to process large datasets inside Sheets, or scheduling automated Workspace tasks. Triggers on: "Apps Script", "google apps script", "SpreadsheetApp", "getValues", "setValues", "onEdit trigger", "time-driven trigger", "apps script quota", "batch update sheets script".
---

# Google Apps Script — Batch Operations & Performance

The single biggest source of slow or quota-busting Apps Script: reading or writing cells one at a time inside a loop. Fix: batch everything.

## The Golden Rule — Never Read/Write in a Loop

```javascript
// ❌ Slow — one API call per cell (O(n) roundtrips to Sheets)
const sheet = SpreadsheetApp.getActiveSheet();
for (let row = 2; row <= 1000; row++) {
  const val = sheet.getRange(row, 1).getValue();   // 1 call per row
  sheet.getRange(row, 2).setValue(val * 1.1);       // 1 call per row
}
// 2000 API calls → hits execution time limit fast

// ✓ Fast — two API calls total, regardless of row count
const sheet = SpreadsheetApp.getActiveSheet();
const data = sheet.getRange(2, 1, 999, 1).getValues();   // 1 call — 2D array
const updated = data.map(([price]) => [price * 1.1]);
sheet.getRange(2, 2, updated.length, 1).setValues(updated); // 1 call
```

## `getValues()` / `setValues()` Patterns

```javascript
// Read entire used range
const sheet = SpreadsheetApp.getActiveSheet();
const [headers, ...rows] = sheet.getDataRange().getValues();
// headers = ['Name', 'Email', 'Status', ...]
// rows = [['Alice', 'alice@...', 'Active'], ...]

// Write back modified rows (same dimensions required)
sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);

// Append rows efficiently
const newRows = [['Bob', 'bob@...', 'Pending'], ['Carol', 'carol@...', 'Active']];
sheet.getRange(sheet.getLastRow() + 1, 1, newRows.length, newRows[0].length)
     .setValues(newRows);
```

## `flush()` — Call Once, Not in Loops

```javascript
// ❌ flush() after every write defeats batching
for (const row of updates) {
  sheet.getRange(...).setValues([row]);
  SpreadsheetApp.flush();   // forces sync on each iteration
}

// ✓ Accumulate all writes, then flush once at the end (or not at all —
//   the script auto-flushes on exit)
const pending = updates.map(row => [/* transformed */row]);
sheet.getRange(2, 1, pending.length, pending[0].length).setValues(pending);
SpreadsheetApp.flush();   // only if you need the changes visible immediately
                           // (e.g., before a sleep or a subsequent read in the same run)
```

## Parallel HTTP with `fetchAll()`

```javascript
// ❌ Sequential — each fetch waits for the previous
for (const id of orderIds) {
  const resp = UrlFetchApp.fetch(`https://api.example.com/orders/${id}`);
  results.push(JSON.parse(resp.getContentText()));
}

// ✓ Parallel — all requests fire at once; Apps Script collects responses
const requests = orderIds.map(id => ({
  url: `https://api.example.com/orders/${id}`,
  method: 'get',
  headers: { Authorization: `Bearer ${getToken()}` },
  muteHttpExceptions: true,   // don't throw on 4xx/5xx — handle per-response
}));

const responses = UrlFetchApp.fetchAll(requests);

const results = responses.map((resp, i) => {
  if (resp.getResponseCode() !== 200) {
    console.error(`Order ${orderIds[i]} failed: ${resp.getResponseCode()}`);
    return null;
  }
  return JSON.parse(resp.getContentText());
}).filter(Boolean);
```

## Quota Awareness

| Limit | Consumer Google account | Google Workspace |
|---|---|---|
| Script runtime | 6 min / execution | 6 min / execution |
| Custom function runtime (`=MYFUNC()` in a cell) | 30 sec / execution | 30 sec / execution |
| Triggers total runtime | 90 min / day | 6 hr / day |
| Triggers | 20 / user / script | 20 / user / script |
| Simultaneous executions | 30 / user | 30 / user |
| `UrlFetchApp.fetch` calls | 20,000 / day | 100,000 / day |
| Email recipients via `MailApp` | 100 / day | 1,500 / day |
| Properties read/write | 50,000 / day | 500,000 / day |
| Spreadsheets created | 250 / day | 3,200 / day |
| Spreadsheet read/write calls | No published daily cap; batching is what keeps you under the 6-min runtime | Same |

Source: https://developers.google.com/apps-script/guides/services/quotas (values can change — re-check before relying on an exact number). Note the chunk-by-trigger pattern below spends **Triggers total runtime** (90 min/day on consumer accounts), and each chunk's `PropertiesService` cursor read/write counts toward the Properties quota.

When a script approaches 6 minutes, break work across multiple time-driven trigger runs using `PropertiesService` as a cursor:

```javascript
function processInChunks() {
  const props = PropertiesService.getScriptProperties();
  const startRow = parseInt(props.getProperty('cursor') || '2');
  const CHUNK_SIZE = 200;

  const sheet = SpreadsheetApp.getActiveSheet();
  const chunk = sheet.getRange(startRow, 1, CHUNK_SIZE, sheet.getLastColumn()).getValues();

  // ... process chunk ...

  const nextRow = startRow + CHUNK_SIZE;
  if (nextRow <= sheet.getLastRow()) {
    props.setProperty('cursor', String(nextRow));   // resume next trigger fire
  } else {
    props.deleteProperty('cursor');                  // done — clear cursor
  }
}
```

## Triggers

```javascript
// Time-driven trigger — created programmatically (preferred over manual setup)
function createDailyTrigger() {
  // Remove existing to avoid duplicates
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'processInChunks')
    .forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger('processInChunks')
    .timeBased()
    .everyHours(1)
    .create();
}

// onEdit — simple trigger, fires on a USER's cell edit in the spreadsheet
function onEdit(e) {
  if (e.range.getSheet().getName() !== 'Orders') return;
  if (e.range.getColumn() !== 3) return;   // only column C
  // handle the edit
}
```

### Simple-trigger limits (`onEdit`, `onOpen`, …)
From https://developers.google.com/apps-script/guides/triggers:
- "They can't run for longer than 30 seconds." — keep `onEdit` tiny; push heavy work to a time-driven trigger.
- "They can't access services that require authorization" (e.g. can't send email). Need `MailApp`/`UrlFetchApp`? Create an **installable** edit trigger: `ScriptApp.newTrigger('handleEdit').forSpreadsheet(SpreadsheetApp.getActive()).onEdit().create()`.
- "Script executions and API requests don't cause triggers to run. For example, calling Range.setValue() to edit a cell does not cause the spreadsheet's onEdit trigger to run." — so writes from a Python Sheets API script or another Apps Script function will NOT fire `onEdit`; don't build a pipeline that relies on it.

## Cloud Logging for Debugging

```javascript
// console.log() → appears in Cloud Logging (Executions panel in Apps Script editor)
function syncOrders() {
  const startTime = Date.now();
  const runId = Utilities.getUuid();

  try {
    console.log(`[${runId}] syncOrders started`);
    const rows = fetchAndTransform();
    console.log(`[${runId}] Fetched ${rows.length} rows in ${Date.now() - startTime}ms`);
    writeToSheet(rows);
    console.log(`[${runId}] Done. Total: ${Date.now() - startTime}ms`);
  } catch (err) {
    console.error(`[${runId}] FAILED at ${Date.now() - startTime}ms: ${err.message}`);
    throw err;   // re-throw so the trigger marks the run as failed
  }
}
```

## Template — Minimal Safe Script

```javascript
/**
 * Entry point — run manually or via time-driven trigger.
 * Reads column A, doubles values, writes to column B.
 */
function main() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Data');
  if (!sheet) throw new Error('Sheet "Data" not found');

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) { console.log('No data rows'); return; }

  const values = sheet.getRange(2, 1, lastRow - 1, 1).getValues();     // read once
  const output = values.map(([v]) => [typeof v === 'number' ? v * 2 : v]);
  sheet.getRange(2, 2, output.length, 1).setValues(output);             // write once

  console.log(`Processed ${output.length} rows`);
}
```

## Sources
- https://developers.google.com/apps-script/guides/sheets — Official Apps Script Sheets guide
- https://folderpal.io/articles/google-apps-script-quotas-and-workarounds-2026-breaking-limits-on-drive-automation — Quota workarounds 2026
- https://dev.to/googleworkspace/automate-your-google-workspace-with-apps-script-triggers-5090 — Triggers guide
- https://geekjob.medium.com/mastering-google-apps-script-718702d893ba — Advanced Apps Script techniques
