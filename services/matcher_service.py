
from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any, Dict, List

from services.nlp_service import (
    extract_skills,
    preprocess_text_for_tfidf,
)


def compute_tfidf_cosine_similarity(
    resume_tokens: List[str],
    jd_tokens: List[str],
) -> int:
    """Compute TF-IDF cosine similarity as a percentage."""

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
        tfidf_matrix = vectorizer.fit_transform(
            [resume_doc, jd_doc]
        )

        similarity = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:2],
        )

        score = float(similarity[0][0])

    except ValueError:
        return 0

    return max(0, min(100, round(score * 100)))


def interpret_match_score(score: int) -> Dict[str, str]:
    """Return human-readable match score interpretation."""

    if score >= 80:
        return {
            "label": "Excellent Match",
            "tone": "excellent",
            "description": (
                "Your resume aligns strongly with the target role's "
                "identified skills and job requirements."
            ),
        }

    if score >= 65:
        return {
            "label": "Strong Match",
            "tone": "strong",
            "description": (
                "Your profile covers most identified job requirements. "
                "Adding evidence for missing skills may improve your fit."
            ),
        }

    if score >= 45:
        return {
            "label": "Moderate Match",
            "tone": "moderate",
            "description": (
                "Your resume shares some relevant skills and terminology "
                "with the job description, but several gaps remain."
            ),
        }

    return {
        "label": "Low Match",
        "tone": "low",
        "description": (
            "Your resume has limited alignment with the identified "
            "requirements of this job description."
        ),
    }


def analyze_resume_against_job(
    resume_text: str,
    job_description: str,
    file_name: str,
    file_size_bytes: int,
    file_type: str,
) -> Dict[str, Any]:
    """
    Analyze a resume against a job description using:
    - spaCy-based skill extraction
    - Matched and missing skill identification
    - TF-IDF cosine similarity
    - 65% skill coverage and 35% text similarity
    """

    # ----------------------------------------
    # 1. Extract skills from both documents
    # ----------------------------------------

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)

    resume_skill_set = set(resume_skills)
    jd_skill_set = set(jd_skills)

    matched_skills = [
        skill for skill in jd_skills
        if skill in resume_skill_set
    ]

    missing_skills = [
        skill for skill in jd_skills
        if skill not in resume_skill_set
    ]

    bonus_skills = [
        skill for skill in resume_skills
        if skill not in jd_skill_set
    ]

    # ----------------------------------------
    # 2. Calculate TF-IDF similarity
    # ----------------------------------------

    resume_tokens, resume_word_count = (
        preprocess_text_for_tfidf(resume_text)
    )

    jd_tokens, jd_word_count = (
        preprocess_text_for_tfidf(job_description)
    )

    cosine_pct = compute_tfidf_cosine_similarity(
        resume_tokens,
        jd_tokens,
    )

    # ----------------------------------------
    # 3. Calculate keyword overlap
    # ----------------------------------------

    resume_vocab = set(resume_tokens)
    jd_vocab = set(jd_tokens)

    shared_term_count = len(
        resume_vocab.intersection(jd_vocab)
    )

    keyword_overlap = (
        min(
            100,
            round(
                (shared_term_count / len(jd_vocab)) * 100
            ),
        )
        if jd_vocab
        else 0
    )

    # ----------------------------------------
    # 4. Calculate skill coverage and score
    # ----------------------------------------

    skill_analysis_available = len(jd_skills) > 0

    if skill_analysis_available:
        skill_coverage = round(
            (len(matched_skills) / len(jd_skills)) * 100
        )

        overall_score = min(
            100,
            round(
                skill_coverage * 0.65
                + cosine_pct * 0.35
            ),
        )

        skill_analysis_message = (
            f"Identified {len(jd_skills)} job skills "
            f"and matched {len(matched_skills)}."
        )

    else:
        # Do not treat an empty skill list as a successful match.
        skill_coverage = 0
        overall_score = 0

        skill_analysis_message = (
            "No recognized skills were detected in the job "
            "description. Skill matching and the overall score "
            "are unavailable. Expand the skill taxonomy or "
            "use a job description with clearer skill requirements."
        )

    interpretation = interpret_match_score(overall_score)

    # ----------------------------------------
    # 5. Generate strengths
    # ----------------------------------------

    strengths: List[str] = []

    if skill_analysis_available:
        strengths.append(
            f"Matched {len(matched_skills)} of "
            f"{len(jd_skills)} identified job skills "
            f"({skill_coverage}% skill coverage)."
        )

        if matched_skills:
            strengths.append(
                "Matching skills include: "
                + ", ".join(matched_skills[:5])
                + "."
            )

    else:
        strengths.append(
            "Structured skill analysis could not be completed "
            "because no recognized job skills were detected."
        )

    strengths.append(
        f"TF-IDF cosine similarity reached {cosine_pct}%, "
        f"with {shared_term_count} shared terms across "
        f"both documents."
    )

    if bonus_skills:
        strengths.append(
            "Additional resume skills detected: "
            + ", ".join(bonus_skills[:5])
            + "."
        )

    # ----------------------------------------
    # 6. Generate recommendations
    # ----------------------------------------

    recommendations: List[str] = []

    if not skill_analysis_available:
        recommendations.append(
            "Review the job description and add its relevant "
            "professional or technical skills to the skill taxonomy."
        )

        recommendations.append(
            "Skill coverage and the overall match score should "
            "not be interpreted until job skills are detected."
        )

    elif missing_skills:
        recommendations.append(
            "Consider adding evidence or relevant experience "
            "for these missing job skills: "
            + ", ".join(missing_skills[:5])
            + "."
        )

    else:
        recommendations.append(
            "All structured skills identified in the job "
            "description are represented in your resume."
        )

    if cosine_pct < 60:
        recommendations.append(
            "Consider using relevant industry terminology "
            "and action verbs from the job description "
            "where they accurately describe your experience."
        )
    else:
        recommendations.append(
            "Support your relevant skills with measurable "
            "achievements and practical work examples."
        )

    # ----------------------------------------
    # 7. Generate analysis overview
    # ----------------------------------------

    if skill_analysis_available:
        overview = (
            f'SkillAlign analyzed {resume_word_count} words '
            f'from "{file_name}" against a '
            f"{jd_word_count}-word job description. "
            f"Your resume matched {len(matched_skills)} "
            f"of {len(jd_skills)} identified job skills "
            f"and achieved {cosine_pct}% TF-IDF similarity, "
            f"resulting in an overall match score of "
            f"{overall_score}%."
        )

    else:
        overview = (
            f'SkillAlign analyzed {resume_word_count} words '
            f'from "{file_name}" against a '
            f"{jd_word_count}-word job description. "
            f"The text similarity score is {cosine_pct}%, "
            f"but no recognized job skills were detected. "
            f"A reliable overall skill match score "
            f"could not be calculated."
        )

    # ----------------------------------------
    # 8. Extract resume preview
    # ----------------------------------------

    preview = (
        f"{resume_text[:260].strip()}..."
        if len(resume_text) > 260
        else resume_text
    )

    # ----------------------------------------
    # 9. Return complete analysis result
    # ----------------------------------------

    return {
        "id": f"scan_{int(time.time() * 1000)}",

        "analyzedAt": datetime.now(
            timezone.utc
        ).isoformat(),

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
