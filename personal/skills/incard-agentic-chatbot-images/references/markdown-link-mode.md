# Markdown-link image mode (web-widget only)

Use this **only** when the bot lives on the **web widget** and the platform still
forces top-3 auto-attach (no top-K fix), so you need exact 1-image control.
**Do NOT use on Facebook / Zalo / Messenger** — those channels show the raw
`![...](https://…)` text to the customer instead of rendering it. For those channels
use auto-attach (see SKILL.md).

## How it works
Turn `enable_image_reply` **OFF**. The bot then embeds an image itself by writing
Markdown `![tên biến thể](S3_URL)` in its reply. The web widget renders that as an
`<img>`. Because the LLM decides what to emit, you get exactly one image for a
specific ask, and several *correct* ones when the customer explicitly wants to
compare (all still labelled and matched).

## Verify the render FIRST (cheap gate)
Before building the whole link table, prove the widget renders bot-emitted markdown:
turn `enable_image_reply` OFF, add ONE temporary rule with one real S3 link and the
`![](url)` syntax, save, ask for it in preview, and check the last message has an
`<img>` with `naturalWidth > 0`. If it renders → build the full table. If the raw URL
shows as text → the widget/channel doesn't render markdown; abandon this mode.

## Build the 5.E link table from the API
Fetch the trained media in-page (on the dashboard, cookies auto-sent):
```js
const r = await fetch('/dashboard/chatbot/train/gdrive-image/list?id=<botid>',
                      {headers:{'X-Requested-With':'XMLHttpRequest'}});
const data = (await r.json()).data;
const imgs = data.filter(d => d.s3_url && /\.(jpg|jpeg|png|webp)$/i.test(d.file_name));
// emit "file_name => s3_url" lines, one per image (skip videos)
```
Insert as section **5.E — LINK ẢNH ĐỂ CHÈN** just before section 6. Videos (`.mp4`)
usually can't be embedded as markdown images, so leave them out — the bot describes
them or offers a human follow-up.

## The 5.A wording for this mode
> 5.A — Cơ chế gửi ảnh. Hệ thống KHÔNG tự đính ảnh. Muốn gửi ảnh, bot TỰ CHÈN link
> bằng cú pháp Markdown `![tên biến thể](LINK)`, LINK lấy NGUYÊN VĂN từ bảng 5.E —
> không sửa, không bịa, không tự ghép link. Mặc định mỗi lượt 1 ảnh của đúng biến thể;
> gửi nhiều ảnh chỉ khi khách chủ động xin (so sánh / xem cả bộ), mỗi ảnh gắn đúng
> nhãn. Biến thể không có link trong 5.E = không có ảnh → xử lý theo 5.C.

Also add a rule forbidding invented URLs: only paste links that exist verbatim in 5.E;
if unsure a link exists, don't send an image.

## Maintenance cost
The 5.E table hard-codes S3 URLs that are tied to `gdrive_file_id`s. **Any time images
are added / renamed / re-embedded, rebuild 5.E** from the media-list API (the ids
change on re-embed). This is the main downside vs auto-attach — flag it to the user.

## Migrating a bot OFF this mode (e.g. it went to Facebook)
1. Turn `enable_image_reply` back ON.
2. Rewrite 5.A to the auto-attach wording and add:
   *"TUYỆT ĐỐI KHÔNG in link/URL/markdown ![]() ra câu trả lời — chỉ mô tả sản phẩm,
   hệ thống tự đính ảnh."*
3. Delete the 5.E table (or leave the catalog 5.B; 5.E is what leaks links).
4. Save, then re-test on the actual channel — auto-attach count now depends on whether
   that environment has the top-K fix.
