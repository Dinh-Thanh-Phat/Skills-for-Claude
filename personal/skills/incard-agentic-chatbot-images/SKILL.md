---
name: incard-agentic-chatbot-images
description: >-
  Set up or fix how an InCard Agentic AI sales chatbot sends PRODUCT IMAGES
  (agentic.incard.biz prod / agentic-stage.incard.biz staging). Use this whenever
  the task involves an InCard Agentic / "Agentic AI Platform" chatbot and images:
  the bot sends the WRONG image, sends too many images, sends a broken image, shows
  a raw image LINK/markdown on Facebook/Zalo, needs its Google-Drive product images
  (re)trained, needs a new sales bot built with an image catalog, or needs the
  instructions edited so images match the customer's question. Triggers on mentions
  of: "agentic", "InCard chatbot", "NARENCA", "gửi ảnh sai", "gửi nhiều ảnh",
  "train image / product media", "enable_image_reply", "chatbot gửi link ảnh",
  a chatbot-kb-images S3 URL, or a Drive folder of product photos for a chatbot.
  Prefer this skill over ad-hoc browser poking for any of those.
compatibility: >-
  Needs the Playwright MCP browser tools to drive the dashboard, and (for image
  verification) a local Google token at C:\Users\wi\.google-docs-token.json plus
  Python. Vietnamese sales-bot context assumed but not required.
---

# InCard Agentic chatbot — product image sending

InCard Agentic AI ("All-in-one Agentic AI Platform") lets a sales chatbot attach
product photos to answers. The photos live in a Google Drive folder and are
"trained" (uploaded to S3 + indexed) per bot. Getting the **right one** image to
show for a given customer question is where things break. This skill captures the
whole loop: how images are chosen, how to fix wrong/duplicate/broken images, and
how to verify it in the live preview.

Two environments, same UI: **prod** `https://agentic.incard.biz`, **staging**
`https://agentic-stage.incard.biz`. Log in at `/login`. Confirm which env + which
bot before editing — never guess credentials.

## The mental model (read first — most mistakes come from skipping this)

The bot matches images **by FILE NAME**, not by picture content. A file called
`IMG_3487.jpg` is invisible to matching; `QDC hành chính 30cm Tiếng Việt gọng nhựa đế gỗ.png`
matches a customer asking for exactly that. So **file naming is the real lever** —
prompt wording can steer the text reply, but it can only pick among the filenames
that exist.

There are **two delivery mechanisms**, and picking the right one is the single most
important decision. They behave differently per channel:

| | Auto-attach (`enable_image_reply` = ON) | Bot self-inserts markdown `![name](s3_url)` (`enable_image_reply` = OFF) |
|---|---|---|
| Who picks the image | Platform, top-K by filename similarity | The LLM, from a link table you put in the instructions |
| Count control | Historically **hard-coded top-3** → drags in wrong "neighbour" variants; a **top-K fix exists on staging** (may not be on prod yet) | Exactly what the LLM emits (usually 1; multiple only when the customer asks for several) |
| Web widget | Renders images | Renders markdown as images |
| **Facebook / Zalo / Messenger** | **Correct** — sent as real attachments, no stray text | **BROKEN** — the raw `![...](https://…)` text is shown to the customer (the channel doesn't render markdown) |

**Decision rule:**
- Bot deployed to **Facebook / Zalo / Messenger** → use **auto-attach** (ON), and rely
  on filenames + the top-K fix. Never use the markdown-link approach there.
- **Web-widget only**, and the platform still forces top-3 (no top-K fix) → the
  **markdown-link** approach gives exact 1-image control. See `references/markdown-link-mode.md`.
- Staging with the top-K fix → **auto-attach is the clean default** everywhere.

If a user reports "it sends the link on Facebook", they are on the markdown approach
on a non-web channel — switch that bot to auto-attach.

## Navigating the dashboard

- Bots list: `/dashboard/chatbot`. Each bot is a `.lqd-card` with an `h3` title and a
  "Chatbot Options" link that opens an Alpine dropdown: **Edit / Customize / Train /
  Test & Embed / Channel** (these call `setActiveChatbot(id, step)`; step 1=Configure,
  3=Train). The dropdown link may need two clicks to open; click the visible
  `a:text-is("Edit")` after it opens.
- The editor is `.lqd-chatbot-edit-window` (a full-screen overlay). Key fields
  (`name=` attributes): `title`, `bubble_message`, `welcome_message`,
  `instructions` (textarea), and checkboxes `enable_image_reply`,
  `do_not_go_beyond_instructions`.
- **Saving**: on the Configure step click the visible **"Next"** button — it fires
  `POST /dashboard/chatbot/update` (watch for a 200). Then reload and re-open Edit to
  confirm the value persisted; the overlay silently drops unsaved edits when the
  browser tab resets.
- The **internal numeric bot id** (e.g. `276`) is what the training APIs use; the
  **preview UUID** (`/chatbot/<uuid>/preview`) is different. Grab the numeric id from a
  network request such as `train/gdrive-image/list?id=276`.

### Writing large instructions safely
The instructions textarea is big (20–30 KB, Vietnamese). Set it via
`browser_evaluate` using the native value setter so Alpine sees the change:
```js
const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
setter.call(ta, newText); ta.dispatchEvent(new Event('input',{bubbles:true}));
ta.dispatchEvent(new Event('change',{bubbles:true}));
```
Prefer **in-page string surgery** (find/replace on `ta.value`) over pasting the whole
doc — smaller, and avoids escaping unicode. When you must inject a big block fresh,
**write it to a local UTF-8 file first, then load that file inside the browser step**
(e.g. a Playwright code step that reads the file with Node `fs` and passes the string as
the `page.evaluate` argument to the setter above). Do NOT push a base64 blob through your
own token stream — see memory `lesson_no-base64-obfuscation-for-injection`.

## Instructions structure (the catalog approach)

Whichever mechanism, the instructions should carry a **filename catalog** so the LLM
understands the product line and names the exact variant in its reply (which also
helps auto-attach rank the right file). A proven structure:

- **5.A Cơ chế** — one short paragraph on how images get sent for THIS bot (auto-attach
  vs markdown). For Facebook bots, add: *"TUYỆT ĐỐI KHÔNG in link/URL/markdown ![]() ra
  câu trả lời — chỉ mô tả sản phẩm, hệ thống tự đính ảnh."*
- **5.B Danh mục tên file** — every product grouped by variant, listing the exact
  filenames, **with explicit warnings for names that collide** (e.g. an LED photo
  historically named like a plain "hành chính" photo — call it out so the bot doesn't
  cross-match).
- **5.C Sản phẩm KHÔNG có ảnh** — list products with no photo (maps, books, a
  language variant that doesn't exist). Rule: describe in words + invite phone/Zalo,
  **never substitute a different product's image.**
- **5.D Quy tắc chọn file** — lock SIZE + TYPE + LANGUAGE + BASE before sending; ask ONE
  clarifying question when a distinguishing attribute is missing; state the full variant
  name verbatim in the reply.
- **5.E LINK ẢNH** — *only for markdown-link mode*: `filename => s3_url` for each image.
  Omit this entirely in auto-attach mode.

Explain the *why* in the prose (customers order the wrong SKU when the photo doesn't
match the words), rather than piling on ALL-CAPS MUSTs.

## Training / re-training the Drive images

Train tab → **Google Drive → Product Media** → paste the public Drive folder URL →
**Scan Folder**. Then **Select All → "Train GPT (N images)"**. Status flips
`not_embedded → success`. (`Documents` sub-tab is for PDFs/KB; `Product Media` is for
image/video matching.)

**Critical gotcha — renaming on Drive does NOT propagate.** The platform keys each
record on `gdrive_file_id`; a rescan sees the same id and **skips it, keeping the old
name**. To actually change a trained filename:
1. **Delete** the stale record in the Product Media list (per-row Delete button →
   confirm the `"Delete this image?"` browser dialog).
2. **Scan Folder** again → the file reappears with its NEW name, status `not_embedded`.
3. **Select All → Train GPT** → back to `success`.

Renaming files on Drive (to fix name collisions) can be done via the Drive API with the
local token — see `scripts/drive_media.py rename`. The image Drive folder is **shared**,
so a rename affects both prod and staging bots that scan it.

**HEIC/HEIF files are silently skipped by Scan Folder** (measured 30/09/2026, bot 286:
99 Drive files → 88 records, the 11 missing were exactly the HEIF ones). iPhone photos are
often HEIF **even when named `.jpeg`** — check `mimeType` via the Drive API, not the
extension. Convert them to real JPG on Drive before scanning, or tell the user they won't be
sent. Scan also picks up `.mp4` (media_type=video); "Select All → Train" may only queue part
of the list per click — loop until the media-list API shows every record `success`.

**Expired plan = silent create failure** (prod, 30/09/2026, account thanhphat12tna234):
the editor still opens and accepts input, but a toast says "AI Sales Chatbot plan has
expired … Renew Plan" and Next sends no create/update request — no bot appears. Check for
that toast before blaming the script; renewing is the account owner's decision.

**Scan returns 0 records → read the scan POST response before retrying.** Prod 30/09/2026:
`POST /dashboard/chatbot/train/gdrive-image/scan` → 422 `Table
'agentic.incard.biz.ext_chatbot_gdrive_folders' doesn't exist` and the media-list API → 500.
The Product Media UI was live on prod but its DB migration was not — only InCard devs can
fix it. The UI shows no error; only the network response does.

**Creating a bot:** "Add New Chatbot" creates the record immediately (it shows in the list
with the typed title/instructions even if the Next-save POST never fires). After creating,
re-read `enable_image_reply` from the list; if it is false, reopen step 1, tick it, click
Next and confirm `POST /dashboard/chatbot/update` → 200. Re-running a create script must
reuse the bot with the same title instead of creating a duplicate.

**Multi-turn media bug — FIXED 30/09/2026 on prod; keep the multi-turn regression.**
Before the fix, only the FIRST image request in a chat got media; later requests said
"em gửi hình/video…" but attached nothing (0/7 on bots 286/287/353/354). Re-test 30/09/2026
16:33 on prod bot 353: 2nd/3rd image requests attached the correct media 6/6 (S40→NPK,
ảnh→video, request after a text turn). Keep multi-turn image cases in every suite; if it
comes back, report it as this regression, not as a wrong-image failure.

## Verifying in the preview (don't trust your eyes on thumbnails)

Open `/chatbot/<preview-uuid>/preview`, click the chat trigger, type a question, wait
~15s. Then read the last message and resolve what it actually sent:

```js
// inside browser_evaluate, page has an <iframe> for the widget
const d=document.querySelector('iframe').contentDocument;
const m=[...d.querySelectorAll('.lqd-ext-chatbot-window-conversation-message')].pop();
const imgs=[...m.querySelectorAll('img')].filter(i=>/s3-agentic/.test(i.src));
// report each: i.src (…/<botid>/<gdrive_file_id>.<ext>) and i.naturalWidth
```
- `naturalWidth === 0` ⇒ **broken image** (usually a stale record pointing at a
  replaced Drive file — re-embed it).
- Extract the `gdrive_file_id` from the S3 path and resolve it back to the real Drive
  filename to confirm the RIGHT variant was sent:
  `python scripts/drive_media.py id2name <id> [<id> …]`.
- The S3 URL shape is
  `https://s3-agentic-ggdrive-images.s3.ap-southeast-1.amazonaws.com/chatbot-kb-images/<botid>/<gdrive_file_id>.<ext>`.

Test a spread, not just the happy path: an exact variant (→ 1 correct image), an
ambiguous ask (→ bot asks back, 0 images), a no-photo product like a map (→ text only,
0 images), a bilingual query, and — since customers do this — an explicit "show me all
3 colours / compare both bases" (→ several *correct* images, each labelled). Resolve
every returned id; a picture that "looks right" in a thumbnail can be the wrong variant.

## The media-list API (source of truth)

`GET /dashboard/chatbot/train/gdrive-image/list?id=<botid>` (send header
`X-Requested-With: XMLHttpRequest`) returns `{ type, data:[ { db_id, gdrive_file_id,
file_name, s3_url, thumbnail_url, status } … ] }`. Use it to: audit which files are
trained, build the 5.E link table (`file_name => s3_url`), find stale/broken records,
and diff against the live Drive folder. Fetch it in-page with `fetch()` while on the
dashboard (cookies are sent automatically).

## Helper script

`scripts/drive_media.py` (uses the local Google token, auto-refreshes) does the
repetitive Drive lookups you'll otherwise rewrite every session:
- `id2name <fileId>…` — resolve S3/Drive file ids to filenames (verifying preview output)
- `list <folderId>` — recursive listing of a Drive image folder (name + id + mime).
  Limitation: one `files.list` call per folder (pageSize 1000), `nextPageToken` is not
  followed — a folder with >1000 items is silently truncated.
- `rename <fileId> "<new name>"` — fix a colliding filename on Drive (then delete
  record → rescan → train, per above)

Set the token path with `--token` (default `C:\Users\wi\.google-docs-token.json`).
Run with `PYTHONIOENCODING=utf-8` on Windows so Vietnamese names print.

## Common failures → fix

- **Wrong image alongside the right one** → auto-attach top-3 dragging in a
  name-neighbour; fix the colliding filename (rename → delete record → rescan → train),
  or switch to markdown-link mode on web, or use the staging top-K fix.
- **Correct image not even in the top-3** → same top-K limitation; markdown-link mode or
  the staging fix.
- **Raw `![...](url)` shown to customer** → markdown mode on Facebook/Zalo; switch that
  bot to auto-attach and strip link output from the instructions.
- **Raw `*asterisks*` / `**bold**` shown to customer** → Facebook/Zalo render NO markdown
  at all, not just images. Instruct the bot to reply in PLAIN TEXT only: no `**bold**`,
  no `*italic*`, no `#`/`_`/`` ` ``. List items = each on its own line, plain words. Same
  root cause as the image-link leak — any markdown syntax leaks as literal characters on
  these channels.
- **Bot answers a "xin link / đặt online" request with only an image + no link** →
  an over-broad "don't print links" rule (added to stop image-link leaks) also suppressed
  legitimate PRODUCT-PAGE links. Split the rule: ban image-file URLs + markdown image
  syntax, but explicitly ALLOW plain product-page URLs (narenca.com.vn/…) when the
  customer asks for a link, and make providing that link the turn's top priority.
- **Link request also auto-attaches an image (customer wanted link only)** → with
  `enable_image_reply` ON, the platform attaches an image on ANY turn where the
  product/variant is named (it can't tell "wants link" from "wants image", and likely
  keys off the customer's query, which already names the product). Instructions can nudge
  ("on pure link requests, keep it link-focused") but CANNOT reliably suppress the attach.
  A true per-intent toggle (link→no image, "cho xem ảnh"→image) is platform-side — needs
  InCard to expose per-turn image control. Set this expectation with the user rather than
  promising an instruction-only fix.
- **Broken/blank image (`naturalWidth=0`)** → stale record; delete + rescan + retrain.
- **Bot sends a globe photo for a "map" question** → no map images exist; instructions
  5.C must forbid substituting, and the bot should describe in words and offer to have a
  human send the real photo (collect phone/Zalo) instead of attaching anything.

## Deeper references
- `references/markdown-link-mode.md` — full recipe for the self-inserted-link approach
  (web-only exact-1-image control): building the 5.E table, the 5.A wording, and the
  render test to run before committing to it.