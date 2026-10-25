import io
import json
import os
import subprocess
import sys
from collections import Counter
from html import escape

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

from matcher import Matcher

BASE = os.path.dirname(os.path.abspath(__file__))
JOBS_PATH = os.path.join(BASE, "jobs.json")

app = FastAPI(title="RozgarMatch")
state = {"matcher": None, "meta": {}}


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
    return HTMLResponse(head + body)


@app.get("/robots.txt")
def robots():
    return PlainTextResponse("User-agent: *\nAllow: /\n\nSitemap: https://rozgarmatch.onrender.com/sitemap.xml\n")


@app.get("/sitemap.xml")
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://rozgarmatch.onrender.com/</loc><lastmod>2026-10-25</lastmod><priority>1.0</priority></url>
  <url><loc>https://rozgarmatch.onrender.com/how-it-works</loc><lastmod>2026-10-25</lastmod><priority>0.8</priority></url>
  <url><loc>https://rozgarmatch.onrender.com/skills-in-demand</loc><lastmod>2026-10-25</lastmod><priority>0.8</priority></url>
</urlset>
"""
    return PlainTextResponse(xml, media_type="application/xml")


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
