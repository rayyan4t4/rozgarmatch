SKILLS = {
    "python": ["python"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs"],
    "next.js": ["next.js", "nextjs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "angular": ["angular"],
    "node.js": ["node.js", "nodejs", "node"],
    "express": ["express", "express.js"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "tailwind", "bootstrap", "sass"],
    "fastapi": ["fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "laravel": ["laravel"],
    "php": ["php"],
    "java": ["java"],
    "spring": ["spring", "spring boot"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
    "flutter": ["flutter", "dart"],
    "android": ["android"],
    "ios": ["ios"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp", ".net", "dotnet"],
    "go": ["golang"],
    "rust": ["rust"],
    "sql": ["sql"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "machine learning": ["machine learning", "ml models", "ml pipelines"],
    "deep learning": ["deep learning", "neural networks", "neural network"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "keras"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "nlp": ["nlp", "natural language processing"],
    "llm": ["llm", "llms", "large language model", "large language models", "gpt", "prompt engineering"],
    "rag": ["rag", "retrieval augmented", "retrieval-augmented"],
    "computer vision": ["computer vision", "opencv", "image classification", "object detection"],
    "data analysis": ["data analysis", "data analytics"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "spark": ["spark", "apache spark", "pyspark"],
    "airflow": ["airflow"],
    "tableau": ["tableau"],
    "power bi": ["power bi", "powerbi"],
    "docker": ["docker", "containers", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud"],
    "azure": ["azure", "microsoft azure"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "github actions", "jenkins"],
    "git": ["git", "github", "gitlab"],
    "linux": ["linux", "bash", "shell scripting"],
    "rest api": ["rest api", "restful", "api design", "apis"],
    "graphql": ["graphql"],
    "testing": ["pytest", "unit testing", "jest", "selenium", "test automation"],
    "agile": ["agile", "scrum"],
    "figma": ["figma"],
    "ui/ux": ["ui/ux", "ux design", "ui design"],
}

import re

_PATTERNS = {}
for canon, aliases in SKILLS.items():
    for a in set(aliases + [canon]):
        _PATTERNS[a] = canon

_SORTED = sorted(_PATTERNS, key=len, reverse=True)


def extract_skills(text):
    if not text:
        return set()
    t = " " + re.sub(r"[^a-z0-9+#./ ]", " ", text.lower()) + " "
    found = set()
    for alias in _SORTED:
        if " " + alias + " " in t or " " + alias + "," in t or "(" + alias + ")" in t:
            found.add(_PATTERNS[alias])
    return found
