---
name: gdrive-doc-reader
description: Read and extract text content from Google Drive files and folders. Use when you need to read documents from Google Drive for processing — especially PDF, DOCX, TXT, and Google Docs. Triggers on: "read Google Drive docs", "extract text from Drive folder", "get content from Drive link", "load documents from Google Drive". Used as Step 1 in chatbot testing pipeline. Outputs combined text content from all docs to a single file.
---

# Google Drive Document Reader

Reads files from Google Drive and extracts text content for downstream processing.

## Supported File Types
- Google Docs (`.gdoc`) → exported as plain text
- PDF (`.pdf`) → text extraction via pdfminer
- DOCX (`.docx`) → text extraction via python-docx
- TXT (`.txt`) → read directly
- Google Sheets → export first sheet as CSV text

## Setup: Google Drive API Authentication

**On this workstation use the existing OAuth token** (shared with `gsheet-formatter` and
`gsheet-safe-write`):

```
C:\Users\wi\.google-docs-token.json
```

This token already has `drive.readonly` + `spreadsheets` scopes. Prefer reading it directly
instead of re-prompting OAuth:

```python
import json, google.oauth2.credentials
tok = json.loads(open(r'C:\Users\wi\.google-docs-token.json').read())
creds = google.oauth2.credentials.Credentials(
    token=None, refresh_token=tok["refresh_token"],
    client_id=tok["client_id"], client_secret=tok["client_secret"],
    token_uri="https://oauth2.googleapis.com/token",
)
```

**Fallback** (other machines / fresh setup) — `~/.credentials/gdrive_credentials.json`:
1. Google Cloud Console → Create a project → Enable Google Drive API
2. Create OAuth2 credentials → Download as `credentials.json`
3. Run auth once to produce `~/.credentials/token.json`

## Python Implementation

Write this script as `gdrive_reader.py`:

```python
import os
import io
import sys
import re
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_PATH = Path.home() / ".credentials" / "token.json"
CRED_PATH = Path.home() / ".credentials" / "gdrive_credentials.json"

class GDriveReader:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)

    def _authenticate(self) -> Credentials:
        creds = None
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(str(CRED_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
            TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_PATH.write_text(creds.to_json())
        return creds

    def extract_file_id(self, drive_link: str) -> str:
        patterns = [
            r'/folders/([a-zA-Z0-9_-]+)',
            r'/file/d/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'/d/([a-zA-Z0-9_-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, drive_link)
            if match:
                return match.group(1)
        raise ValueError(f"Cannot extract ID from Drive link: {drive_link}")

    def list_files_in_folder(self, folder_id: str) -> list:
        files = []
        page_token = None
        while True:
            response = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token
            ).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        return files

    def read_file(self, file_id: str, mime_type: str) -> str:
        GOOGLE_DOC = 'application/vnd.google-apps.document'
        GOOGLE_SHEET = 'application/vnd.google-apps.spreadsheet'

        if mime_type == GOOGLE_DOC:
            content = self.service.files().export(fileId=file_id, mimeType='text/plain').execute()
            return content.decode('utf-8')
        elif mime_type == GOOGLE_SHEET:
            content = self.service.files().export(fileId=file_id, mimeType='text/csv').execute()
            return content.decode('utf-8')
        else:
            request = self.service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buffer.seek(0)

            if 'pdf' in mime_type:
                return self._extract_pdf(buffer)
            elif 'wordprocessingml' in mime_type:
                return self._extract_docx(buffer)
            else:
                return buffer.read().decode('utf-8', errors='ignore')

    def _extract_pdf(self, buffer: io.BytesIO) -> str:
        import pdfminer.high_level
        return pdfminer.high_level.extract_text(buffer)

    def _extract_docx(self, buffer: io.BytesIO) -> str:
        from docx import Document
        doc = Document(buffer)
        return '\n'.join(para.text for para in doc.paragraphs)

    def read_from_link(self, drive_link: str, output_file: str = "docs_content.txt") -> dict:
        file_id = self.extract_file_id(drive_link)
        metadata = self.service.files().get(fileId=file_id, fields="id, name, mimeType").execute()

        if metadata['mimeType'] == 'application/vnd.google-apps.folder':
            files = self.list_files_in_folder(file_id)
        else:
            files = [metadata]

        all_text = []
        file_count = 0

        for file in files:
            print(f"  Reading: {file['name']}")
            try:
                text = self.read_file(file['id'], file['mimeType'])
                if text.strip():
                    all_text.append(f"=== {file['name']} ===\n{text}\n")
                    file_count += 1
            except Exception as e:
                print(f"  ⚠️ Skipped {file['name']}: {e}")

        if not all_text:
            raise RuntimeError("No text content extracted from any file in the Drive link")

        combined = '\n'.join(all_text)
        Path(output_file).write_text(combined, encoding='utf-8')

        word_count = len(combined.split())
        print(f"✓ Read {file_count} files, {word_count:,} words → {output_file}")
        return {"file_count": file_count, "word_count": word_count, "output": output_file}


if __name__ == "__main__":
    reader = GDriveReader()
    reader.read_from_link(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "docs_content.txt")
```

## Dependencies
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install pdfminer.six python-docx
```

## Output Format

File: `docs_content.txt`
```
=== Document1.pdf ===
[extracted text content]

=== HR Policy.docx ===
[extracted text content]

=== Product Guide (Google Doc) ===
[extracted text content]
```

## Error Handling
- File not accessible → skip with warning, continue to next file
- Invalid Drive link → raise immediately with helpful message
- Empty docs folder → raise error, don't produce empty output
- Auth failure → guide user through re-authentication steps
- Unsupported file type → log and skip (don't crash)

## Key Principle
Output must always be a non-empty text file. If all files fail to extract, raise an error — don't pass an empty file downstream.
