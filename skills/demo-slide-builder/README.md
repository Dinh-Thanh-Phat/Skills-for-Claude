# demo-slide-builder

Generate a professional `.pptx` demo presentation from any inputs.

## How to use

Say **"tạo slide"** or **"use demo-slide-builder"** and describe what you want.

## Supported inputs

| Input type | Example |
|---|---|
| Text description | "Demo cho feature X gồm 3 tính năng: A, B, C" |
| Screenshots | Attach images → embedded in the matching feature slide |
| Web link | Provide a URL → Claude fetches and summarizes |
| PDF / DOCX | Attach file → Claude extracts structure |

## Slide structure

1. **Title slide** — navy background · title · date · team
2. **Agenda** — list of features
3. **Feature slides** (one per feature) — header, bullets, image (if available)
4. **Q&A / Next Steps** — navy background

## Run the script directly

```powershell
python "C:\Users\wi\.claude\skills\demo-slide-builder\generate_slide.py" `
  --input "C:\tmp\slide_data.json" `
  --output "C:\tmp\demo_slides.pptx"
```

## Sample JSON input

```json
{
  "title": "Sprint 12 Demo",
  "date": "2026-05-08",
  "team": "Platform Team",
  "features": [
    {
      "name": "Bulk Import",
      "description": "Upload thousands of records at once via CSV",
      "bullets": [
        "Supports CSV up to 50,000 rows",
        "Real-time validation with error row highlighting",
        "Auto-maps columns by header name",
        "Rollback on partial failure"
      ],
      "image_path": null
    },
    {
      "name": "Role-Based Access",
      "description": "Granular permissions per team and resource",
      "bullets": [
        "5 built-in roles: Owner, Admin, Editor, Viewer, Guest",
        "Custom roles with field-level permissions",
        "Audit log for all permission changes"
      ],
      "image_path": "C:\\Screenshots\\rbac_ui.png"
    }
  ],
  "next_steps": [
    "UAT sign-off by 2026-05-15",
    "Deploy to staging on 2026-05-12"
  ]
}
```

## Output

File saved to `C:\tmp\demo_slides.pptx` (default) or wherever you specify with `--output`.

## Dependencies

```
python-pptx  (pip install python-pptx)
Pillow       (installed automatically with python-pptx)
```
