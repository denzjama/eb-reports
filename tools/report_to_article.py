#!/usr/bin/env python3
"""Turn an Employer Brand Auditor HTML report into a Markdown article.

Usage:
    python3 report_to_article.py REPORT.html [--report-url URL] [--site] [-o ARTICLE.md]

The article carries the score, verdict, what works, the main problems, the
first actions, a short method note and the source list. The full report is
linked with --report-url (for example its GitHub Pages address).
"""
import argparse
import json
import re
import sys

TEXT = {
    "ru": {
        "score": "Оценка HR-бренда",
        "of": "из 100",
        "coverage": "покрытие",
        "conf": {"high": "надёжность высокая", "medium": "надёжность средняя", "low": "надёжность низкая"},
        "works": "Что работает",
        "problems": "Главные проблемы",
        "actions": "С чего начать",
        "method": "Как сделан разбор",
        "method_text": (
            "Аудит сделан плагином Employer Brand Auditor по открытым материалам для кандидатов: "
            "карьерный сайт, вакансии, истории сотрудников, официальные соцсети. Учитывается только "
            "текст, который удалось прочитать; каждая цитата сверена с сохранённым источником. "
            "Отзывы сотрудников показаны отдельно и на оценку не влияют. Материалы собраны {date}."
        ),
        "perception": "Что говорят в отзывах",
        "perception_note": "Отзывы — мнения отдельных людей, а не факты о компании; на оценку они не влияют.",
        "full": "Полный отчёт с методологией, картой источников и всеми доказательствами",
        "sources": "Источники",
        "disclaimer": (
            "Разбор оценивает только публичную коммуникацию работодателя, а не то, как в компании "
            "работается на самом деле. Если вы представляете компанию и видите ошибку, напишите — исправим."
        ),
        "title": "HR-бренд {company}: {score} из 100",
    },
    "en": {
        "score": "Employer Brand Score",
        "of": "out of 100",
        "coverage": "coverage",
        "conf": {"high": "high reliability", "medium": "medium reliability", "low": "low reliability"},
        "works": "What works",
        "problems": "The main problems",
        "actions": "Where to start",
        "method": "How this review was made",
        "method_text": (
            "The audit was made with the Employer Brand Auditor plugin from public candidate-facing "
            "material: the careers site, job ads, employee stories and official social channels. Only "
            "text that was actually read counts, and every quotation was checked against the saved "
            "source. Employee reviews are shown separately and never change the score. Material "
            "captured on {date}."
        ),
        "perception": "What reviews say",
        "perception_note": "Reviews are individual opinions, not facts about the company; they never change the score.",
        "full": "Full report with the method, source map and all evidence",
        "sources": "Sources",
        "disclaimer": (
            "This review assesses the employer's public communication only, not what working there "
            "is actually like. If you represent the company and see an error, get in touch and it "
            "will be corrected."
        ),
        "title": "{company}'s employer brand: {score}/100",
    },
}


def load(path):
    html = open(path, encoding="utf-8").read()
    m = re.search(r'<script[^>]*id="report-data"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        sys.exit("No report data found in %s" % path)
    return json.loads(m.group(1).replace("<\\/", "</"))


def build(d, report_url=None, site=False):
    t = TEXT.get(d.get("lang"), TEXT["en"])
    s = d["score"]
    out = []
    add = out.append
    title = t["title"].format(company=d["company"], score=s["value"])
    if site:
        add("---")
        add("title: " + json.dumps(title, ensure_ascii=False))
        add("---")
    else:
        add("# " + title)
    add("")
    add("*" + d.get("verdict", "") + "*")
    add("")
    add("**{} — {} {}** · {} {}% · {}".format(
        t["score"], s["value"], t["of"], t["coverage"], s.get("coverage", ""),
        t["conf"].get(s.get("confidence"), "")))
    add("")
    for p in d.get("summary", {}).get("points", []):
        add("- " + (p if isinstance(p, str) else p.get("text", "")))
    add("")

    add("## " + t["works"])
    for x in d.get("strengths", [])[:4]:
        add("")
        add("**{}.** {}".format(x["title"].rstrip("."), x.get("text", "")))
    add("")

    add("## " + t["problems"])
    for x in d.get("problems", [])[:4]:
        add("")
        add("**{}.** {}".format(x["title"].rstrip("."), x.get("why", "")))
        for e in x.get("evidence", [])[:1]:
            q = e if isinstance(e, str) else e.get("quote") or e.get("text") or ""
            if q:
                add("")
                add("> " + q.replace("\n", " "))
    add("")

    add("## " + t["actions"])
    add("")
    for i, a in enumerate(d.get("summary", {}).get("actions", []), 1):
        add("{}. {}".format(i, a if isinstance(a, str) else a.get("text", "")))
    add("")

    per = d.get("perception") or {}
    if per.get("themes") and not per.get("thin"):
        add("## " + t["perception"])
        add("")
        add("*" + t["perception_note"] + "*")
        add("")
        for th in per["themes"][:5]:
            name = th.get("theme") or th.get("title") or ""
            count = "{} / {}".format(th["mentions"], th["of"]) if th.get("mentions") else ""
            say = th.get("note") or th.get("summary") or ""
            add("- **{}**{}: {}".format(name, " ({})".format(count) if count else "", say))
        add("")

    add("## " + t["method"])
    add("")
    add(t["method_text"].format(date=d.get("date", "")))
    if report_url:
        add("")
        add("**[{}]({})**".format(t["full"], report_url))
    add("")

    srcs = d.get("sources", [])
    if srcs:
        add("## " + t["sources"])
        add("")
        for x in srcs:
            add("- [{}]({})".format(x.get("title", x.get("url")), x.get("url")))
        add("")

    add("---")
    add("")
    add("*" + t["disclaimer"] + "*")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--report-url")
    ap.add_argument("-o", "--out")
    ap.add_argument("--site", action="store_true", help="page for the site: title in front matter, no top heading")
    a = ap.parse_args()
    md = build(load(a.report), a.report_url, a.site)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(md)
        print(a.out)
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
