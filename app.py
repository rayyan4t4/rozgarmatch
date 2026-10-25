import io
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from html import escape

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

from matcher import Matcher

BASE = os.path.dirname(os.path.abspath(__file__))
JOBS_PATH = os.path.join(BASE, "jobs.json")

app = FastAPI(title="RozgarMatch")
state = {"matcher": None, "meta": {}}

NAV = '<nav class="nav"><a class="brand" href="/">RozgarMatch</a><span class="links"><a href="/jobs">Jobs</a><a href="/skills-in-demand">Skills in Demand</a><a href="/blog">Blog</a><a href="/how-it-works">How It Works</a><a href="/about">About</a></span></nav>'
NAV_CSS = ".nav { display:flex; justify-content:space-between; align-items:center; padding:16px 0; border-bottom:1px solid #e3e7ec; margin-bottom:26px; flex-wrap:wrap; gap:8px; } .nav .brand { font-size:20px; font-weight:bold; color:#101418; text-decoration:none; } .nav .links a { margin-left:16px; font-size:14.5px; }"
SLUG_SPECIAL = {"c++": "cpp", "c#": "csharp", "node.js": "nodejs"}
BLOG_POSTS = {"cv-job-matching-guide", "skills-remote-tech-jobs-ask-for", "fresh-graduate-job-hunting", "skill-gap-analysis-study-plan"}


def slugify(skill):
    if skill in SLUG_SPECIAL:
        return SLUG_SPECIAL[skill]
    return re.sub(r"[^a-z0-9]+", "-", skill.lower()).strip("-")


def skill_slugs():
    jobs = state["matcher"].jobs if state["matcher"] else []
    counts = Counter(s for j in jobs for s in j["skills"])
    return {slugify(s): s for s, n in counts.items() if n >= 5}


def job_card(j):
    chips = "".join('<span class="chip">' + escape(s) + "</span>" for s in j["skills"])
    return (
        '<div class="job"><span class="job-title">' + escape(j["title"]) + "</span>"
        '<div class="job-meta">' + escape(j["company"]) + " · " + escape(j["location"]) + " · via " + escape(j["source"]) + "</div>"
        '<div class="chips">' + chips + "</div>"
        '<p class="desc">' + escape(j["description"][:220]) + "…</p>"
        '<a class="apply" href="' + escape(j["url"]) + '" target="_blank" rel="noopener">View &amp; apply →</a></div>'
    )


def load():
    try:
        if not os.path.exists(JOBS_PATH):
            subprocess.run([sys.executable, "ingest.py"], cwd=BASE, check=False)
        with open(JOBS_PATH) as f:
            data = json.load(f)
        state["matcher"] = Matcher(data["jobs"])
        state["meta"] = {"count": data["count"], "fetched_at": data["fetched_at"]}
    except Exception:
        state["matcher"] = Matcher([])
        state["meta"] = {"count": 0, "fetched_at": ""}


@app.on_event("startup")
def startup():
    load()


@app.get("/")
def home():
    return FileResponse(os.path.join(BASE, "static", "index.html"))


@app.get("/how-it-works")
def how_it_works():
    return FileResponse(os.path.join(BASE, "static", "how-it-works.html"))


@app.get("/skills-in-demand")
def skills_in_demand():
    jobs = state["matcher"].jobs if state["matcher"] else []
    total = len(jobs)
    counts = Counter(s for j in jobs for s in j["skills"])
    rows = "".join(
        '<div class="row"><span>' + escape(skill) + '</span><span class="muted">asked by ' + str(n) + " of " + str(total) + " listings (" + str(round(100 * n / total) if total else 0) + '%)</span></div>'
        for skill, n in counts.most_common(48)
    )
    head = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skills in Demand — What Live Tech Jobs Ask For | RozgarMatch</title>
<meta name="description" content="The most in-demand skills across live tech job listings, counted from real postings: see what employers ask for most and which skills are worth learning next.">
<link rel="canonical" href="https://rozgarmatch.onrender.com/skills-in-demand">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:url" content="https://rozgarmatch.onrender.com/skills-in-demand">
<meta property="og:title" content="Skills in Demand — What Live Tech Jobs Ask For">
<meta property="og:description" content="The most requested skills in live tech job listings, counted from real postings.">
<meta property="og:image" content="https://rayyankhan.online/covers/card-rozgar.webp">
<style>
  body { margin:0; font-family: Georgia, 'Times New Roman', serif; color:#101418; background:#fbfcfd; }
  .wrap { max-width: 860px; margin: 0 auto; padding: 40px 20px 80px; }
  h1 { font-size: 34px; margin: 0 0 8px; letter-spacing: -0.5px; }
  p { line-height: 1.6; }
  .sub { color:#5b6672; font-size: 17px; }
  .card { background:#fff; border:1px solid #e3e7ec; border-radius: 12px; padding: 10px 22px; }
  .row { display:flex; justify-content:space-between; gap:14px; padding:9px 0; border-bottom:1px solid #e3e7ec; }
  .row:last-child { border-bottom:0; }
  .muted { color:#5b6672; font-size: 14px; white-space: nowrap; }
  a { color:#0b6e4f; }
  .foot { color:#5b6672; font-size: 13.5px; margin-top: 40px; }
  .nav { display:flex; justify-content:space-between; align-items:center; padding:16px 0; border-bottom:1px solid #e3e7ec; margin-bottom:26px; flex-wrap:wrap; gap:8px; }
  .nav .brand { font-size:20px; font-weight:bold; color:#101418; text-decoration:none; }
  .nav .links a { margin-left:16px; font-size:14.5px; }
</style>
</head>
<body>
<div class="wrap">
"""
    body = (
        "<h1>Skills in demand right now</h1>\n"
        '<p class="sub">Counted live from the ' + str(total) + ' tech job listings RozgarMatch currently indexes (RemoteOK + Arbeitnow). '
        "If you are a fresh graduate deciding what to learn next, start at the top of this list — and check which of these your own CV is missing with the <a href=\"/\">CV matcher</a>.</p>\n"
        '<div class="card">' + rows + "</div>\n"
        '<p class="foot">RozgarMatch by <a href="https://rayyankhan.online">Rayyan Khan</a> · <a href="/">Match your CV</a> · <a href="/how-it-works">How it works</a></p>\n'
        "</div>\n</body>\n</html>"
    )
    return HTMLResponse(head + NAV + body)


@app.get("/jobs")
def jobs_page():
    jobs = state["matcher"].jobs if state["matcher"] else []
    links = "".join('<a class="chip" href="/jobs/' + slug + '">' + escape(skill) + "</a>" for slug, skill in sorted(skill_slugs().items(), key=lambda kv: kv[1]))
    cards = "".join(job_card(j) for j in jobs)
    head = jobs_head("Remote Tech Jobs — Live Listings Ranked by CV Fit | RozgarMatch", "Browse live remote tech job listings indexed by RozgarMatch from RemoteOK and Arbeitnow. Match your CV to see your fit score, matched skills, and missing skills for every job.", "https://rozgarmatch.onrender.com/jobs")
    body = (
        "<h1>Live remote tech jobs</h1>\n"
        '<p class="sub">' + str(len(jobs)) + ' current tech listings, indexed live. <a href="/">Match your CV</a> to rank these by your fit — or browse by skill:</p>\n'
        '<div class="chips" style="margin-bottom:22px">' + links + "</div>\n" + cards
        + '<p class="foot">RozgarMatch by <a href="https://rayyankhan.online">Rayyan Khan</a> · <a href="/">Match your CV</a> · <a href="/skills-in-demand">Skills in demand</a></p>\n</div>\n</body>\n</html>'
    )
    return HTMLResponse(head + NAV + body)


@app.get("/jobs/{slug}")
def jobs_by_skill(slug: str):
    mapping = skill_slugs()
    if slug not in mapping or not state["matcher"]:
        return HTMLResponse("Not found", status_code=404)
    skill = mapping[slug]
    jobs = [j for j in state["matcher"].jobs if skill in j["skills"]]
    label = skill[:1].upper() + skill[1:]
    cards = "".join(job_card(j) for j in jobs)
    head = jobs_head(label + " Jobs — Live Remote Listings | RozgarMatch", "Live remote tech jobs asking for " + skill + ", indexed by RozgarMatch. Match your CV to see your fit, the skills you already have, and the ones each job still needs.", "https://rozgarmatch.onrender.com/jobs/" + slug)
    body = (
        "<h1>" + escape(label) + " jobs</h1>\n"
        '<p class="sub">' + str(len(jobs)) + ' live listings asking for ' + escape(skill) + '. <a href="/">Match your CV</a> to rank them by your fit, or <a href="/jobs">browse all jobs</a>.</p>\n' + cards
        + '<p class="foot">RozgarMatch by <a href="https://rayyankhan.online">Rayyan Khan</a> · <a href="/jobs">All jobs</a> · <a href="/skills-in-demand">Skills in demand</a></p>\n</div>\n</body>\n</html>'
    )
    return HTMLResponse(head + NAV + body)


def jobs_head(title, description, canonical):
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + escape(title) + """</title>
<meta name="description" content=""" + escape(description) + """>
<link rel="canonical" href=""" + canonical + """>
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:title" content=""" + escape(title) + """>
<meta property="og:description" content=""" + escape(description) + """>
<meta property="og:image" content="https://rayyankhan.online/covers/card-rozgar.webp">
<style>
  body { margin:0; font-family: Georgia, 'Times New Roman', serif; color:#101418; background:#fbfcfd; }
  .wrap { max-width: 860px; margin: 0 auto; padding: 24px 20px 80px; }
  h1 { font-size: 34px; margin: 0 0 8px; letter-spacing: -0.5px; }
  .sub { color:#5b6672; font-size: 17px; line-height: 1.5; }
  a { color:#0b6e4f; }
  .job { background:#fff; border:1px solid #e3e7ec; border-radius: 12px; padding: 18px 20px; margin-bottom: 12px; }
  .job-title { font-size: 18px; font-weight: bold; }
  .job-meta { color:#5b6672; font-size: 14px; margin: 3px 0 10px; }
  .chips { display:flex; flex-wrap: wrap; gap: 6px; }
  .chip { font: 12.5px ui-monospace, Menlo, monospace; background: #eef4f1; border-radius: 999px; padding: 3px 10px; color:#101418; text-decoration:none; }
  .desc { color:#3c4652; font-size: 14.5px; line-height: 1.55; margin: 10px 0; }
  a.apply { font-size: 14.5px; }
  .foot { color:#5b6672; font-size: 13.5px; margin-top: 40px; }
""" + NAV_CSS + """
</style>
</head>
<body>
<div class="wrap">
"""


@app.get("/blog")
def blog_index():
    return FileResponse(os.path.join(BASE, "static", "blog", "index.html"))


@app.get("/blog/{slug}")
def blog_post(slug: str):
    if slug not in BLOG_POSTS:
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(os.path.join(BASE, "static", "blog", slug + ".html"))


@app.get("/about")
def about():
    return FileResponse(os.path.join(BASE, "static", "about.html"))


@app.get("/robots.txt")
def robots():
    return PlainTextResponse("User-agent: *\nAllow: /\n\nSitemap: https://rozgarmatch.onrender.com/sitemap.xml\n")


@app.get("/sitemap.xml")
def sitemap():
    base = "https://rozgarmatch.onrender.com"
    fetched = (state["meta"].get("fetched_at") or "")[:10] or date.today().isoformat()
    entries = [("/", "1.0"), ("/jobs", "0.9"), ("/skills-in-demand", "0.8"), ("/how-it-works", "0.7"), ("/about", "0.7"), ("/blog", "0.8")]
    entries += [("/blog/" + s, "0.8") for s in sorted(BLOG_POSTS)]
    entries += [("/jobs/" + s, "0.7") for s in sorted(skill_slugs())]
    urls = "".join('  <url><loc>' + base + path + "</loc><lastmod>" + fetched + "</lastmod><priority>" + prio + "</priority></url>\n" for path, prio in entries)
    return PlainTextResponse('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n", media_type="application/xml")


@app.get("/api/jobs")
def jobs(q: str = "", limit: int = 50):
    m = state["matcher"]
    if m is None:
        return JSONResponse({"meta": state["meta"], "jobs": []})
    out = m.jobs
    if q:
        ql = q.lower()
        out = [j for j in out if ql in (j["title"] + " " + j["company"] + " " + " ".join(j["skills"])).lower()]
    return {"meta": state["meta"], "jobs": [
        {k: j[k] for k in ("id", "title", "company", "location", "url", "source", "skills")} | {"description": j["description"][:300]}
        for j in out[:limit]
    ]}


@app.post("/api/match")
async def match(cv_text: str = Form(""), file: UploadFile = File(None)):
    text = cv_text or ""
    if file is not None and file.filename:
        raw = await file.read()
        if file.filename.lower().endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        else:
            text = raw.decode("utf-8", errors="ignore")
    text = text.strip()
    if len(text) < 40:
        return JSONResponse({"error": "Paste or upload a CV with more detail so matching has something to work with."}, status_code=400)
    return state["matcher"].match(text)


@app.post("/api/refresh")
def refresh():
    subprocess.run([sys.executable, "ingest.py"], cwd=BASE, check=False)
    load()
    return {"meta": state["meta"]}
