from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Dict, List, Tuple

from config import Config

if TYPE_CHECKING:
    from spacy.language import Language
    from spacy.matcher import PhraseMatcher

# Curated domain skill taxonomy with canonical names and aliases
SKILL_TAXONOMY: List[Tuple[str, List[str]]] = [
    # Programming Languages
    ("Python", ["python", "py"]),
    ("JavaScript", ["javascript", "js", "ecmascript", "es6"]),
    ("TypeScript", ["typescript", "ts"]),
    ("Java", ["java"]),
    ("C++", ["c++", "cpp"]),
    ("C#", ["c#", "csharp"]),
    ("Go", ["golang"]),
    ("Rust", ["rust"]),
    ("SQL", ["sql"]),
    ("PHP", ["php"]),
    ("Ruby", ["ruby", "ruby on rails", "rails"]),
    ("Swift", ["swift"]),
    ("Kotlin", ["kotlin"]),
    ("Scala", ["scala"]),
    ("Bash / Shell", ["bash", "shell scripting", "zsh"]),
    ("HTML5", ["html", "html5"]),
    ("CSS3", ["css", "css3", "scss", "sass"]),
    # Web & Mobile Frameworks
    ("React", ["react", "reactjs", "react.js"]),
    ("Next.js", ["next.js", "nextjs"]),
    ("Angular", ["angular", "angularjs"]),
    ("Vue.js", ["vue", "vuejs", "vue.js"]),
    ("Node.js", ["node.js", "nodejs"]),
    ("Express.js", ["express", "expressjs", "express.js"]),
    ("Flask", ["flask"]),
    ("Django", ["django"]),
    ("FastAPI", ["fastapi"]),
    ("Spring Boot", ["spring boot", "spring framework"]),
    (".NET", [".net", "asp.net", "dotnet"]),
    ("Tailwind CSS", ["tailwind", "tailwindcss", "tailwind css"]),
    ("React Native", ["react native"]),
    ("Flutter", ["flutter"]),
    ("GraphQL", ["graphql"]),
    ("REST APIs", ["rest api", "rest apis", "restful", "restful apis"]),
    # Data Science, AI & NLP
    ("Machine Learning", ["machine learning", "ml"]),
    ("Deep Learning", ["deep learning", "neural networks", "cnn", "rnn"]),
    ("Natural Language Processing", ["natural language processing", "nlp", "text mining"]),
    ("spaCy", ["spacy"]),
    ("scikit-learn", ["scikit-learn", "sklearn", "scikit learn"]),
    ("PyTorch", ["pytorch"]),
    ("TensorFlow", ["tensorflow", "keras"]),
    ("Pandas", ["pandas"]),
    ("NumPy", ["numpy"]),
    ("TF-IDF", ["tf-idf", "tfidf", "cosine similarity"]),
    ("PyMuPDF", ["pymupdf", "fitz"]),
    ("python-docx", ["python-docx"]),
    ("Large Language Models", ["llm", "llms", "large language models", "generative ai", "langchain"]),
    ("Computer Vision", ["computer vision", "opencv"]),
    ("Data Analysis", ["data analysis", "data analytics", "exploratory data analysis"]),
    ("Data Visualization", ["data visualization", "matplotlib", "seaborn", "plotly", "tableau", "power bi"]),
    ("Statistical Modeling", ["statistical modeling", "statistics", "hypothesis testing", "a/b testing"]),
    ("NLTK", ["nltk"]),
    ("Hugging Face", ["hugging face", "huggingface", "transformers"]),
    # Databases & Storage
    ("PostgreSQL", ["postgresql", "postgres"]),
    ("MySQL", ["mysql"]),
    ("MongoDB", ["mongodb", "mongo"]),
    ("SQLite", ["sqlite"]),
    ("Redis", ["redis"]),
    ("Elasticsearch", ["elasticsearch"]),
    ("Firebase", ["firebase", "firestore"]),
    ("Supabase", ["supabase"]),
    ("Snowflake", ["snowflake"]),
    # Cloud, DevOps & Tooling
    ("AWS", ["aws", "amazon web services", "ec2", "s3", "lambda"]),
    ("Google Cloud", ["gcp", "google cloud", "google cloud platform"]),
    ("Azure", ["azure", "microsoft azure"]),
    ("Docker", ["docker", "containerization"]),
    ("Kubernetes", ["kubernetes", "k8s"]),
    ("CI/CD", ["ci/cd", "cicd", "github actions", "jenkins", "gitlab ci"]),
    ("Git", ["git", "github", "gitlab", "version control"]),
    ("Linux", ["linux", "ubuntu", "unix"]),
    ("Terraform", ["terraform"]),
    ("Microservices", ["microservices", "distributed systems"]),
    # Testing, Product & Design
    ("Unit Testing", ["unit testing", "pytest", "jest", "vitest", "junit", "mocha"]),
    ("End-to-End Testing", ["playwright", "cypress", "selenium", "e2e testing"]),
    ("UI/UX Design", ["ui/ux", "ux design", "ui design", "figma", "wireframing", "prototyping"]),
    ("Responsive Design", ["responsive design", "responsive web design"]),
    ("Accessibility (WCAG)", ["accessibility", "wcag", "a11y"]),
    # Engineering & Professional Practices
    ("Agile / Scrum", ["agile", "scrum", "kanban", "jira"]),
    ("System Design", ["system design", "software architecture", "design patterns"]),
    ("Object-Oriented Programming", ["object-oriented programming", "oop", "object oriented"]),
    ("Data Structures & Algorithms", ["data structures", "algorithms", "dsa"]),
    ("Technical Writing", ["technical writing", "documentation", "api documentation"]),
    ("Problem Solving", ["problem solving", "analytical thinking", "critical thinking"]),
    ("Team Collaboration", ["collaboration", "cross-functional", "teamwork", "stakeholder management"]),
    ("Project Management", ["project management", "product management", "roadmap"]),
    ("Cybersecurity", ["cybersecurity", "owasp", "oauth", "jwt", "authentication"]),
]

EXTRA_STOP_WORDS = {
    "etc", "also", "using", "used", "use", "work", "working", "role", "team",
    "ability", "experience", "including", "within", "strong", "excellent",
    "good", "looking", "required", "preferred", "responsibilities", "requirements",
    "qualifications", "candidate", "position", "company", "years", "year",
    "join", "help", "build", "building", "create", "creating", "ensure", "support",
}

# Skills with punctuation/symbols where regex boundary checks complement PhraseMatcher
SYMBOL_SENSITIVE_ALIASES: Dict[str, List[re.Pattern[str]]] = {}
for canonical, aliases in SKILL_TAXONOMY:
    patterns = []
    for alias in aliases:
        escaped = re.escape(alias.lower())
        patterns.append(re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE))
    SYMBOL_SENSITIVE_ALIASES[canonical] = patterns


@lru_cache(maxsize=1)
def get_spacy_nlp() -> Language:
    """Load the configured spaCy pipeline once and cache it."""
    import spacy

    try:
        return spacy.load(Config.SPACY_MODEL)
    except OSError:
        nlp = spacy.blank("en")
        return nlp


@lru_cache(maxsize=1)
def get_phrase_matcher() -> PhraseMatcher:
    """Build a spaCy PhraseMatcher for fast multi-token skill extraction."""
    from spacy.matcher import PhraseMatcher

    nlp = get_spacy_nlp()
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    for canonical, aliases in SKILL_TAXONOMY:
        patterns = [nlp.make_doc(alias) for alias in aliases]
        matcher.add(canonical, patterns)
    return matcher


def extract_skills(text: str) -> List[str]:
    """
    Extract canonical skills using spaCy PhraseMatcher plus boundary-safe
    pattern checks for symbol-rich technologies (C++, C#, .NET, CI/CD, etc.).
    """
    nlp = get_spacy_nlp()
    matcher = get_phrase_matcher()
    doc = nlp(text)

    found_set = set()
    for match_id, _start, _end in matcher(doc):
        canonical = nlp.vocab.strings[match_id]
        found_set.add(canonical)

    for canonical, regexes in SYMBOL_SENSITIVE_ALIASES.items():
        if canonical in found_set:
            continue
        if any(pattern.search(text) for pattern in regexes):
            found_set.add(canonical)

    # Preserve deterministic taxonomy order
    return [canonical for canonical, _ in SKILL_TAXONOMY if canonical in found_set]


def preprocess_text_for_tfidf(text: str) -> Tuple[List[str], int]:
    """
    Tokenize and lemmatize text using spaCy, removing stop words and punctuation.

    Returns:
        Tuple of (normalized_tokens, raw_word_count)
    """
    raw_word_count = len([w for w in text.strip().split() if w])
    nlp = get_spacy_nlp()
    doc = nlp(text)

    tokens: List[str] = []
    for token in doc:
        if token.is_space or token.is_punct or token.like_num:
            continue
        raw_lower = token.text.lower().strip("-./")
        if len(raw_lower) < 2:
            continue
        if token.is_stop or raw_lower in EXTRA_STOP_WORDS:
            continue
        lemma = (token.lemma_ or raw_lower).lower().strip("-./")
        if len(lemma) < 2 or lemma in EXTRA_STOP_WORDS or lemma == "-pron-":
            lemma = raw_lower
        tokens.append(lemma)

    return tokens, raw_word_count
