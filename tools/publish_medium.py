#!/usr/bin/env python3
"""Send a Markdown article to Medium as a draft.

Usage:
    python3 publish_medium.py ARTICLE.md [--canonical URL] [--tags a,b,c]
                              [--publication ID] [--status draft|unlisted|public]
                              [--dry-run]

The integration token is read from MEDIUM_TOKEN or ~/.eb-auditor/medium-token.
Medium stopped issuing new tokens in 2025; only tokens created earlier work.
The default status is draft: the article appears in Medium's drafts and is
published by hand after a read-through.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.medium.com/v1"
TOKEN_FILE = os.path.expanduser("~/.eb-auditor/medium-token")


def token():
    t = os.environ.get("MEDIUM_TOKEN")
    if not t and os.path.exists(TOKEN_FILE):
        t = open(TOKEN_FILE).read().strip()
    if not t:
        sys.exit("No Medium token: set MEDIUM_TOKEN or put it in %s" % TOKEN_FILE)
    return t


def call(method, path, tok, body=None):
    req = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": "Bearer " + tok,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["data"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        if e.code == 401:
            sys.exit("Medium rejected the token (401). It may be revoked or never valid. " + detail)
        sys.exit("Medium API error %s: %s" % (e.code, detail))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article")
    ap.add_argument("--canonical", help="address of the original (your site); Medium shows it as the source")
    ap.add_argument("--tags", default="Employer Branding,HR,Recruiting", help="up to 3, comma-separated")
    ap.add_argument("--publication", help="publication id instead of your profile")
    ap.add_argument("--status", default="draft", choices=["draft", "unlisted", "public"])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    md = open(a.article, encoding="utf-8").read()
    title = next((l[2:].strip() for l in md.splitlines() if l.startswith("# ")), os.path.basename(a.article))
    body = {
        "title": title[:100],
        "contentFormat": "markdown",
        "content": md,
        "tags": [x.strip() for x in a.tags.split(",") if x.strip()][:3],
        "publishStatus": a.status,
        "notifyFollowers": a.status == "public",
    }
    if a.canonical:
        body["canonicalUrl"] = a.canonical

    if a.dry_run:
        shown = dict(body, content="<%d characters>" % len(md))
        print(json.dumps(shown, ensure_ascii=False, indent=2))
        return

    tok = token()
    if a.publication:
        path = "/publications/%s/posts" % a.publication
    else:
        path = "/users/%s/posts" % call("GET", "/me", tok)["id"]
    post = call("POST", path, tok, body)
    print("%s: %s" % (post.get("publishStatus"), post.get("url")))


if __name__ == "__main__":
    main()
