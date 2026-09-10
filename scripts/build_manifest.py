#!/usr/bin/env python3
"""Build manifest.json — the file list index.html renders in its sidebar.

Scans one folder (default: html/) for *.html / *.htm files and records, per file:
  path      repo-relative path, e.g. "html/reports/q3.html"
  name      file name
  dir       sub-folder relative to the root folder ("" for files directly in it)
  title     <title> text, else first <h1>, else a prettified file name
  modified  last commit date (git log -1), else file mtime — ISO 8601
  size      bytes

Standard library only. Usage:
  python scripts/build_manifest.py                      # html/ -> manifest.json
  python scripts/build_manifest.py --root docs --out _site/manifest.json --title "My pages"

Files and folders whose names start with "." or "_" are skipped, matching what a
Jekyll-based GitHub Pages build would ignore.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HTML_EXT = {".html", ".htm"}
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def extract_title(path: Path) -> str | None:
    """Return the <title> (or first <h1>) text from the first 128 KB of the file."""
    try:
        with path.open("rb") as fh:
            text = fh.read(131072).decode("utf-8", "ignore")
    except OSError:
        return None
    for rx in (TITLE_RE, H1_RE):
        m = rx.search(text)
        if m:
            t = WS_RE.sub(" ", html.unescape(TAG_RE.sub("", m.group(1)))).strip()
            if t:
                return t
    return None


def prettify(name: str) -> str:
    stem = re.sub(r"\.html?$", "", name, flags=re.I)
    return re.sub(r"[-_]+", " ", stem).strip() or name


def git_modified(path: Path, repo_root: Path) -> str | None:
    """Committer date of the last commit touching the file, or None outside git."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path.relative_to(repo_root))],
            cwd=repo_root, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = out.stdout.strip() if out.returncode == 0 else ""
    return value or None


def fs_modified(path: Path) -> str:
    ts = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    return ts.isoformat(timespec="seconds")


def hidden(name: str) -> bool:
    return name.startswith(".") or name.startswith("_")


def collect(repo_root: Path, root: str, use_git: bool) -> list[dict]:
    base = repo_root / root
    entries: list[dict] = []
    if not base.is_dir():
        return entries
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if not hidden(d))
        for fn in sorted(filenames):
            if hidden(fn) or Path(fn).suffix.lower() not in HTML_EXT:
                continue
            p = Path(dirpath) / fn
            rel = p.relative_to(repo_root).as_posix()
            sub = p.parent.relative_to(base).as_posix()
            entries.append({
                "path": rel,
                "name": fn,
                "dir": "" if sub == "." else sub,
                "title": extract_title(p) or prettify(fn),
                "modified": (git_modified(p, repo_root) if use_git else None) or fs_modified(p),
                "size": p.stat().st_size,
            })
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="html", help="folder to scan, relative to the repo root (default: html)")
    ap.add_argument("--out", default="manifest.json", help="output file (default: manifest.json)")
    ap.add_argument("--title", default=None, help="site title shown in the sidebar")
    ap.add_argument("--repo", default=".", help="repository root (default: current directory)")
    ap.add_argument("--no-git", action="store_true", help="use file mtimes instead of git commit dates")
    args = ap.parse_args()

    repo_root = Path(args.repo).resolve()
    root = args.root.strip("/").replace("\\", "/")
    files = collect(repo_root, root, use_git=not args.no_git)

    manifest = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "root": root,
        "site_title": args.title,
        "count": len(files),
        "files": files,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not (repo_root / root).is_dir():
        print(f"warning: folder '{root}/' does not exist — wrote an empty manifest", file=sys.stderr)
    print(f"{out}: {len(files)} file(s) from {root}/")
    for f in files:
        print(f"  {f['path']}  —  {f['title']}  ({f['modified'][:10]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
