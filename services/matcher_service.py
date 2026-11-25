from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any, Dict, List

from services.nlp_service import extract_skills, preprocess_text_for_tfidf


def compute_tfidf_cosine_similarity(resume_tokens: List[str], jd_tokens: List[str]) -> int:
    """Compute L2-normalized TF-IDF cosine similarity (0-100) using scikit-learn."""
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
        token_pattern=r"(?u)\b[\w+#.\-/]{2,}\b",
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([resume_doc, jd_doc])
        sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        score = float(sim_matrix[0][0])
    except ValueError:
        return 0

    return max(0, min(100, round(score * 100)))


def interpret_match_score(score: int) -> Dict[str, str]:
    """Return human-readable interpretation metadata for a match score."""
    if score >= 80:
        return {
            "label": "Excellent Match",
            "tone": "excellent",
            "description": (
                "Your resume aligns strongly with the target role's core skills, "
                "terminology, and technical requirements."
            ),
        }
    if score >= 65:
        return {
            "label": "Strong Match",
            "tone": "strong",
            "description": (
                "Your profile covers most key job competencies. Adding a few missing "
                "target keywords can further elevate your fit."
            ),
        }
    if score >= 45:
        return {
            "label": "Moderate Match",
            "tone": "moderate",
            "description": (
                "You share foundational skills with this role, though several required "
                "technologies or domain phrases are missing."
            ),
        }
    return {
        "label": "Low Match",
        "tone": "low",
        "description": (
            "Significant skill and keyword gaps were detected between this resume "
            "and the target job description."
        ),
    }


def analyze_resume_against_job(
    resume_text: str,
    job_description: str,
    file_name: str,
    file_size_bytes: int,
    file_type: str,
) -> Dict[str, Any]:
    """Run full spaCy skill matching and scikit-learn TF-IDF cosine similarity pipeline."""
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)

    resume_skill_set = set(resume_skills)
    jd_skill_set = set(jd_skills)

    matched_skills = [s for s in jd_skills if s in resume_skill_set]
    missing_skills = [s for s in jd_skills if s not in resume_skill_set]
    bonus_skills = [s for s in resume_skills if s not in jd_skill_set]

    resume_tokens, resume_word_count = preprocess_text_for_tfidf(resume_text)
    jd_tokens, jd_word_count = preprocess_text_for_tfidf(job_description)

    cosine_pct = compute_tfidf_cosine_similarity(resume_tokens, jd_tokens)

    resume_vocab = set(resume_tokens)
    jd_vocab = set(jd_tokens)
    shared_term_count = len(resume_vocab.intersection(jd_vocab))

    keyword_overlap = (
        min(100, round((shared_term_count / len(jd_vocab)) * 100)) if jd_vocab else 0
    )

    skill_coverage = (
        round((len(matched_skills) / len(jd_skills)) * 100) if jd_skills else cosine_pct
    )

    overall_score = (
        min(100, round(skill_coverage * 0.65 + cosine_pct * 0.35))
        if jd_skills
        else cosine_pct
    )

    interpretation = interpret_match_score(overall_score)

    strengths: List[str] = []
    if matched_skills:
        strengths.append(
            f"Matched {len(matched_skills)} of {len(jd_skills)} identified job requirements "
            f"({skill_coverage}% skill coverage), including {', '.join(matched_skills[:4])}."
        )
    else:
        strengths.append(
            f"Identified {len(resume_skills)} distinct technical and professional skills in your uploaded resume."
        )

    strengths.append(
        f"scikit-learn TF-IDF cosine similarity reached {cosine_pct}%, with {shared_term_count} shared lemmatized terms across both documents."
    )

    if bonus_skills:
        strengths.append(
            f"Additional transferable skills detected beyond the job brief: {', '.join(bonus_skills[:4])}."
        )

    recommendations: List[str] = []
    if missing_skills:
        recommendations.append(
            f"Prioritize adding evidence or project bullets for missing job skills: {', '.join(missing_skills[:5])}."
        )
    elif jd_skills:
        recommendations.append(
            "All structured skills extracted from the job description are already represented in your resume."
        )

    if cosine_pct < 60:
        recommendations.append(
            "Mirror more domain-specific phrasing and action verbs from the job description to raise TF-IDF textual alignment."
        )
    else:
        recommendations.append(
            "Quantify key achievements with measurable outcomes alongside your matched technical stack to stand out during screening."
        )

    if jd_skills:
        overview = (
            f'SkillAlign analyzed {resume_word_count} words from "{file_name}" against a '
            f"{jd_word_count}-word job description. Your resume matched {len(matched_skills)} of "
            f"{len(jd_skills)} required skills and achieved a {cosine_pct}% TF-IDF cosine "
            f"similarity score, yielding an overall {overall_score}% match."
        )
    else:
        overview = (
            f'SkillAlign analyzed {resume_word_count} words from "{file_name}" against a '
            f"{jd_word_count}-word job description, achieving a {cosine_pct}% TF-IDF cosine similarity score."
        )

    preview = f"{resume_text[:260].strip()}…" if len(resume_text) > 260 else resume_text

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
        "resumeSkills": resume_skills,
        "jdSkills": jd_skills,
        "matchedSkills": matched_skills,
        "missingSkills": missing_skills,
        "bonusSkills": bonus_skills,
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
            "extractedTextPreview": preview,
        },
    }
