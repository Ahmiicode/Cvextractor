from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, TYPE_CHECKING, Dict, List, Tuple

from config import Config

if TYPE_CHECKING:
    from spacy.language import Language
    from spacy.matcher import PhraseMatcher


# =========================================================
# SKILL TAXONOMY
# =========================================================

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

    # Carpentry, Construction & Woodworking
    ("Woodworking", ["woodworking", "wood work"]),
    ("Carpentry", ["carpentry", "carpenter"]),
    ("Furniture Installation", ["furniture installation", "furniture assembly"]),
    ("Cabinet Making", ["cabinet making", "cabinet installation"]),
    ("Blueprint Reading", ["blueprint reading", "reading blueprints"]),
    ("Technical Drawing Interpretation", ["technical drawings", "construction drawings"]),
    ("Measuring & Cutting", ["measuring and cutting", "measurement and cutting"]),
    ("Power Tools", ["power tools", "electric tools"]),
    ("Hand Tools", ["hand tools", "manual tools"]),
    ("Wood Finishing", ["wood finishing", "wood polishing"]),
    ("Door & Window Installation", ["door installation", "window installation"]),
    ("Flooring Installation", ["floor installation", "flooring installation"]),
    ("Construction Safety", ["construction safety", "workplace safety"]),
    ("Material Selection", ["material selection", "building materials"]),
    ("Repair & Maintenance", ["repair and maintenance", "maintenance and repair"]),

    # Marketing & Sales
    ("Digital Marketing", ["digital marketing", "online marketing"]),
    ("Social Media Marketing", ["social media marketing", "social media management"]),
    ("SEO", ["search engine optimization", "seo"]),
    ("Content Creation", ["content creation", "content development"]),
    ("Market Research", ["market research", "consumer research"]),
    ("Lead Generation", ["lead generation", "generating leads"]),
    ("Sales", ["sales", "sales management"]),
    ("Customer Relationship Management", ["customer relationship management", "crm"]),
    ("Negotiation", ["negotiation", "negotiation skills"]),

    # HR & Administration
    ("Recruitment", ["recruitment", "talent acquisition"]),
    ("Employee Relations", ["employee relations", "staff relations"]),
    ("Human Resource Management", ["human resource management", "human resources", "hr management"]),
    ("Payroll Management", ["payroll management", "payroll processing"]),
    ("Administrative Support", ["administrative support", "office administration"]),
    ("Record Keeping", ["record keeping", "document management"]),

    # Healthcare
    ("Patient Care", ["patient care", "patient assistance"]),
    ("First Aid", ["first aid", "basic first aid"]),
    ("Medical Records Management", ["medical records", "patient records"]),
    ("Medication Administration", ["medication administration", "administering medication"]),
    ("Vital Signs Monitoring", ["vital signs", "blood pressure monitoring"]),

    # Accounting & Finance
    ("Bookkeeping", ["bookkeeping", "book keeping"]),
    ("Financial Reporting", ["financial reporting", "financial reports"]),
    ("Financial Analysis", ["financial analysis", "financial planning"]),
    ("Accounts Payable", ["accounts payable"]),
    ("Accounts Receivable", ["accounts receivable"]),
    ("Budget Management", ["budget management", "budgeting"]),
    ("Microsoft Excel", ["microsoft excel", "ms excel", "excel"]),

    # Kitchen Assistant, Food Service & Hospitality
    ("Food Preparation", ["food preparation", "meal preparation", "preparing food"]),
    ("Food Safety", ["food safety", "safe food handling"]),
    ("Food Hygiene", ["food hygiene", "kitchen hygiene", "personal hygiene"]),
    ("Food Handling", ["food handling", "handling food"]),
    ("Food Storage", ["food storage", "proper food storage"]),
    ("Cleaning & Sanitizing", ["cleaning and sanitizing", "cleaning and sanitation", "sanitizing"]),
    ("Dishwashing", ["dishwashing", "washing dishes", "washing utensils"]),
    ("Kitchen Equipment", ["kitchen equipment", "commercial kitchen equipment"]),
    ("Stock Rotation", ["stock rotation", "fifo", "first in first out"]),
    ("Inventory Management", ["inventory management", "stock management", "inventory control"]),
    ("Temperature Control", ["temperature control", "food temperature monitoring"]),
    ("Allergen Awareness", ["allergen awareness", "food allergens", "allergen management"]),
    ("HACCP", ["haccp", "hazard analysis critical control points"]),
    ("Portion Control", ["portion control"]),
    ("Catering", ["catering", "catering services"]),
    ("Table Service", ["table service", "serving customers", "food service"]),
    ("Customer Service", ["customer service", "customer support", "guest service"]),
    ("Kitchen Maintenance", ["kitchen maintenance", "maintaining kitchen equipment"]),
    ("Waste Management", ["waste management", "waste disposal", "food waste management"]),

    # Retail, Customer Service & Operations
    ("Cash Handling", ["cash handling", "handling cash"]),
    ("Point of Sale", ["point of sale", "pos systems", "pos system"]),
    ("Retail Operations", ["retail operations", "retail management"]),
    ("Merchandising", ["merchandising", "product merchandising"]),
    ("Order Processing", ["order processing", "processing orders"]),
    ("Complaint Handling", ["complaint handling", "handling customer complaints"]),

    # Cleaning & Facilities
    ("Commercial Cleaning", ["commercial cleaning", "office cleaning"]),
    ("Housekeeping", ["housekeeping", "room cleaning"]),
    ("Laundry Operations", ["laundry operations", "laundry services"]),
    ("Sanitation", ["sanitation", "sanitary procedures"]),
    ("Facilities Maintenance", ["facilities maintenance", "building maintenance"]),

    # Driving, Warehousing & Logistics
    ("Driving", ["driving", "safe driving"]),
    ("Valid Driving Licence", ["valid driving licence", "valid driver's license", "driving license"]),
    ("Forklift Operation", ["forklift operation", "operating a forklift", "forklift"]),
    ("Warehouse Operations", ["warehouse operations", "warehouse work"]),
    ("Packing & Packaging", ["packing", "packaging", "packing goods"]),
    ("Loading & Unloading", ["loading and unloading", "loading unloading"]),
    ("Delivery Operations", ["delivery operations", "delivery driving"]),
    ("Supply Chain Management", ["supply chain management", "supply chain"]),

    # Skilled Trades
    ("Electrical Installation", ["electrical installation", "electrical wiring"]),
    ("Plumbing", ["plumbing", "pipe fitting"]),
    ("Welding", ["welding", "metal welding"]),
    ("Painting & Decorating", ["painting and decorating", "painting", "decorating"]),
    ("Masonry", ["masonry", "bricklaying", "brick laying"]),
    ("Construction", ["construction", "construction work"]),
    ("Equipment Maintenance", ["equipment maintenance", "machinery maintenance"]),

    # Education, Childcare & Security
    ("Teaching", ["teaching", "classroom teaching"]),
    ("Lesson Planning", ["lesson planning", "planning lessons"]),
    ("Childcare", ["childcare", "child care", "child supervision"]),
    ("Safeguarding", ["safeguarding", "child safeguarding"]),
    ("Classroom Management", ["classroom management"]),
    ("Security Operations", ["security operations", "security duties"]),
    ("Access Control", ["access control", "visitor access control"]),
    ("CCTV Monitoring", ["cctv monitoring", "cctv operation"]),

    # General Workplace & Kitchen Skills
    ("Knife Skills", ["knife skills", "knife handling", "chopping and cutting", "washing and chopping"]),
    ("Communication", ["communication", "communication skills", "verbal communication", "written communication"]),
    ("Time Management", ["time management", "managing time", "meeting deadlines"]),
    ("Following Instructions", ["follow instructions", "following instructions", "follow recipes", "following recipes"]),
    ("Physical Stamina", ["physical stamina", "stamina", "standing for long", "lifting"]),
    ("Attention to Detail", ["attention to detail", "detail-oriented", "detail oriented"]),
    ("Working Under Pressure", ["fast-paced", "fast paced", "working under pressure", "under pressure"]),
]


# =========================================================
# STOP WORDS
# =========================================================

EXTRA_STOP_WORDS = {
    "etc", "also", "using", "used", "use", "work", "working", "role", "team",
    "ability", "experience", "including", "within", "strong", "excellent",
    "good", "looking", "required", "preferred", "responsibilities", "requirements",
    "qualifications", "candidate", "position", "company", "years", "year",
    "join", "help", "build", "building", "create", "creating", "ensure", "support",
}


# =========================================================
# REGEX SKILL MATCHING
# =========================================================

SYMBOL_SENSITIVE_ALIASES: Dict[str, List[re.Pattern[str]]] = {}

for canonical, aliases in SKILL_TAXONOMY:
    patterns = []

    for alias in aliases:
        escaped = re.escape(alias.lower())
        patterns.append(
            re.compile(
                rf"(?<![a-z0-9]){escaped}(?![a-z0-9])",
                re.IGNORECASE,
            )
        )

    SYMBOL_SENSITIVE_ALIASES[canonical] = patterns


# =========================================================
# SPACY INITIALIZATION
# =========================================================

@lru_cache(maxsize=1)
def get_spacy_nlp() -> Language:
    """Load configured spaCy model once."""

    import spacy

    try:
        return spacy.load(Config.SPACY_MODEL)
    except OSError:
        return spacy.blank("en")


@lru_cache(maxsize=1)
def get_phrase_matcher() -> PhraseMatcher:
    """Build PhraseMatcher for skill extraction."""

    from spacy.matcher import PhraseMatcher

    nlp = get_spacy_nlp()

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

    for canonical, aliases in SKILL_TAXONOMY:
        patterns = [nlp.make_doc(alias) for alias in aliases]
        matcher.add(canonical, patterns)

    return matcher


# =========================================================
# SKILL EXTRACTION
# =========================================================

def extract_skills(text: str) -> List[str]:
    """
    Extract canonical skills from resume or job description.
    """

    if not text:
        return []

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

    return [
        canonical
        for canonical, _ in SKILL_TAXONOMY
        if canonical in found_set
    ]


# =========================================================
# INDUSTRY DETECTION
# =========================================================

INDUSTRY_TERMS: Dict[str, List[str]] = {

    "Information Technology": [
        "software", "developer", "programming", "python",
        "javascript", "database", "network", "cybersecurity",
        "web development",
    ],

    "Kitchen & Hospitality": [
        "kitchen", "chef", "cook", "food preparation",
        "food hygiene", "dishwashing", "catering",
        "restaurant", "food safety",
    ],

    "Construction & Carpentry": [
        "carpenter", "carpentry", "woodworking", "construction",
        "blueprint", "power tools", "cabinet", "plumbing", "welding",
    ],

    "Marketing & Sales": [
        "marketing", "sales", "seo", "social media",
        "lead generation", "campaign", "market research",
        "customer acquisition",
    ],

    "Healthcare": [
        "patient", "nursing", "clinical", "medical",
        "healthcare", "vital signs", "medication", "first aid",
    ],

    "Human Resources & Administration": [
        "recruitment", "human resources", "payroll",
        "employee relations", "administration", "office management",
    ],

    "Accounting & Finance": [
        "accounting", "bookkeeping", "financial reporting",
        "accounts payable", "accounts receivable", "budget", "taxation",
    ],

    "Retail & Customer Service": [
        "retail", "cash handling", "point of sale",
        "customer service", "merchandising", "sales assistant",
    ],

    "Cleaning & Facilities": [
        "housekeeping", "cleaning", "sanitation",
        "laundry", "facilities", "janitorial",
    ],

    "Driving & Logistics": [
        "driver", "driving", "delivery", "warehouse",
        "forklift", "logistics", "loading and unloading",
    ],

    "Education & Childcare": [
        "teaching", "teacher", "lesson planning",
        "childcare", "classroom", "safeguarding",
    ],

    "Security": [
        "security guard", "security operations",
        "cctv", "access control", "patrol",
    ],
}


def _skill_section(first: str, last: str) -> set:
    names = [name for name, _ in SKILL_TAXONOMY]
    return set(names[names.index(first): names.index(last) + 1])


# Skill names that belong to each industry (taken from SKILL_TAXONOMY order).
INDUSTRY_SKILLS: Dict[str, set] = {
    "Information Technology": _skill_section("Python", "Cybersecurity"),
    "Construction & Carpentry": _skill_section("Woodworking", "Repair & Maintenance")
    | _skill_section("Electrical Installation", "Equipment Maintenance"),
    "Marketing & Sales": _skill_section("Digital Marketing", "Negotiation"),
    "Human Resources & Administration": _skill_section("Recruitment", "Record Keeping"),
    "Healthcare": _skill_section("Patient Care", "Vital Signs Monitoring"),
    "Accounting & Finance": _skill_section("Bookkeeping", "Microsoft Excel"),
    "Kitchen & Hospitality": _skill_section("Food Preparation", "Waste Management")
    | {"Knife Skills"},
    "Retail & Customer Service": _skill_section("Cash Handling", "Complaint Handling"),
    "Cleaning & Facilities": _skill_section("Commercial Cleaning", "Facilities Maintenance"),
    "Driving & Logistics": _skill_section("Driving", "Supply Chain Management"),
    "Education & Childcare": _skill_section("Teaching", "Classroom Management"),
    "Security": _skill_section("Security Operations", "CCTV Monitoring"),
}


def detect_industry(text: str) -> Dict[str, Any]:
    """
    Estimate the most likely industry using keyword signals plus the
    number of industry-specific skills found in the text.
    """

    normalized = (text or "").lower()

    counts: Dict[str, int] = {}

    try:
        found_skills = set(extract_skills(text or ""))
    except Exception:
        found_skills = set()

    for industry, terms in INDUSTRY_TERMS.items():

        count = 0

        for term in terms:

            pattern = re.compile(
                rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])",
                re.IGNORECASE,
            )

            if pattern.search(normalized):
                count += 1

        # Skill signals: every industry-specific skill found counts too.
        count += len(found_skills & INDUSTRY_SKILLS.get(industry, set()))

        counts[industry] = count

    if not counts:
        return {
            "industry": "Other / Unclassified",
            "confidence": "low",
            "signalCount": 0,
            "industryCounts": {},
        }

    best_industry = max(counts, key=counts.get)
    best_count = counts[best_industry]

    if best_count == 0:
        best_industry = "Other / Unclassified"
        confidence = "low"

    elif best_count >= 4:
        confidence = "high"

    else:
        confidence = "medium"

    return {
        "industry": best_industry,
        "confidence": confidence,
        "signalCount": best_count,
        "industryCounts": counts,
    }


# =========================================================
# EXPERIENCE EXTRACTION
# =========================================================

def extract_experience_years(text: str) -> float | None:
    """
    Extract explicitly mentioned years of experience.
    """

    if not text:
        return None

    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?experience",

        r"experience\s+(?:of|for)\s+(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
    ]

    values: List[float] = []

    for pattern in patterns:

        for match in re.finditer(pattern, text, re.IGNORECASE):

            try:
                values.append(float(match.group(1)))

            except (TypeError, ValueError):
                continue

    return max(values) if values else None


def extract_experience_evidence(
    text: str,
    max_items: int = 8,
) -> List[str]:
    """
    Extract lines that may contain work / project experience evidence.

    Detects experience headings (e.g. "EXPERIENCE & ACADEMIC PROJECTS")
    and keeps the first lines under them, plus dated roles and
    employment keywords.
    """

    if not text:
        return []

    markers = (
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "internship",
        "worked as",
        "employment",
        "career history",
        "professional background",
        "volunteer",
        "freelance",
        "part-time",
        "part time",
    )

    heading_words = (
        "experience", "projects", "project experience", "internship",
        "work history", "employment", "volunteering",
    )

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]

    results: List[str] = []
    lines_after_heading = 0

    def add(value: str) -> None:
        value = re.sub(r"^[-*•▪–]+\s*", "", value).strip()[:350]
        if value and value not in results:
            results.append(value)

    for line in lines:

        if len(results) >= max_items:
            break

        if not line:
            continue

        lowered = line.lower()

        is_heading = len(line) <= 70 and any(
            word in lowered for word in heading_words
        )

        if is_heading:
            lines_after_heading = 4
            continue

        if lines_after_heading > 0 and len(line) >= 12:
            lines_after_heading -= 1
            add(line)
            continue

        if len(line) < 12:
            continue

        if any(marker in lowered for marker in markers):
            add(line)

        elif re.search(
            r"\b(19|20)\d{2}\s*[-–to]+\s*(present|current|(19|20)\d{2})\b",
            lowered,
        ):
            add(line)

    return results


# =========================================================
# EDUCATION EXTRACTION
# =========================================================

def extract_education_evidence(
    text: str,
    max_items: int = 8,
) -> List[str]:
    """
    Extract lines that may contain education or qualifications.
    """

    if not text:
        return []

    markers = (
        "education",
        "qualification",
        "qualifications",
        "bachelor",
        "degree",
        "b.sc",
        "bsc",
        "bs ",
        "master",
        "m.sc",
        "msc",
        "mba",
        "phd",
        "diploma",
        "certificate",
        "certification",
        "high school",
        "secondary school",
        "matric",
        "intermediate",
        "vocational",
        "apprenticeship",
        "training",
    )

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]

    results: List[str] = []

    for line in lines:

        line = re.sub(r"[*_#`]+", "", line)
        line = re.sub(r"^[-•▪–]+\s*", "", line).strip()

        if len(line) < 4:
            continue

        # A bare heading such as "Qualifications:" is not evidence.
        if line.endswith(":") and len(line.split()) <= 4:
            continue

        lowered = line.lower()

        if any(marker in lowered for marker in markers):
            results.append(line[:350])

        if len(results) >= max_items:
            break

    return results


# =========================================================
# PARTIAL SKILL EVIDENCE
# =========================================================

PARTIAL_FILLER_WORDS = {
    "and", "or", "of", "the", "for", "to", "in", "on", "a", "an", "with",
}


PARTIAL_GENERIC_WORDS = {
    "skills", "skill", "management", "service", "services", "operations",
    "control", "handling", "support", "systems", "system", "work",
}


def find_partial_skill_evidence(
    job_description: str,
    resume_text: str,
    minimum_overlap: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Find possible partial skill evidence using shared alias words.

    These are possible clues, not confirmed skill matches.
    """

    resume_lower = (resume_text or "").lower()
    jd_lower = (job_description or "").lower()

    resume_words = set(
        re.findall(r"[a-z0-9+#.]+", resume_lower)
    )

    partials: List[Dict[str, Any]] = []

    already_found = set(
        extract_skills(resume_text or "")
    )

    for canonical, aliases in SKILL_TAXONOMY:

        if canonical in already_found:
            continue

        jd_has_skill = any(
            re.search(
                rf"(?<![a-z0-9]){re.escape(alias.lower())}(?![a-z0-9])",
                jd_lower,
            )
            for alias in aliases
        )

        if not jd_has_skill:
            continue

        best_alias = None
        best_ratio = 0.0

        for alias in aliases:

            words = set(
                re.findall(r"[a-z0-9+#.]+", alias.lower())
            ) - PARTIAL_FILLER_WORDS

            if len(words) < 2:
                continue

            hits = words & resume_words

            # A shared generic word ("skills", "management") alone is
            # not partial evidence.
            if not (hits - PARTIAL_GENERIC_WORDS):
                continue

            ratio = len(hits) / len(words)

            if (
                0 < ratio < 1
                and ratio >= minimum_overlap
                and ratio > best_ratio
            ):

                best_alias = alias
                best_ratio = ratio

        if best_alias:

            partials.append({
                "skill": canonical,
                "evidence": best_alias,
                "overlap": round(best_ratio * 100),
            })

    return partials


# =========================================================
# TF-IDF TEXT PREPROCESSING
# =========================================================

def preprocess_text_for_tfidf(
    text: str,
) -> Tuple[List[str], int]:
    """
    Tokenize and lemmatize text using spaCy.
    Remove stop words and punctuation.
    """

    if not text:
        return [], 0

    raw_word_count = len([
        word
        for word in text.strip().split()
        if word
    ])

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

        lemma = (
            token.lemma_ or raw_lower
        ).lower().strip("-./")

        if (
            len(lemma) < 2
            or lemma in EXTRA_STOP_WORDS
            or lemma == "-pron-"
        ):
            lemma = raw_lower

        tokens.append(lemma)

    return tokens, raw_word_count