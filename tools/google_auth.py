#!/usr/bin/env python3
"""Create ~/.google-docs-token.json — the token gdrive-doc-reader / gsheet-formatter / gsheet-safe-write read.

    pip install google-auth-oauthlib google-api-python-client
    python tools/google_auth.py path/to/client_secret.json

client_secret.json: Google Cloud Console -> APIs & Services -> enable "Google Drive API" and
"Google Sheets API" -> Credentials -> Create OAuth client ID -> type "Desktop app" -> Download JSON.
A browser opens once to approve; the refresh token is stored, so it is a one-time step.
"""
import json
import os
import sys

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
]
OUT = os.path.expanduser('~/.google-docs-token.json')

if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
    sys.exit(__doc__)
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit('Missing package: pip install google-auth-oauthlib google-api-python-client')

creds = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES).run_local_server(port=0)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({'type': 'authorized_user', 'client_id': creds.client_id,
               'client_secret': creds.client_secret, 'refresh_token': creds.refresh_token}, f)
print(f'Saved {OUT} — keep it private (it grants access to your Drive).')
