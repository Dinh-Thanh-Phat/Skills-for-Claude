#!/usr/bin/env python3
"""sheets_lib.py — thin Google Sheets/Drive helper for english-vocab-coach.

Uses the local OAuth token at C:/Users/wi/.google-docs-token.json (installed-app
credentials with a refresh_token). No browser flow at runtime — the refresh token
mints access tokens automatically.

Public helpers:
  get_services()                         -> (sheets_service, drive_service)
  find_or_create_spreadsheet(title)      -> spreadsheet_id
  ensure_tab(sheets, sid, tab_title)     -> ensures a sheet/tab exists
  append_rows(sheets, sid, tab, rows)    -> append 2D list of values
  write_header(sheets, sid, tab, header) -> put header in row 1 if empty
"""

import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_PATH = os.environ.get(
    "GOOGLE_DOCS_TOKEN", r"C:/Users/wi/.google-docs-token.json"
)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _creds():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds.valid:
        creds.refresh(Request())
    return creds


def get_services():
    c = _creds()
    sheets = build("sheets", "v4", credentials=c, cache_discovery=False)
    drive = build("drive", "v3", credentials=c, cache_discovery=False)
    return sheets, drive


def find_or_create_spreadsheet(title):
    sheets, drive = get_services()
    q = (
        f"name = '{title}' and "
        "mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
    )
    res = drive.files().list(q=q, spaces="drive", fields="files(id,name)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    created = sheets.spreadsheets().create(
        body={"properties": {"title": title}}, fields="spreadsheetId"
    ).execute()
    return created["spreadsheetId"]


def _existing_tabs(sheets, sid):
    meta = sheets.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties").execute()
    return {s["properties"]["title"] for s in meta.get("sheets", [])}


def ensure_tab(sheets, sid, tab_title):
    if tab_title in _existing_tabs(sheets, sid):
        return
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=sid,
        body={"requests": [{"addSheet": {"properties": {"title": tab_title}}}]},
    ).execute()


def write_header(sheets, sid, tab, header):
    got = sheets.spreadsheets().values().get(
        spreadsheetId=sid, range=f"{tab}!A1:Z1"
    ).execute()
    if got.get("values"):
        return  # header already present
    sheets.spreadsheets().values().update(
        spreadsheetId=sid,
        range=f"{tab}!A1",
        valueInputOption="RAW",
        body={"values": [header]},
    ).execute()


def append_rows(sheets, sid, tab, rows):
    if not rows:
        return
    sheets.spreadsheets().values().append(
        spreadsheetId=sid,
        range=f"{tab}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


if __name__ == "__main__":
    # Smoke test: create/find the vocab spreadsheet and write a probe row.
    import datetime

    sheets, drive = get_services()
    sid = find_or_create_spreadsheet("English Vocabulary — Daily")
    ensure_tab(sheets, sid, "_probe")
    write_header(sheets, sid, "_probe", ["ts", "note"])
    append_rows(sheets, sid, "_probe", [[datetime.datetime.now().isoformat(), "sheets_lib OK"]])
    print("OK spreadsheet_id =", sid)
    print("URL = https://docs.google.com/spreadsheets/d/%s" % sid)
