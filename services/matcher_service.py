from __future__ import annotations

from datetime import datetime, timezone
import re
import time
from typing import Any, Dict, List

from services.nlp_service import (
    extract_skills,
    preprocess_text_for_tfidf,
    detect_industry,
    extract_experience_years,
    extract_experience_evidence,
    extract_education_evidence,
    find_partial_skill_evidence,
)


# =========================================================
# SHARED HELPERS
# =========================================================

def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        return ", ".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    return str(value).strip()


def normalize_evidence(value: Any) -> List[str]:
    if not value:
        return []

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if isinstance(value, dict):
        text = (
            value.get("text")
            or value.get("evidence")
            or value.get("description")
            or value.get("value")
        )
        return [str(text).strip()] if text else []

    if isinstance(value, (list, tuple, set)):
        results = []

        for item in value:
            if isinstance(item, dict):
                text = (
                    item.get("text")
                    or item.get("evidence")
                    or item.get("description")
                    or item.get("value")
                )
                if text:
                    results.append(str(text).strip())
            elif item:
                results.append(str(item).strip())

        return [item for item in results if item]

    return []


def normalize_skill_list(skills: Any) -> List[str]:
    if not skills:
        return []

    results = []

    for skill in skills:
        if isinstance(skill, dict):
            skill = skill.get("skill") or skill.get("name") or skill.get("label")

        if skill:
            cleaned = str(skill).strip()
            if cleaned and cleaned.lower() not in {
                item.lower() for item in results
            }:
                results.append(cleaned)

    return results


# =========================================================
# REQUIREMENT / PARTIAL-MATCH HELPERS
# =========================================================

# If the skill taxonomy finds fewer job skills than this, the job
# description's own requirement phrases are added so that the Missing
# Skills list is never artificially short (e.g. non-IT jobs).
MIN_JD_SKILLS = 6

_FILLER_WORDS = {
    "the", "and", "for", "with", "our", "you", "your", "are", "will",
    "this", "that", "from", "have", "has", "who", "all", "any", "can",
    "must", "should", "able", "ability", "good", "strong", "great",
    "work", "working", "role", "job", "team", "looking", "required",
    "requirements", "preferred", "skills", "skill", "experience",
    "knowledge", "including", "such", "also", "etc", "per", "not",
    "new", "well", "more", "other", "their", "them", "than", "into",
    "need", "needs", "someone", "every", "morning", "today", "here",
    "nothing", "useful", "hello", "world", "day", "days", "time", "make",
    "take", "get", "give", "come", "like", "just", "very", "much", "many",
    "some", "when", "what", "where", "which", "while", "about", "after",
    "before", "over", "under", "again", "only", "then", "once", "each",
    "both", "same", "being", "does", "doing", "done", "were", "was",
    "would", "could", "may", "might", "shall", "applicants", "applicant",
    "seeking", "wanted", "want", "hiring", "join", "ideal", "candidate",
}

# job skill (lowercase) -> related resume skills that count as PARTIAL
# evidence. Extend this map for your own skill taxonomy.
RELATED_SKILLS: Dict[str, List[str]] = {
    "aws": ["Docker", "Linux", "Google Cloud", "Azure"],
    "azure": ["AWS", "Google Cloud", "Docker", "Linux"],
    "google cloud": ["AWS", "Azure", "Docker", "Linux"],
    "kubernetes": ["Docker", "Linux"],
    "ci/cd": ["Git", "Docker", "Unit Testing"],
    "team collaboration": ["Agile / Scrum", "Project Management"],
    "time management": ["Agile / Scrum", "Project Management"],
    "communication": ["Agile / Scrum", "Team Collaboration", "Technical Writing"],
    "following instructions": ["Unit Testing", "Git", "Agile / Scrum"],
    "attention to detail": ["Unit Testing", "Data Analysis"],
    "working under pressure": ["Agile / Scrum"],
    "problem solving": ["Data Analysis", "Data Structures & Algorithms"],
    "customer service": ["Sales", "Complaint Handling", "Customer Relationship Management"],
}


def content_words(text: str) -> set:
    return {
        word
        for word in re.findall(r"[a-z0-9+#./-]{3,}", (text or "").lower())
        if word not in _FILLER_WORDS
    }


def phrase_overlap(phrase: str, resume_text: str):
    """Share of a requirement phrase's content words found in the resume."""
    words = content_words(phrase)

    if not words:
        return 0.0, []

    hits = sorted(words & content_words(resume_text))
    return len(hits) / len(words), hits


def keyword_requirements(jd_tokens: List[str], limit: int = 10) -> List[str]:
    """Last resort: most frequent meaningful job keywords."""
    from collections import Counter

    counts = Counter(
        token for token in jd_tokens
        if len(token) >= 4
        and token.isalpha()
        and token.lower() not in _FILLER_WORDS
    )

    return [word.title() for word, _ in counts.most_common(limit)]


def related_skill_partials(
    missing_skills: List[str],
    resume_skills: List[str],
    already: set,
) -> List[Dict[str, Any]]:

    resume_by_key = {skill.lower(): skill for skill in resume_skills}
    results = []

    for skill in missing_skills:
        key = skill.lower()

        if key in already or key not in RELATED_SKILLS:
            continue

        found = [
            resume_by_key[name.lower()]
            for name in RELATED_SKILLS[key]
            if name.lower() in resume_by_key
        ]

        if found:
            results.append({
                "skill": skill,
                "evidence": ", ".join(found),
                "reason": (
                    f"Related skills in the resume ({', '.join(found)}) "
                    f"may support {skill}, but it is not stated directly."
                ),
            })

    return results


# =========================================================
# TF-IDF SIMILARITY
# =========================================================

def compute_tfidf_cosine_similarity(
    resume_tokens: List[str],
    jd_tokens: List[str],
) -> int:

    if not resume_tokens or not jd_tokens:
        return 0

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    resume_doc = " ".join(resume_tokens)
    jd_doc = " ".join(jd_tokens)

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        lowercase=False,
        token_pattern=r"(?u)\b[\w+#./-]{2,}\b",
    )

    try:
        matrix = vectorizer.fit_transform([resume_doc, jd_doc])
        similarity = cosine_similarity(matrix[0:1], matrix[1:2])
        score = float(similarity[0][0])

    except ValueError:
        return 0

    return max(0, min(100, round(score * 100)))


# =========================================================
# SCORE INTERPRETATION
# =========================================================

def interpret_match_score(score: int) -> Dict[str, str]:

    if score >= 80:
        return {
            "label": "Excellent Match",
            "tone": "excellent",
            "description": (
                "Your resume aligns strongly with the identified "
                "requirements of this job."
            ),
        }

    if score >= 65:
        return {
            "label": "Strong Match",
            "tone": "strong",
            "description": (
                "Your profile covers many of the identified job "
                "requirements. Some improvements may further "
                "strengthen your application."
            ),
        }

    if score >= 45:
        return {
            "label": "Moderate Match",
            "tone": "moderate",
            "description": (
                "Your resume shares some relevant skills and "
                "terminology with the job description, but "
                "several gaps remain."
            ),
        }

    if score < 15:
        return {
            "label": "No Significant Match",
            "tone": "none",
            "description": (
                "Almost none of the job requirements were found in "
                "your resume. The full list of required skills that "
                "were not found is shown below."
            ),
        }

    return {
        "label": "Low Match",
        "tone": "low",
        "description": (
            "Your resume has limited alignment with the "
            "identified requirements of this job."
        ),
    }


# =========================================================
# FALLBACK REQUIREMENT EXTRACTION
# =========================================================

def extract_fallback_requirements(
    job_description: str,
    max_items: int = 20,
) -> List[str]:

    if not job_description:
        return []

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in job_description.splitlines()
    ]

    markers = (
        "requirements",
        "qualifications",
        "what you will need",
        "what we're looking for",
        "what we are looking for",
        "required skills",
        "essential skills",
        "key responsibilities",
        "responsibilities",
        "must have",
    )

    stop_markers = (
        "about us",
        "benefits",
        "what we offer",
        "company overview",
    )

    candidates = []
    inside_requirements = False

    for line in lines:
        if not line:
            continue

        lowered = line.lower()

        if any(marker in lowered for marker in markers):
            inside_requirements = True
            continue

        if any(lowered.startswith(marker) for marker in stop_markers):
            inside_requirements = False

        is_bullet = bool(
            re.match(r"^(?:[-*•▪]|\d+[.)])\s*", line)
        )

        requirement_language = any(
            phrase in lowered
            for phrase in (
                "ability to",
                "knowledge of",
                "experience with",
                "experience in",
                "proficient in",
                "familiar with",
                "responsible for",
                "must be able",
                "good communication",
                "attention to detail",
                "able to work",
            )
        )

        if not (is_bullet or inside_requirements or requirement_language):
            continue

        cleaned = re.sub(
            r"^(?:[-*•▪]|\d+[.)])\s*",
            "",
            line,
        ).strip(" .;:-")

        words = cleaned.split()

        if len(words) < 2 or len(words) > 20:
            continue

        if cleaned.lower() not in {
            item.lower() for item in candidates
        }:
            candidates.append(cleaned)

        if len(candidates) >= max_items:
            break

    return candidates


# =========================================================
# PARTIAL SKILL ANALYSIS
# =========================================================

def calculate_partial_matches(
    jd_skills: List[str],
    resume_skills: List[str],
    resume_text: str,
    job_description: str,
) -> List[Dict[str, Any]]:

    try:
        detected = find_partial_skill_evidence(
            job_description,
            resume_text,
        )
    except Exception:
        detected = []

    resume_lookup = {skill.lower() for skill in resume_skills}
    missing_lookup = {skill.lower() for skill in jd_skills}

    results = []
    seen = set()

    for item in detected or []:
        if not isinstance(item, dict):
            continue

        skill = normalize_text(item.get("skill"))

        if not skill:
            continue

        skill_key = skill.lower()

        if skill_key not in missing_lookup:
            continue

        if skill_key in resume_lookup or skill_key in seen:
            continue

        evidence = (
            item.get("evidence")
            or item.get("text")
            or item.get("description")
            or ""
        )

        results.append({
            "skill": skill,
            "evidence": normalize_text(evidence),
            "reason": normalize_text(
                item.get("reason") or item.get("explanation")
            ),
        })

        seen.add(skill_key)

    return results


# =========================================================
# EXPERIENCE ANALYSIS
# =========================================================

def analyze_experience(
    resume_text: str,
    job_description: str,
) -> Dict[str, Any]:

    resume_years = extract_experience_years(resume_text)
    required_years = extract_experience_years(job_description)

    evidence = normalize_evidence(
        extract_experience_evidence(resume_text)
    )

    if resume_years is not None and required_years is not None:

        meets_requirement = resume_years >= required_years

        if meets_requirement:
            status = "Meets stated experience requirement"
            message = (
                f"The resume indicates {resume_years} years of experience, "
                f"compared with {required_years} years requested."
            )
        else:
            status = "Below stated experience requirement"
            message = (
                f"The resume indicates {resume_years} years of experience, "
                f"while the job description requests {required_years} years. "
                "Relevant internships, projects, and practical training "
                "may also be useful to highlight."
            )

    elif resume_years is not None:

        meets_requirement = None
        status = "Experience duration found in resume"
        message = (
            f"The resume indicates {resume_years} years of experience. "
            "The job description does not state a clear number of "
            "required experience years."
        )

    elif required_years is not None:

        meets_requirement = None
        status = "Required experience identified; resume duration unclear"
        message = (
            f"The job description requests {required_years} years of "
            "experience, but the resume does not state a clear duration."
        )

    elif evidence:

        meets_requirement = None
        status = "Work experience evidence found"
        message = (
            "Work-related information was found in the resume, "
            "but a clear experience duration could not be established."
        )

    else:

        meets_requirement = None
        status = "No clear work experience evidence found"
        message = (
            "No clear work experience duration or employment evidence "
            "was identified in the resume."
        )

    return {
        "resumeYears": resume_years,
        "requiredYears": required_years,
        "meetsRequirement": meets_requirement,
        "status": status,
        "message": message,
        "evidence": evidence,
    }


# =========================================================
# EDUCATION ANALYSIS
# =========================================================

def analyze_education(
    resume_text: str,
    job_description: str,
) -> Dict[str, Any]:

    resume_education = normalize_evidence(
        extract_education_evidence(resume_text)
    )

    required_education = normalize_evidence(
        extract_education_evidence(job_description)
    )

    if resume_education and required_education:

        status = "Education information found in both documents"

        message = (
            "Education details were identified in the resume and job "
            "description. Compare the two to determine "
            "whether the candidate meets the stated requirement."
        )

    elif resume_education:

        status = "Education information found in resume"

        message = (
            "The resume contains education information, but no specific "
            "education requirement was clearly identified in the job "
            "description."
        )

    elif required_education:

        status = "Job education requirement not found in resume"

        message = (
            "The job description mentions education or qualifications, "
            "but corresponding education evidence was not identified "
            "in the resume."
        )

    else:

        status = "Education information not clearly identified"

        message = (
            "No clear education information was detected in either "
            "document. Add relevant qualifications to the resume "
            "if applicable."
        )

    return {
        "resumeEducation": resume_education,
        "requiredEducation": required_education,
        "status": status,
        "message": message,
        "educationFound": bool(resume_education),
        "requirementFound": bool(required_education),
    }


# =========================================================
# INDUSTRY COMPARISON
# =========================================================

def analyze_industries(
    resume_text: str,
    job_description: str,
) -> Dict[str, Any]:

    resume_result = detect_industry(resume_text) or {}
    job_result = detect_industry(job_description) or {}

    resume_label = (
        resume_result.get("industry") or "Other / Unclassified"
    )

    job_label = (
        job_result.get("industry") or "Other / Unclassified"
    )

    classified = (
        resume_label != "Other / Unclassified"
        and job_label != "Other / Unclassified"
    )

    different = classified and resume_label != job_label

    if different:

        message = (
            f"The resume appears to belong to {resume_label}, while "
            f"the job description appears to belong to {job_label}. "
            "This indicates a possible cross-industry career transition. "
            "The system has still completed the skill, experience, "
            "and education analysis."
        )

    elif classified:

        message = (
            f"Both documents appear to relate to {resume_label}. "
            "The industry classification is consistent."
        )

    else:

        message = (
            "There is not enough industry-specific information to "
            "confidently classify both documents. Skill and requirement "
            "comparison has still been performed."
        )

    return {
        "resumeIndustry": resume_label,
        "jobIndustry": job_label,
        "differentIndustries": different,
        "isDifferentIndustry": different,
        "classificationAvailable": classified,
        "message": message,
        "resumeConfidence": resume_result.get("confidence", 0),
        "jobConfidence": job_result.get("confidence", 0),
    }


# =========================================================
# RECOMMENDATIONS
# =========================================================

def generate_recommendations(
    matched_skills: List[str],
    missing_skills: List[str],
    partial_skills: List[Dict[str, Any]],
    industry_analysis: Dict[str, Any],
    experience_analysis: Dict[str, Any],
    education_analysis: Dict[str, Any],
    cosine_pct: int,
) -> List[str]:

    recommendations = []

    if missing_skills:
        recommendations.append(
            "Review the following job requirements and develop relevant "
            "knowledge or practical experience: "
            + ", ".join(missing_skills[:10])
            + "."
        )

    if partial_skills:
        names = [item["skill"] for item in partial_skills]

        recommendations.append(
            "Possible partial evidence was found for "
            + ", ".join(names[:5])
            + ". Add clear examples or practical experience if you "
            "genuinely possess these skills."
        )

    if industry_analysis.get("differentIndustries"):
        recommendations.insert(
            0,
            "Your resume (" + industry_analysis["resumeIndustry"]
            + ") and the target role (" + industry_analysis["jobIndustry"]
            + ") belong to different industries. If you want this role, "
            "highlight transferable skills, relevant training, and any "
            "genuine practical experience in the target industry. "
            "Otherwise, search for jobs closer to your own field.",
        )

    if not matched_skills:
        recommendations.append(
            "No job requirements were fully matched. Start with the "
            "highest-priority missing skills listed above and gain "
            "genuine training or experience in them."
        )

    if experience_analysis.get("meetsRequirement") is False:
        recommendations.append(
            "The experience duration stated in the resume is below "
            "the job's stated requirement. Highlight relevant "
            "internships, projects, voluntary work, and practical training."
        )

    elif not experience_analysis.get("evidence"):
        recommendations.append(
            "Add relevant employment history, internships, practical "
            "training, or project experience where applicable."
        )

    if (
        education_analysis.get("requirementFound")
        and not education_analysis.get("educationFound")
    ):
        recommendations.append(
            "The job description includes education requirements that "
            "were not identified in the resume. Include your relevant "
            "qualifications if you have them."
        )

    if cosine_pct < 40:
        recommendations.append(
            "Improve alignment by accurately describing relevant duties, "
            "tools, responsibilities, and achievements using terminology "
            "that reflects the target job."
        )

    if matched_skills:
        recommendations.append(
            "Support your matching skills with measurable achievements "
            "and specific examples from previous work or projects."
        )

    if not recommendations:
        recommendations.append(
            "Continue strengthening your resume with clear achievements, "
            "relevant skills, and practical examples."
        )

    return recommendations


# =========================================================
# MAIN RESUME ANALYSIS
# =========================================================

def analyze_resume_against_job(
    resume_text: str,
    job_description: str,
    file_name: str,
    file_size_bytes: int,
    file_type: str,
) -> Dict[str, Any]:

    resume_text = resume_text or ""
    job_description = job_description or ""

    # 1. Extract skills from both documents.
    resume_skills = normalize_skill_list(
        extract_skills(resume_text)
    )

    jd_skills = normalize_skill_list(
        extract_skills(job_description)
    )

    resume_tokens, resume_word_count = (
        preprocess_text_for_tfidf(resume_text)
    )

    jd_tokens, jd_word_count = (
        preprocess_text_for_tfidf(job_description)
    )

    # 2. Requirement phrases from the job description itself.
    #    Added whenever the skill taxonomy finds too few job skills
    #    (e.g. a Kitchen Assistant job), so the analysis stays complete.
    fallback_requirements = []

    if len(jd_skills) < MIN_JD_SKILLS:
        known = {skill.lower() for skill in jd_skills}

        for item in extract_fallback_requirements(job_description, 10):
            if len(item.split()) > 12:
                continue

            if item.lower() not in known:
                fallback_requirements.append(item)
                known.add(item.lower())

        jd_skills = jd_skills + fallback_requirements

    # Last resort: the list of required skills is never empty.
    if not jd_skills:
        fallback_requirements = keyword_requirements(jd_tokens)
        jd_skills = fallback_requirements.copy()

    resume_lookup = {skill.lower() for skill in resume_skills}
    jd_lookup = {skill.lower() for skill in jd_skills}
    phrase_lookup = {skill.lower() for skill in fallback_requirements}

    matched_skills = []
    missing_skills = []
    phrase_partials = []

    for skill in jd_skills:
        key = skill.lower()

        if key in resume_lookup:
            matched_skills.append(skill)
            continue

        if key in phrase_lookup:
            ratio, hits = phrase_overlap(skill, resume_text)

            if ratio >= 0.8:
                matched_skills.append(skill)
                continue

            if ratio >= 0.4:
                phrase_partials.append({
                    "skill": skill,
                    "evidence": ", ".join(hits),
                    "reason": (
                        "Some terms from this requirement appear in "
                        "the resume, but not the complete requirement."
                    ),
                })

        missing_skills.append(skill)

    bonus_skills = [
        skill for skill in resume_skills
        if skill.lower() not in jd_lookup
    ]

    # 3. Partial skill evidence (NLP service + phrase overlap +
    #    related-skill map). Partial skills stay in missing_skills too,
    #    because they are not fully confirmed.
    partial_evidence = calculate_partial_matches(
        missing_skills,
        resume_skills,
        resume_text,
        job_description,
    )

    seen_partial = {item["skill"].lower() for item in partial_evidence}

    for item in phrase_partials:
        if item["skill"].lower() not in seen_partial:
            partial_evidence.append(item)
            seen_partial.add(item["skill"].lower())

    partial_evidence.extend(
        related_skill_partials(
            missing_skills,
            resume_skills,
            seen_partial,
        )
    )

    # Keep a simple string list for the dashboard skill chips.
    partial_matched_skills = [
        item["skill"] for item in partial_evidence
    ]

    # 4. TF-IDF similarity.
    cosine_pct = compute_tfidf_cosine_similarity(
        resume_tokens,
        jd_tokens,
    )

    # 5. Keyword overlap.
    resume_vocab = set(resume_tokens)
    jd_vocab = set(jd_tokens)

    shared_terms = resume_vocab.intersection(jd_vocab)
    shared_term_count = len(shared_terms)

    keyword_overlap = (
        min(100, round((shared_term_count / len(jd_vocab)) * 100))
        if jd_vocab else 0
    )

    # 6. Skill coverage and overall score.
    skill_analysis_available = bool(jd_skills)

    if skill_analysis_available:
        skill_coverage = round(
            (len(matched_skills) / len(jd_skills)) * 100
        )

        overall_score = round(
            skill_coverage * 0.65 + cosine_pct * 0.35
        )

        skill_analysis_message = (
            f"Identified {len(jd_skills)} job requirements. "
            f"{len(matched_skills)} matched, "
            f"{len(missing_skills)} missing, and "
            f"{len(partial_matched_skills)} partially matched."
        )

    else:
        skill_coverage = 0
        overall_score = 0

        skill_analysis_message = (
            "No recognizable skills or requirement phrases were "
            "detected in the job description. The skill analysis "
            "is limited; review the job description."
        )

    overall_score = max(0, min(100, overall_score))
    interpretation = interpret_match_score(overall_score)

    # 7. Industry comparison.
    industry_analysis = analyze_industries(
        resume_text,
        job_description,
    )

    if industry_analysis["differentIndustries"]:
        interpretation["description"] += (
            " Note: the resume (" + industry_analysis["resumeIndustry"]
            + ") and the job (" + industry_analysis["jobIndustry"]
            + ") belong to different industries, which strongly "
            "affects the score."
        )

    # 8. Experience comparison.
    experience_analysis = analyze_experience(
        resume_text,
        job_description,
    )

    # 9. Education comparison.
    education_analysis = analyze_education(
        resume_text,
        job_description,
    )

    # 10. Strengths.
    strengths = []

    if matched_skills:
        strengths.append(
            "Matching skills identified: "
            + ", ".join(matched_skills[:8])
            + "."
        )

    if bonus_skills:
        strengths.append(
            "Additional skills detected in your resume: "
            + ", ".join(bonus_skills[:8])
            + "."
        )

    if experience_analysis["evidence"]:
        strengths.append(
            "Work experience information was found in the resume."
        )

    if education_analysis["educationFound"]:
        strengths.append(
            "Education or qualification information was found."
        )

    if not strengths:
        strengths.append(
            "The resume was successfully processed. However, no "
            "direct matching skills were identified."
        )

    strengths.append(
        f"TF-IDF text similarity: {cosine_pct}%."
    )

    # 11. Recommendations.
    recommendations = generate_recommendations(
        matched_skills,
        missing_skills,
        partial_evidence,
        industry_analysis,
        experience_analysis,
        education_analysis,
        cosine_pct,
    )

    # 12. Overview.
    industry_note = ""

    if industry_analysis["differentIndustries"]:
        industry_note = (
            " The resume and job description appear to belong "
            "to different industries."
        )

    overview = (
        f'SkillAlign analyzed {resume_word_count} words from '
        f'"{file_name}" against a {jd_word_count}-word job description. '
        f'{len(matched_skills)} of {len(jd_skills)} identified job '
        f'requirements matched the resume. '
        f'{len(missing_skills)} requirements were identified as missing. '
        f'{len(partial_matched_skills)} possible partial matches were found. '
        f'Text similarity was {cosine_pct}%, and the overall match score '
        f'was {overall_score}%.{industry_note}'
    )

    preview = (
        resume_text[:260].strip() + "..."
        if len(resume_text) > 260
        else resume_text
    )

    # 13. Complete response.
    return {
        "id": f"scan_{int(time.time() * 1000)}",
        "analyzedAt": datetime.now(timezone.utc).isoformat(),

        "fileName": file_name,
        "fileSizeBytes": file_size_bytes,
        "fileType": file_type,

        "overallScore": overall_score,
        "skillCoverage": skill_coverage,
        "cosineSimilarity": cosine_pct,
        "keywordOverlap": keyword_overlap,

        "interpretation": interpretation,

        "skillAnalysisAvailable": skill_analysis_available,
        "skillAnalysisMessage": skill_analysis_message,

        "resumeSkills": resume_skills,
        "jdSkills": jd_skills,
        "matchedSkills": matched_skills,
        "missingSkills": missing_skills,
        "bonusSkills": bonus_skills,

        # Strings for dashboard chips.
        "partialMatchedSkills": partial_matched_skills,

        # Detailed partial evidence for expanded UI/report use.
        "partialSkillEvidence": partial_evidence,

        "fallbackRequirements": fallback_requirements,

        "industryAnalysis": industry_analysis,
        "experienceAnalysis": experience_analysis,
        "educationAnalysis": education_analysis,

        "summary": {
            "overview": overview,
            "strengths": strengths,
            "recommendations": recommendations,
        },

        "stats": {
            "resumeWordCount": resume_word_count,
            "jdWordCount": jd_word_count,
            "sharedTermCount": shared_term_count,
            "totalJdKeywords": len(jd_vocab),
            "totalJdSkills": len(jd_skills),
            "matchedSkillsCount": len(matched_skills),
            "missingSkillsCount": len(missing_skills),
            "partialMatchesCount": len(partial_matched_skills),
            "extractedTextPreview": preview,
        },
    }