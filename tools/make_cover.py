#!/usr/bin/env python3
"""Render a 1400x788 cover image for a review.

Usage:
    python3 make_cover.py REPORT.html --line "One-line verdict" -o cover.png [--month "October 2026"]

The company and score come from the report. The line is written by hand:
a short, plain version of the verdict (about 120 characters).
"""
import argparse
import html
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_to_article import load  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  html,body{{margin:0;width:1400px;height:788px;overflow:hidden}}
  body{{font-family:Inter,Helvetica,Arial,sans-serif;background:#111318;color:#f4f4f2;position:relative}}
  .grid{{position:absolute;inset:0;background-image:linear-gradient(#ffffff0a 1px,transparent 1px),linear-gradient(90deg,#ffffff0a 1px,transparent 1px);background-size:56px 56px}}
  .wrap{{position:absolute;inset:0;padding:84px 96px;display:flex;flex-direction:column;justify-content:space-between}}
  .kicker{{font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#9aa0aa;font-weight:600}}
  .row{{display:flex;align-items:flex-end;justify-content:space-between;gap:64px}}
  h1{{font-size:{size}px;line-height:1;margin:0;font-weight:800;letter-spacing:-.02em}}
  .verdict{{font-size:30px;line-height:1.35;color:#c9ccd2;max-width:760px;margin-top:28px}}
  .score{{text-align:right;flex:none}}
  .num{{font-size:220px;line-height:.85;font-weight:800;letter-spacing:-.04em;color:{color}}}
  .of{{font-size:34px;color:#9aa0aa;font-weight:600;margin-top:12px}}
  .bar{{height:14px;width:420px;background:#2a2e36;border-radius:7px;margin-top:22px;margin-left:auto;overflow:hidden}}
  .bar i{{display:block;height:100%;width:{score}%;background:{color}}}
  .foot{{display:flex;justify-content:space-between;font-size:22px;color:#9aa0aa}}
  .foot b{{color:#f4f4f2;font-weight:600}}
</style></head>
<body><div class="grid"></div>
<div class="wrap">
  <div class="kicker">Employer brand review · {month}</div>
  <div class="row">
    <div><h1>{company}</h1><div class="verdict">{line}</div></div>
    <div class="score"><div class="num">{score}</div><div class="of">out of 100</div><div class="bar"><i></i></div></div>
  </div>
  <div class="foot"><span><b>Employer Brand Reviews</b> · public candidate-facing material only</span><span>Made with Employer Brand Auditor</span></div>
</div>
</body></html>
"""


def color(score):
    if score >= 70:
        return "#5fd38d"
    if score >= 50:
        return "#ffcc3d"
    return "#ff7a59"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--line", required=True)
    ap.add_argument("--month")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    d = load(a.report)
    score = d["score"]["value"]
    month = a.month
    if not month:
        y, m = d["date"].split("-")[:2]
        month = "%s %s" % (MONTHS[int(m) - 1], y)
    company = d["company"]
    page = PAGE.format(
        company=html.escape(company), line=html.escape(a.line), month=html.escape(month),
        score=score, color=color(score), size=96 if len(company) <= 12 else 72,
    )
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "cover.html")
        open(src, "w", encoding="utf-8").write(page)
        out = os.path.abspath(a.out)
        subprocess.run(
            ["perl", "-e", "alarm 60; exec @ARGV", CHROME, "--headless=new", "--disable-gpu",
             "--hide-scrollbars", "--virtual-time-budget=5000",
             "--user-data-dir=" + os.path.expanduser("~/.eb-auditor/chrome-cover"),
             "--window-size=1400,788", "--screenshot=" + out, "file://" + src],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    if not os.path.exists(out):
        sys.exit("Cover was not rendered")
    print(out)


if __name__ == "__main__":
    main()
