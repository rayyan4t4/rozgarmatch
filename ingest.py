import json
import re
import sys
import urllib.request
from datetime import datetime, timezone

from skills import extract_skills

TECH_HINTS = [
    "developer", "engineer", "software", "data", "machine learning", "ml",
    "ai ", " ai", "full stack", "fullstack", "backend", "back end",
    "frontend", "front end", "devops", "programmer", "web", "mobile",
    "android", "ios", "qa", "scientist", "analyst", "architect", "sre",
    "cloud", "python", "javascript", "designer", "ux", "ui",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "RozgarMatch/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def clean(html):
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def is_tech(title, tags):
    t = (" " + (title or "").lower() + " ")
    return any(h in t for h in TECH_HINTS)


def from_remoteok(raw):
    jobs = []
    for j in raw:
        if not isinstance(j, dict) or not j.get("position"):
            continue
        desc = clean(j.get("description"))
        if not is_tech(j["position"], j.get("tags")):
            continue
        jobs.append({
            "id": "rok-" + str(j["id"]),
            "title": j["position"],
            "company": j.get("company") or "",
            "location": j.get("location") or "Remote",
            "url": j.get("apply_url") or j.get("url") or "",
            "source": "RemoteOK",
            "date": j.get("date") or "",
            "tags": [t for t in (j.get("tags") or []) if len(t) < 30],
            "description": desc[:6000],
            "skills": sorted(extract_skills(j["position"] + " " + desc + " " + " ".join(j.get("tags") or []))),
        })
    return jobs


def from_arbeitnow(raw):
    jobs = []
    for j in raw.get("data", []):
        desc = clean(j.get("description"))
        if not is_tech(j.get("title"), j.get("tags")):
            continue
        jobs.append({
            "id": "arb-" + str(j.get("slug") or abs(hash(j.get("url")))),
            "title": j.get("title") or "",
            "company": j.get("company_name") or "",
            "location": j.get("location") or "Remote",
            "url": j.get("url") or "",
            "source": "Arbeitnow",
            "date": "",
            "tags": [t for t in (j.get("tags") or []) if len(t) < 30],
            "description": desc[:6000],
            "skills": sorted(extract_skills((j.get("title") or "") + " " + desc + " " + " ".join(j.get("tags") or []))),
        })
    return jobs


def main():
    jobs, seen = [], set()
    for url, fn in [
        ("https://remoteok.com/api", from_remoteok),
        ("https://www.arbeitnow.com/api/job-board-api", from_arbeitnow),
    ]:
        try:
            for job in fn(fetch(url)):
                key = (job["title"].lower(), job["company"].lower())
                if key not in seen and job["url"]:
                    seen.add(key)
                    jobs.append(job)
        except Exception as e:
            print(f"WARN {url}: {e}", file=sys.stderr)
    out = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(jobs),
        "jobs": jobs,
    }
    with open("jobs.json", "w") as f:
        json.dump(out, f)
    print(f"ingested {len(jobs)} tech jobs")


if __name__ == "__main__":
    main()
