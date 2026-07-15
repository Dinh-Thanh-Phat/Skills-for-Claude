#!/usr/bin/env python3
"""Drive helpers for the InCard Agentic chatbot-image workflow.

Uses a local Google OAuth token (auto-refreshes) to talk to the Drive REST API.
No external deps — stdlib only.

Usage (run with PYTHONIOENCODING=utf-8 on Windows for Vietnamese names):
  python drive_media.py id2name <fileId> [<fileId> ...]
  python drive_media.py list <folderId>
  python drive_media.py rename <fileId> "<new file name>"

Optional: --token PATH   (default: C:\\Users\\wi\\.google-docs-token.json)

The file ids come from an S3 image URL the bot returns, e.g.
  https://s3-agentic-ggdrive-images.s3.../chatbot-kb-images/276/<FILE_ID>.jpg
so `id2name <FILE_ID>` tells you which real variant was actually sent.
"""
import json
import sys
import urllib.parse
import urllib.request

DEFAULT_TOKEN = r"C:\Users\wi\.google-docs-token.json"


def get_access_token(token_path):
    tok = json.load(open(token_path, encoding="utf-8"))
    if "refresh_token" not in tok and "access_token" in tok:
        return tok["access_token"]
    data = urllib.parse.urlencode({
        "client_id": tok["client_id"],
        "client_secret": tok["client_secret"],
        "refresh_token": tok["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    return json.load(urllib.request.urlopen(req))["access_token"]


def _api(url, at, data=None, method=None):
    headers = {"Authorization": "Bearer " + at}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    return json.load(urllib.request.urlopen(req))


def id2name(at, ids):
    for fid in ids:
        url = (f"https://www.googleapis.com/drive/v3/files/{fid}"
               "?fields=id,name&supportsAllDrives=true")
        try:
            r = _api(url, at)
            print(f"{fid}  ->  {r['name']}")
        except Exception as e:  # noqa: BLE001
            print(f"{fid}  ->  ERROR {e}")


def _children(at, fid):
    url = "https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode({
        "q": f"'{fid}' in parents and trashed=false",
        "fields": "files(id,name,mimeType)",
        "pageSize": 1000,
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
    })
    return _api(url, at)["files"]


def list_folder(at, folder_id, path=""):
    rows = []
    for f in _children(at, folder_id):
        if f["mimeType"].endswith("folder"):
            rows.append((path + f["name"] + "/", "FOLDER", f["id"]))
            rows += list_folder(at, f["id"], path + f["name"] + "/")
        else:
            rows.append((path + f["name"], f["mimeType"], f["id"]))
    return rows


def rename(at, fid, new_name):
    url = (f"https://www.googleapis.com/drive/v3/files/{fid}"
           "?fields=id,name&supportsAllDrives=true")
    r = _api(url, at, data={"name": new_name}, method="PATCH")
    print("OK ->", r["name"])
    print("Remember: on the platform, DELETE the old Product-Media record for this "
          "file, then Scan Folder + Select All + Train GPT so the new name takes effect.")


def main():
    argv = sys.argv[1:]
    token_path = DEFAULT_TOKEN
    if "--token" in argv:
        i = argv.index("--token")
        token_path = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    at = get_access_token(token_path)
    if cmd == "id2name":
        id2name(at, rest)
    elif cmd == "list":
        rows = list_folder(at, rest[0])
        media = sum(1 for _, mt, _ in rows if mt.startswith(("image/", "video/")))
        print(f"TOTAL {len(rows)} | MEDIA {media}")
        for name, mt, fid in sorted(rows):
            print(f"{mt:15} | {fid} | {name}")
    elif cmd == "rename":
        rename(at, rest[0], rest[1])
    else:
        print(f"Unknown command: {cmd}\n")
        print(__doc__)


if __name__ == "__main__":
    main()
