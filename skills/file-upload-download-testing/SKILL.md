---
name: file-upload-download-testing
description: Patterns for testing file upload and download UI in Playwright — setInputFiles, drag-and-drop, custom dropzones, upload-relationship/drawer fields (PayloadCMS/Strapi), FSA API workaround, download verification. Use when writing tests for any file upload feature (profile pictures, document import, CSV upload, CMS image/logo fields) or file download (export, report download). Triggers on: "file upload", "setInputFiles", "drag and drop", "file download", "export CSV", "download button", "input type file", "React Dropzone", "file chooser", "filechooser event", "upload field", "image field", "logo upload", "avatar upload", "image cropper", "media drawer", "PayloadCMS upload", "Create New media", "upload inside iframe", "Cloudinary widget", "S3 presigned upload", "inline image editor", "broken image check", "DataTransfer drop".
---

# File Upload & Download Testing

## Upload Patterns

### 1. Standard `<input type="file">` — target the input directly
```typescript
// ✅ Always find the underlying <input type="file">, even if hidden
const fileInput = page.locator('input[type="file"]');
await fileInput.setInputFiles('tests/fixtures/sample.csv');

// ✅ Virtual file — no actual file needed on disk
await fileInput.setInputFiles({
  name: 'test-data.csv',
  mimeType: 'text/csv',
  buffer: Buffer.from('id,name,email\n1,Alice,alice@example.com\n2,Bob,bob@example.com'),
});

// Assert filename displayed after upload
await expect(page.getByText('test-data.csv')).toBeVisible();
```

### 2. Hidden input (styled upload button)
```typescript
// Most styled upload buttons hide the real <input type="file"> via CSS
// ✅ Target the hidden input directly — setInputFiles works on hidden inputs as-is
// (there is NO `force` option; setInputFiles only accepts timeout / signal / noWaitAfter)
const hiddenInput = page.locator('input[type="file"]');
await hiddenInput.setInputFiles('path/to/document.pdf');

await expect(page.getByText('document.pdf')).toBeVisible();
```

### 3. Drag-and-drop dropzone (React Dropzone, custom)
```typescript
// ✅ Use locator.drop() for external file drag-and-drop (Playwright v1.60+, cross-browser)
// Payload is an OBJECT: files = path | path[] | {name,mimeType,buffer} | array of those
const dropzone = page.getByTestId('upload-dropzone');
await dropzone.drop({ files: 'tests/fixtures/image.png' });
// virtual file:
// await dropzone.drop({ files: { name: 'note.txt', mimeType: 'text/plain', buffer: Buffer.from('hello') } });
// clipboard-like data: await dropzone.drop({ data: { 'text/plain': 'hello' } });

// Verify upload succeeded
await expect(page.getByText('image.png')).toBeVisible();
await expect(page.getByText('Upload complete')).toBeVisible();
```

### 4. File validation UI — size and type errors
```typescript
// Test file size validation
await fileInput.setInputFiles({
  name: 'huge-file.zip',
  mimeType: 'application/zip',
  buffer: Buffer.alloc(20 * 1024 * 1024), // 20MB virtual file
});
await expect(page.getByText('File too large. Max 10MB')).toBeVisible();

// Test file type validation
await fileInput.setInputFiles({
  name: 'script.exe',
  mimeType: 'application/octet-stream',
  buffer: Buffer.from('fake exe content'),
});
await expect(page.getByText('Unsupported file type')).toBeVisible();
```

### 5. Progress indicator
```typescript
// Simulate slow upload to test progress bar
await page.route('**/api/upload', async route => {
  await new Promise(r => setTimeout(r, 1000));
  await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
});
await fileInput.setInputFiles('tests/fixtures/large.pdf');
await expect(page.getByRole('progressbar')).toBeVisible();
await expect(page.getByText('Upload complete')).toBeVisible({ timeout: 5000 });
```

### 6. Upload-relationship field (PayloadCMS / drawer-based CMS)

Some CMSs (PayloadCMS, Strapi, KeystoneJS) render an "image"/"logo"/"file" field as a
**relationship to a media collection**, NOT a raw `<input type="file">`. The field on the
edit page shows buttons like **"Create New"** / **"Choose from existing"** / a drag zone —
there is **no usable file input in that field's markup**. `setInputFiles` on the page's
first `input[type="file"]` silently does nothing → the field saves as `null`.

```typescript
// ❌ WRONG — no file input in the upload-relationship field; saves null
await page.locator('input[type="file"]').first().setInputFiles({ name: 'logo.png', ... });

// ✅ CORRECT — open the media drawer, upload INSIDE it, then save the drawer
const field = page.locator('#field-logo');              // the upload-relationship field
await field.getByRole('button', { name: /Create New/i }).click();

const drawer = page.locator('.drawer__content, [role="dialog"]').last();
await drawer.waitFor({ state: 'visible' });

// the REAL file input lives inside the drawer's media-create form
await drawer.locator('input[type="file"]').setInputFiles({
  name: 'logo.png', mimeType: 'image/png', buffer: PNG_BUFFER,
});

// media collection usually requires Alt text — fill required drawer fields
const alt = drawer.getByRole('textbox', { name: /Alt/i }).first();
if (await alt.isVisible().catch(() => false)) await alt.fill('logo alt');

await drawer.getByRole('button', { name: /^Save\b/i }).first().click();  // saves the media
// drawer closes; field now shows a thumbnail. Then save the PARENT record.
await page.getByRole('button', { name: /^Save\b/i }).first().click();
```

Alternative — **"Choose from existing"** picks an already-uploaded media (no new file,
nothing to clean up afterwards):
```typescript
await field.getByRole('button', { name: /Choose from existing/i }).click();
const drawer = page.locator('[role="dialog"]').last();
await drawer.getByRole('row').nth(1).click();   // pick first media row
```

**Always verify persistence via API** — a thumbnail showing in the UI is not proof:
```typescript
const r = await page.request.get(`${API}/tech-stack/${id}?depth=1`, { headers });
expect((await r.json()).logo, 'upload-relationship persisted').toBeTruthy();
```

**Cleanup note:** "Create New" creates a real media record. Capture its id
(`json.logo.id`) and report/delete it — otherwise it leaks into the media collection.

## Advanced Upload Patterns

### 7. `filechooser` event — no accessible input in the DOM

When a button opens the native OS file dialog and there is genuinely no `<input type="file">`
you can reach (e.g. `window.showOpenFilePicker`, some web components):
```typescript
// ✅ Promise.all so the listener is armed BEFORE the click
const [fileChooser] = await Promise.all([
  page.waitForEvent('filechooser'),
  page.getByRole('button', { name: 'Upload' }).click(),
]);
if (fileChooser.isMultiple()) {
  await fileChooser.setFiles(['tests/fixtures/a.png', 'tests/fixtures/b.png']);
} else {
  await fileChooser.setFiles('tests/fixtures/a.png');
}
```
Note: `filechooser` does NOT fire for `window.showOpenFilePicker` (FSA API) — see the FSA
section below for that case.

### 8. Pure drag-and-drop dropzone — listens to `drop` only, no hidden input

Fallback only for Playwright < 1.60 (no `locator.drop()`), or when `drop()` and
`input[type=file]` both fail — build a `DataTransfer` and dispatch:
```typescript
const dataTransfer = await page.evaluateHandle(async () => {
  const dt = new DataTransfer();
  const res = await fetch('data:image/png;base64,iVBORw0KGgo...'); // or a real URL
  const blob = await res.blob();
  dt.items.add(new File([blob], 'image.png', { type: 'image/png' }));
  return dt;
});
await page.dispatchEvent('#dropzone', 'drop', { dataTransfer });
await expect(page.getByText('image.png')).toBeVisible();
```
Limitation: creating `DataTransfer` this way only works in Chromium and Firefox, not WebKit.
On 1.60+ prefer `locator.drop()`, which works cross-browser.

### 9. Rich-text editor inline image (Lexical / Slate / TipTap / CKEditor)

The image button opens either a file dialog or an upload drawer/modal:
```typescript
await page.getByRole('button', { name: /Insert image|Image/i }).click();
// Case A: modal with a file input
const modal = page.locator('[role="dialog"]').last();
await modal.locator('input[type="file"]').setInputFiles({ name: 'inline.png', mimeType: 'image/png', buffer: PNG });
await modal.getByRole('button', { name: /Insert|Upload|Add/i }).click();
// Verify the <img> landed inside the editor content area
await expect(page.locator('.editor-content img, [contenteditable] img')).toBeVisible();
```

### 10. Image cropper modal (avatar / profile picture)

Upload → crop modal opens → confirm. The cropped result is what actually persists:
```typescript
await page.locator('input[type="file"]').setInputFiles('tests/fixtures/avatar.jpg');
const cropper = page.locator('[role="dialog"]:has(.cropper-container), .crop-modal').last();
await cropper.waitFor({ state: 'visible' });
// optional: drag the crop box / zoom slider before confirming
await cropper.getByRole('button', { name: /Crop|Save|Apply|Confirm/i }).click();
await cropper.waitFor({ state: 'hidden' });
// verify the avatar image src updated (not the old/default one)
await expect(page.locator('img.avatar')).not.toHaveAttribute('src', /default|placeholder/);
```

### 11. Multiple files into one field/drawer

```typescript
// Standard multi-input
await page.locator('input[type="file"]').setInputFiles([
  'tests/fixtures/a.png', 'tests/fixtures/b.png', 'tests/fixtures/c.png',
]);
await expect(page.getByText('3 files selected')).toBeVisible();

// CMS bulk-upload drawer — one setInputFiles call with an array, then save each
const drawer = page.locator('[role="dialog"]').last();
await drawer.locator('input[type="file"]').setInputFiles(['tests/fixtures/a.png', 'tests/fixtures/b.png']);
```

### 12. iframe-embedded uploader (Cloudinary / Uploadcare / Filestack widgets)

```typescript
const frame = page.frameLocator('iframe[src*="cloudinary"], iframe.upload-widget');
await frame.locator('input[type="file"]').setInputFiles('tests/fixtures/photo.jpg');
// wait for a real UI signal INSIDE the frame, not just the iframe element
await expect(frame.getByText(/Upload complete|Done/i)).toBeVisible();
```
If the widget hides its input, combine with the `filechooser` event (§7) — arm
`page.waitForEvent('filechooser')` then click the widget's button.

### 13. Direct-to-S3 presigned URL upload

Browser does `PUT` straight to S3 after fetching a presigned URL from your API. In tests
you usually don't want a real S3 round-trip — intercept the `PUT`:
```typescript
// Let the presigned-URL request through, stub the actual S3 PUT
await page.route(/s3[.-].*amazonaws\.com/, route =>
  route.fulfill({ status: 200, headers: { ETag: '"mock-etag"' } })
);
await page.locator('input[type="file"]').setInputFiles('tests/fixtures/big.pdf');
await expect(page.getByText('Upload complete')).toBeVisible();
```
For a true end-to-end test, let it hit S3 and assert on the final record's stored URL.

### 14. Replace / remove an already-uploaded file

```typescript
// Replace: most UIs let you setInputFiles again on the same input
await page.locator('input[type="file"]').setInputFiles('tests/fixtures/new.png');
await expect(page.getByText('new.png')).toBeVisible();
await expect(page.getByText('old.png')).toHaveCount(0);

// Remove: explicit clear, then assert empty state
await page.getByRole('button', { name: /Remove|Delete file|✕/i }).click();
await expect(page.getByText(/No file|Drag and drop/i)).toBeVisible();
// programmatic clear of an input: setInputFiles([])
await page.locator('input[type="file"]').setInputFiles([]);
```

### 15. Verify the image actually rendered (not a broken image)

A visible `<img>` element ≠ a loaded image. Check `naturalWidth`:
```typescript
const img = page.locator('img.uploaded-preview');
await expect(img).toBeVisible();
const ok = await img.evaluate((el: HTMLImageElement) => el.complete && el.naturalWidth > 0);
expect(ok, 'uploaded image actually loaded (not broken)').toBe(true);
```

### 16. `capture` attribute (camera / webcam input)

`<input type="file" accept="image/*" capture="environment">` still accepts `setInputFiles`
in automation — the `capture` hint is ignored by Playwright:
```typescript
await page.locator('input[capture]').setInputFiles({
  name: 'snapshot.jpg', mimeType: 'image/jpeg', buffer: JPG_BUFFER,
});
```

### 17. Paste-from-clipboard image (Ctrl+V into an editor)

```typescript
await page.locator('[contenteditable]').focus();
const dataTransfer = await page.evaluateHandle(async () => {
  const dt = new DataTransfer();
  const res = await fetch('data:image/png;base64,iVBORw0KGgo...');
  dt.items.add(new File([await res.blob()], 'pasted.png', { type: 'image/png' }));
  return dt;
});
await page.dispatchEvent('[contenteditable]', 'paste', { clipboardData: dataTransfer });
await expect(page.locator('[contenteditable] img')).toBeVisible();
```

### Known remaining edge cases (not covered here)

- **Resumable / chunked uploads** (tus protocol, Uppy, large-file multipart): assert on
  final completion + server record; chunk-level testing belongs in integration tests.
- **Native mobile app uploads**: use Appium/Maestro, not Playwright.

## Download Patterns

### 1. Capture download — always use Promise.all
```typescript
// ✅ CRITICAL: both promises must start in the SAME tick
const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.getByRole('button', { name: 'Export CSV' }).click(),
]);

// Save before it expires
await download.saveAs('test-results/export.csv');

// Assert filename
expect(download.suggestedFilename()).toContain('export');

// Assert content
const fs = require('fs');
const content = fs.readFileSync('test-results/export.csv', 'utf8');
expect(content).toContain('id,name,email');
expect(content.split('\n').length).toBeGreaterThan(1);
```

### 2. Download from link
```typescript
const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.getByRole('link', { name: 'Download Report' }).click(),
]);
const path = `test-results/${download.suggestedFilename()}`;
await download.saveAs(path);
expect(download.suggestedFilename()).toMatch(/report.*\.pdf/i);
```

## File System Access API (modern Chrome)

The FSA API bypasses `page.on('filechooser')` entirely. If `setInputFiles` doesn't work:

```typescript
// Option 1: Disable FSA in app config for test environment
// <Dropzone useFsAccessApi={false}> or environment flag

// Option 2: Intercept at network layer after upload completes
await page.route('**/api/upload', route =>
  route.fulfill({ status: 200, body: JSON.stringify({ url: '/files/test.pdf' }) })
);
```

## Gotchas

| Gotcha | Fix |
|---|---|
| `setInputFiles` on styled button element | Always locate `input[type="file"]` directly — works even if hidden (no `force` option exists) |
| `page.on('filechooser')` never fires | App uses File System Access API — disable it in test config |
| Download race condition: click then waitForEvent | Always `Promise.all([waitForEvent, click])` — both start together |
| `suggestedFilename()` ≠ saved file path | They're different values — don't mix them up |
| `locator.drop()` not available | Requires Playwright v1.60+ — update, or use the `DataTransfer` fallback (Pattern 8) |
| CMS image/logo field saves `null` after `setInputFiles` | It's an upload-RELATIONSHIP field — open the "Create New" drawer and upload inside it (see Pattern 6) |
| Drawer's Save does nothing | Media collection has required fields (Alt) — fill them before Save |
| `filechooser` event never fires | App uses FSA API (`showOpenFilePicker`) — `filechooser` does not cover it; disable FSA in test config |
| `DataTransfer` drop fails in Safari/WebKit | Use `locator.drop()` (1.60+, cross-browser); manual `DataTransfer` works only in Chromium + Firefox |
| iframe widget upload "not found" | Use `page.frameLocator(...)` and wait for a UI signal INSIDE the frame, not the iframe tag |
| `<img>` visible but image is broken | Visibility ≠ loaded — assert `complete && naturalWidth > 0` (see Pattern 15) |
| Cropper: original file persists, not the crop | Must confirm the crop modal; assert the final `src` changed (see Pattern 10) |

## Checklist

- [ ] Upload: targeting `input[type="file"]` directly (even hidden ones)
- [ ] Virtual file used in CI (no real file dependency on disk)
- [ ] Drag-and-drop: using `locator.drop({ files })` (1.60+), not manual `dispatchEvent`
- [ ] CMS image/logo field: used the "Create New" drawer pattern, verified persistence via API, captured created media id for cleanup
- [ ] No DOM input at all: `filechooser` event armed with `Promise.all` before the click
- [ ] Pure dropzone (no input): `locator.drop()`; only on < 1.60 fall back to `DataTransfer` + `dispatchEvent` (Chromium/Firefox)
- [ ] iframe widget: `frameLocator()` used, waited on a signal inside the frame
- [ ] Cropper / inline-editor image: confirmed the modal, asserted final result not the raw upload
- [ ] Image upload verified actually rendered (`naturalWidth > 0`), not just `<img>` visible
- [ ] Direct-to-S3: S3 `PUT` intercepted (or deliberately left live for true E2E)
- [ ] File size error and file type error tested as separate cases
- [ ] Download: `Promise.all([waitForEvent('download'), click()])` — never sequential
- [ ] Download content verified (not just filename)
- [ ] Upload progress indicator tested with route delay

