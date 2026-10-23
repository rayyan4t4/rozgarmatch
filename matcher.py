from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from skills import extract_skills


class Matcher:
    def __init__(self, jobs):
        self.jobs = jobs
        corpus = [j["title"] + " " + j["description"] for j in jobs]
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=8000, sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(corpus) if corpus else None

    def match(self, cv_text, top_n=15):
        cv_skills = extract_skills(cv_text)
        if self.matrix is None or not self.jobs:
            return {"cv_skills": sorted(cv_skills), "matches": [], "top_gaps": []}
        cv_vec = self.vectorizer.transform([cv_text])
        sims = cosine_similarity(cv_vec, self.matrix)[0]
        scored = []
        for i, job in enumerate(self.jobs):
            required = set(job["skills"])
            matched = sorted(required & cv_skills)
            missing = sorted(required - cv_skills)
            recall = (len(matched) / len(required)) if required else 0.0
            skill_score = recall * min(1.0, len(required) / 4)
            fit = round(100 * (0.65 * skill_score + 0.35 * float(sims[i])), 1)
            scored.append({
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "url": job["url"],
                "source": job["source"],
                "fit": fit,
                "matched_skills": matched,
                "missing_skills": missing,
            })
        scored.sort(key=lambda x: -x["fit"])
        top = scored[:top_n]
        gap_counter = Counter()
        for m in top:
            gap_counter.update(m["missing_skills"])
        top_gaps = [{"skill": s, "in_demand_by": c} for s, c in gap_counter.most_common(10)]
        return {"cv_skills": sorted(cv_skills), "matches": top, "top_gaps": top_gaps}
