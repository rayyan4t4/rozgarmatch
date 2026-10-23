# RozgarMatch

Live tech jobs, ranked against your actual CV — plus the skill gaps worth closing first.

## The problem

Graduates apply blind. Job boards list hundreds of roles with no signal about which ones a given CV actually fits, and no honest answer to "what should I learn next?" RozgarMatch ingests real, current tech listings, extracts the skills each job asks for, and scores your CV against every one of them.

## What it does

- Ingests live listings from the RemoteOK and Arbeitnow public APIs (no keys), filters to tech roles, dedupes.
- Extracts skills from your CV and from each job's title, tags and full description using a 70+ skill taxonomy.
- Ranks jobs by fit: 65% skill coverage (weighted so jobs that specify more skills count more) + 35% TF-IDF text similarity between your CV and the job description.
- For every match: the skills you have, the skills it still asks for, and a direct apply link.
- Aggregates your top gaps across your best matches — the skills the market is asking you for most.

## Run it

```bash
pip install -r requirements.txt
python ingest.py
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000, paste a CV (or upload a PDF), and get ranked matches. `POST /api/refresh` re-ingests the latest listings.

## Honest limits

- Listings are remote/global roles from the two APIs — strong for Pakistani graduates targeting remote work, not a local-jobs board (yet).
- Fit is skills-based. It does not judge seniority, salary fit, or company quality.
- Skill extraction is taxonomy-based: a skill phrased unusually may be missed.

Built by Rayyan Khan — Day 1 of the serious daily build program (2026-10-23).
