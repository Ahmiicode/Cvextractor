from __future__ import annotations

from services.matcher_service import analyze_resume_against_job
from services.nlp_service import extract_skills, preprocess_text_for_tfidf


def test_spacy_skill_extraction_resolves_aliases_and_symbols():
    text = (
        "Built microservices with ReactJS, Node.js, C++, sklearn, Postgres, "
        "CI/CD pipelines, and Natural Language Processing via spaCy."
    )
    skills = extract_skills(text)

    assert "React" in skills
    assert "Node.js" in skills
    assert "C++" in skills
    assert "scikit-learn" in skills
    assert "PostgreSQL" in skills
    assert "CI/CD" in skills
    assert "Natural Language Processing" in skills
    assert "spaCy" in skills


def test_preprocess_text_filters_stop_words():
    tokens, raw_words = preprocess_text_for_tfidf(
        "The candidate is building scalable Python applications with Flask."
    )
    assert raw_words == 9
    assert "the" not in tokens
    assert "python" in tokens
    assert "flask" in tokens


def test_matcher_returns_matched_missing_and_tfidf_scores():
    resume_text = (
        "Python developer experienced in Flask, spaCy, scikit-learn, "
        "PostgreSQL, Git, and REST APIs for NLP pipelines."
    )
    jd_text = (
        "Hiring a Python Engineer with Flask, spaCy, scikit-learn, "
        "PostgreSQL, Docker, and AWS cloud deployment experience."
    )

    result = analyze_resume_against_job(
        resume_text=resume_text,
        job_description=jd_text,
        file_name="alex_cv.pdf",
        file_size_bytes=2048,
        file_type="PDF",
    )

    assert 0 <= result["overallScore"] <= 100
    assert 0 <= result["cosineSimilarity"] <= 100
    assert "Python" in result["matchedSkills"]
    assert "Flask" in result["matchedSkills"]
    assert "Docker" in result["missingSkills"]
    assert "AWS" in result["missingSkills"]
    assert result["interpretation"]["label"] in {
        "Excellent Match",
        "Strong Match",
        "Moderate Match",
        "Low Match",
    }
