---
name: demo-slide-builder
description: >
  Build a PowerPoint (.pptx) demo presentation from diverse inputs (text descriptions,
  screenshots, web links with/without login, PDF/docx files). Use this skill ONLY when
  the user explicitly says "tạo slide", "make slides", "create a presentation",
  "build a deck", or explicitly asks to use the demo-slide-builder skill.
  Do NOT trigger for unrelated tasks.
---

# Demo Slide Builder

Generate a professional internal demo `.pptx` from any combination of inputs.

## When to Trigger

Trigger ONLY when user explicitly says one of:
- "tạo slide", "tạo presentation", "tạo deck"
- "make slides", "create slides", "build slides"
- "create a presentation", "build a deck", "generate pptx"
- "dùng demo-slide-builder", "use demo-slide-builder"

## Step 1 — Gather Information

Ask (or infer from context) the following. Do not proceed until you have at least a title and one feature:

| Field | Ask if missing |
|---|---|
| **title** | "What's the title of this demo session?" |
| **date** | Default to today's date if not given |
| **team** | "Which team or project is this for?" |
| **features** | "List the features you want to demo" (or will be discovered from the web) |
| **next_steps** | Optional — "Any next steps to include?" |

---

## Step 2 — Process Each Input Type

### Text / Description
- Extract feature names: look for capitalized nouns, action verbs ("New dashboard", "Bulk import")
- Each feature → `name`, `description`, and 3–5 `bullets` (concrete capabilities, not vague filler)
- Keep bullets tight: what changed, what it does, who benefits

### Web Link (no login required)
- Use WebFetch to load the page
- Summarize into feature blocks: heading → `name`, key paragraphs → `bullets`
- Ignore nav, footers, cookie banners

### Web Link + Account (login required) — see Section A below
- Use Playwright browser automation to log in and explore
- Take screenshots of key pages/features
- Save screenshots locally and embed them in the matching feature slides

### Screenshot / Image (already provided by user)
- Describe the visible UI: layout, key elements, labels, data shown
- Map to the most relevant feature slide
- Set `image_path` to the file path (absolute) so the script can insert it

### PDF / DOCX File
- Read the file content
- Extract section headings → feature names
- Summarize each section into 3–5 bullets

---

## Section A — Web Automation with Login

Use this flow when the user provides a URL + username/password (or says "tự vào web", "login vào", "explore trang").

### A0. Set browser to full size FIRST (do this before anything else)

**Always do these 2 steps before the first navigate — and repeat the evaluate after EVERY navigate:**

```
# Step 1 — once at session start
mcp__plugin_playwright_playwright__browser_resize
  → width: 1440, height: 900

# Step 2 — after EVERY navigate (zoom + scroll to top)
mcp__plugin_playwright_playwright__browser_evaluate
  → () => { document.body.style.zoom = '0.85'; window.scrollTo(0, 0); }
  ⚠️ Use document.body NOT document.documentElement — body zoom is more reliable across frameworks

# Step 3 — wait for layout to settle
mcp__plugin_playwright_playwright__browser_wait_for
  → time: 1.5
```

**Why:**
- `browser_resize` sets the viewport to 1440×900 so the app renders in desktop mode
- `zoom: 0.85` fits more content into the screenshot without clipping edges
- Without these, the default viewport (~800×600) makes cards stack into 1 column and screenshots look tiny and unreadable

### A1. Open and log in

```
mcp__plugin_playwright_playwright__browser_navigate  → go to login URL
mcp__plugin_playwright_playwright__browser_snapshot  → read the login form
mcp__plugin_playwright_playwright__browser_fill_form → fill username + password fields
mcp__plugin_playwright_playwright__browser_click     → click login/submit button
mcp__plugin_playwright_playwright__browser_wait_for  → wait for dashboard/home to load
```

If the login form is unusual (2FA, captcha, OAuth redirect), stop and ask the user to complete login manually in the browser, then continue from the next step.

### A2. Explore features

After login, navigate to each feature area the user mentioned (or explore the main nav if features are not specified):

```
mcp__plugin_playwright_playwright__browser_navigate  → go to feature URL or click nav item
mcp__plugin_playwright_playwright__browser_snapshot  → read page structure, note key elements
mcp__plugin_playwright_playwright__browser_take_screenshot → capture the page
```

For each feature page, follow this **exact 5-step sequence** — no shortcuts:

```
# 1. Navigate
mcp__plugin_playwright_playwright__browser_navigate → feature URL

# 2. Apply zoom + scroll (MANDATORY after every navigate)
mcp__plugin_playwright_playwright__browser_evaluate
  → () => { document.body.style.zoom = '0.85'; window.scrollTo(0, 0); }   // body, same as A0

# 3. Wait for render
mcp__plugin_playwright_playwright__browser_wait_for → time: 1.5

# 4. (Optional) Snapshot to verify content loaded — skip if you already know the page
mcp__plugin_playwright_playwright__browser_snapshot → depth: 3

# 5. Take screenshot
mcp__plugin_playwright_playwright__browser_take_screenshot
  → filename: "slides_screenshots/<NN>_<feature_slug>.png"
```

> ⚠️ **Path constraint:** Playwright can only save inside the project directory. Always use a **relative path** (`slides_screenshots/...`). The JSON `image_path` must be the **absolute path**, e.g. `d:\HK8\Learning\DQ\phat\phat\slides_screenshots\01_cards_list.png`.

Ensure the output directory exists before the first screenshot:
```powershell
New-Item -ItemType Directory -Force -Path "slides_screenshots"
```

**Checklist before moving to the next feature:**
- [ ] `browser_resize` done once at session start (1440×900)
- [ ] `document.body.style.zoom = '0.85'` + `scrollTo(0,0)` applied after this navigate
- [ ] Scroll target section into view before screenshot (see below)
- [ ] Waited 1.5s for full render
- [ ] `Read` the PNG to visually confirm correct section is visible
- [ ] Screenshot saved to `slides_screenshots/` (NOT `C:\tmp\`)

**Scroll to target section before screenshot:**
```js
// When page has multiple sections, always scroll the specific section into view
await page.evaluate(`() => {
  const h = Array.from(document.querySelectorAll('h2,h3,h4'))
    .find(el => el.textContent.includes('Your Target Section'));
  if (h) h.scrollIntoView({ behavior: 'instant', block: 'start' });
}`);
```
Without this, the screenshot may capture a different section (e.g. Activities log instead of Your Plan).

Repeat for each feature. Cover all features the user listed. If no list given, cover the top 3–5 sections from the main nav.

### A3. Close browser and build slide data

After collecting all screenshots:
- Close the browser tab (optional, no harm if left open)
- Map each feature's screenshots and notes into the JSON payload
- Set `image_path` to the saved screenshot path for each feature

---

## Step 3 — Build the JSON Payload

Construct this structure. Every field is a string or array of strings.

```json
{
  "title": "Demo session title",
  "date": "2026-05-08",
  "team": "Team or project name",
  "agenda_sections": [
    {
      "title": "Section Label (e.g. User — Mua gói)",
      "items": [
        {
          "text": "Short action (3–6 words)",
          "desc": "1-line explanation of what will be shown"
        }
      ]
    }
  ],
  "features": [
    {
      "name": "Slide Title",
      "description": "One-sentence context shown under title",
      "bullets": ["Outcome-focused point 1", "Point 2", "Point 3", "Point 4"],
      "image_path": "d:\\HK8\\Learning\\DQ\\phat\\phat\\slides_screenshots\\sNN_feature.png"
    }
  ],
  "next_steps": ["Action item 1", "Action item 2"]
}
```

**`agenda_sections`** drives the Agenda slide. If omitted, feature names are used as a flat list.

Rules:
- `bullets`: 3–5 items per feature (script keeps only the first 5), outcome-focused not a feature checkbox list — ≤ 15 words each
- `image_path`: absolute path to saved screenshot, or **`null`** for text-only slides (admin/backend pages with no UI to capture)
- `next_steps`: optional, can be empty array `[]`
- Screenshot naming: `sNN_descriptive_name.png` (numbered in demo flow order)

> ⚠️ `image_path` must be **absolute** so `generate_slide.py` can find the file.

---

## Step 4 — Run the Script

Save the JSON to `C:\tmp\slide_data.json`, then run via PowerShell:

```powershell
python "C:\Users\wi\.claude\skills\demo-slide-builder\generate_slide.py" `
  --input "C:\tmp\slide_data.json" `
  --output "C:\tmp\demo_slides.pptx"
```

The script prints the output path and slide count when done.

---

## Step 5 — Present the Result

Tell the user:
1. Where the file was saved (exact path)
2. How many slides were generated
3. Which features have real screenshots embedded vs placeholder

Example:
> "Slide deck saved to `C:\tmp\demo_slides.pptx` — 6 slides total (title, agenda, 3 feature slides, Q&A).
> Screenshots embedded: Bulk Import, RBAC. Placeholder: Notifications (page didn't load)."

---

---

## Agenda Slide Rules

**Max 4–5 items total.** More than 5 → audience loses track.

Always use `{ "text": "...", "desc": "..." }` objects — NOT plain strings:
- `text`: bold label, **3–6 words** — the "what"
- `desc`: gray subtext, **1 line** — the "how" or scope

| ❌ Too long | ✅ Correct |
|---|---|
| `"Module Plans: chọn AI Social Marketing"` | `text: "Chọn plan & bảng giá"` + `desc: "So sánh 3 tier, chọn kỳ hạn, xác nhận đơn hàng"` |
| `"AI Social Media Suite: platforms & posts"` | `text: "AI Social Media Suite"` + `desc: "Kiểm tra 6 platform kết nối và scheduled posts"` |

Max 2 items per section → if >2 related actions, merge with `→` or `+` in `text`.

Badges are color-coded per section (auto-assigned: blue/green/orange/yellow).

---

## Verify Generated PPTX (No COM Required)

PowerPoint COM (`New-Object -ComObject PowerPoint.Application`) is **unreliable** on Windows — throws `RPC_E_CALL_REJECTED` (0x80010001) when another PPT instance exists. Use python-pptx to verify instead:

```bash
python -c "
import sys, io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pptx import Presentation
prs = Presentation('C:/tmp/demo.pptx')
for i, s in enumerate(prs.slides):
    t = next((sh.text[:60] for sh in s.shapes if sh.has_text_frame and sh.text.strip()), '')
    print(f'Slide {i+1:2d}: {t}')
print(f'Total: {len(prs.slides)} slides, {__import__(\"os\").path.getsize(\"C:/tmp/demo.pptx\")//1024} KB')
"
```

**File locked by PowerPoint?** Kill it first:
```powershell
Get-Process powerpnt -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
# then regenerate
```

---

## Check Account State Before Designing Demo Narrative

Before writing the JSON, always verify the real state of the staging account. If the account already has **active plans/data**, the "new user" narrative breaks.

| Actual state | Narrative to use |
|---|---|
| No plans active | "User chưa có gói — mua từ đầu" |
| Plans already active | "User verify dashboard sau khi kích hoạt" |
| Limits reached (e.g. 5/5 chatbots) | "Hệ thống cảnh báo limit — upgrade để tiếp tục" |
| Pending bank transfers | "Pending state — chờ team duyệt" |

Never force a narrative that contradicts real account data — use what's actually visible.

---

## Feature Slide Content Rules (from web best practices)

1. **One slide = one user action.** Don't combine "select plan + checkout" on a single slide.
2. **Bullets = outcomes, not feature list.** What can the user DO? What limits will they hit?
   - ❌ "Has Facebook, Instagram, X, LinkedIn support"
   - ✅ "Kết nối 6 nền tảng: Facebook, Instagram, X, LinkedIn, TikTok, Zalo OA"
3. **3–5 bullets, max 5** (`generate_slide.py` renders `bullets[:5]` and drops the rest) — each ≤ 15 words.
4. **Admin/backend slides with no UI** → set `"image_path": null` for clean text-only slides.

---

## Slide Structure Reference

| Slide | Content |
|---|---|
| 1 — Title | Full navy background · demo title · date · team name |
| 2 — Agenda | Sections left panel · numbered items right (with desc) |
| 3…N — Features | Navy header · feature name · bullets left · screenshot right |
| Last — Q&A | "Q&A & Next Steps" · next_steps bullets |

---

## Screenshot Storage Convention

All auto-captured screenshots go to: `<project_root>\slides_screenshots\`

> Playwright cannot write outside the project directory. Always use a relative path like `slides_screenshots/<feature_slug>.png` when calling `browser_take_screenshot`. The JSON `image_path` must use the absolute project path.

Name pattern: `<NN>_<feature_slug>.png` — numbered to match slide order.

Example: "Bulk Import" (slide 3) → `slides_screenshots/03_bulk_import.png`

## Slide Layout Reference (generate_slide.py)

The script uses a **left-text / right-image** layout per feature slide:

| Zone | Position | Size |
|---|---|---|
| Header bar | full width, top | 13.33" × 1.1" |
| Text (description + bullets) | left | 5.0" wide |
| Image | right | **7.7" wide × 6.0" tall** |

The image is inserted with **aspect-ratio-correct scaling** (`_add_picture_fit`) — it fits within the 7.7×6.0 box without stretching. A 1440×900 screenshot renders at ≈ 7.7×4.8 inches.

Do NOT change `img_w`/`img_h` in the script without re-testing — the large right panel is intentional to make screenshots clearly readable in the slide.
