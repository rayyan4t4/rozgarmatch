import io
import json
import os
import subprocess
import sys

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse

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
