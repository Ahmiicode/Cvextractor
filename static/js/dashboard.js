(() => {
  const MAX_FILE_SIZE = 5 * 1024 * 1024;
  const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];

  const SAMPLE_RESUME_FILENAME = 'Sample_CS_Graduate_Resume.txt';
  const SAMPLE_RESUME_TEXT = `ALEXANDER PATEL
London, United Kingdom | BSc Computer Science

SUMMARY
Final-year Computer Science undergraduate specializing in Applied Natural Language Processing, full-stack web engineering, and machine learning pipelines. Experienced in Python, Flask, spaCy, scikit-learn, PyMuPDF, python-docx, and REST APIs.

TECHNICAL SKILLS
Languages: Python, TypeScript, JavaScript, SQL, HTML5, CSS3
Frameworks & Libraries: Flask, React, Node.js, Tailwind CSS, spaCy, scikit-learn, Pandas, NumPy
Data & NLP: Natural Language Processing, TF-IDF, Machine Learning, Data Analysis, Unit Testing
Tools & Infrastructure: Git, Docker, PostgreSQL, Linux, Agile / Scrum

EXPERIENCE & ACADEMIC PROJECTS
 Resume-to-Job Matching System (Final Year Project)
- Built a Python and Flask NLP web application to parse PDF and DOCX resumes using PyMuPDF, python-docx, spaCy tokenization, and scikit-learn TF-IDF cosine similarity.
- Implemented automated skill extraction and gap diagnostics achieving 91% precision on benchmark academic test sets.`;

  const SAMPLE_JOB_DESCRIPTION = `Junior NLP & Full-Stack Python Engineer

We are seeking a motivated Junior Engineer to join our Talent Intelligence engineering team. You will help build document-processing pipelines, semantic skill matching models, and responsive web dashboards.

Responsibilities:
- Build and maintain backend services using Python, Flask, and REST APIs.
- Develop NLP text extraction and matching models using spaCy, scikit-learn, TF-IDF, PyMuPDF, and Pandas.
- Collaborate with frontend engineers using HTML5, CSS3, JavaScript, and Tailwind CSS.
- Store and query structured candidate records in PostgreSQL and deploy containerized services with Docker and AWS.
- Maintain high code quality through Unit Testing, CI/CD pipelines, and Git version control.

Required Qualifications:
- Strong proficiency in Python, SQL, and Natural Language Processing (NLP).
- Hands-on experience with Flask, spaCy, scikit-learn, and Machine Learning fundamentals.
- Familiarity with PostgreSQL, Docker, AWS, and CI/CD workflows.`;

  const PAGE_META = {
    dashboard: {
      title: 'Dashboard',
      subtitle: 'Welcome to the SkillAlign Resume-to-Job Matching Workspace',
    },
    scanner: {
      title: 'Resume Scanner',
      subtitle: 'Upload a PDF or DOCX resume and compare it against a target job description',
    },
    results: {
      title: 'Analysis Results',
      subtitle: 'Detailed matching score, skill gap breakdown, and TF-IDF similarity metrics',
    },
    'how-it-works': {
      title: 'How It Works',
      subtitle: 'Explore the  PyMuPDF, spaCy, and scikit-learn matching pipeline',
    },
    about: {
      title: 'About SkillAlign',
      subtitle: 'Academic project overview, scoring methodology, and supported formats',
    },
  };

  let activeSection =
    document.querySelector('[data-initial-section]')?.getAttribute('data-initial-section') ||
    'dashboard';
  let selectedFile = null;
  let latestAnalysis = null;
  let isAnalyzing = false;

  // Navigation elements
  const desktopSidebar = document.getElementById('desktop-sidebar');
  const collapseBtn = document.getElementById('sidebar-collapse-btn');
  const collapseIcon = document.getElementById('sidebar-collapse-icon');
  const mobileDrawer = document.getElementById('mobile-sidebar-drawer');
  const mobileBackdrop = document.getElementById('mobile-sidebar-backdrop');
  const mobileOpenBtn = document.getElementById('mobile-sidebar-open');
  const mobileCloseBtn = document.getElementById('mobile-sidebar-close');
  const headerTitle = document.getElementById('header-page-title');
  const headerSubtitle = document.getElementById('header-page-subtitle');
  const headerScanBtn = document.getElementById('header-scan-btn');
  const navButtons = document.querySelectorAll('[data-nav]');
  const goScannerButtons = document.querySelectorAll('[data-go-scanner]');

  // Scanner elements
  const fileInput = document.getElementById('resume-file-input');
  const dropzone = document.getElementById('resume-dropzone');
  const dropzoneEmpty = document.getElementById('dropzone-empty');
  const dropzoneSelected = document.getElementById('dropzone-selected');
  const browseFilesBtn = document.getElementById('browse-files-btn');
  const replaceFileBtn = document.getElementById('replace-file-btn');
  const removeFileBtn = document.getElementById('remove-file-btn');
  const selectedFilenameEl = document.getElementById('selected-filename');
  const selectedFilesizeEl = document.getElementById('selected-filesize');
  const uploadStatusEl = document.getElementById('upload-status-text');
  const jdInput = document.getElementById('job-description-input');
  const clearJdBtn = document.getElementById('clear-jd-btn');
  const jdCounterEl = document.getElementById('jd-counter-text');
  const loadSampleBtn = document.getElementById('load-sample-btn');
  const validationErrorEl = document.getElementById('scanner-validation-error');
  const analyzeBtn = document.getElementById('analyze-resume-btn');
  const analyzeBtnSpinner = document.getElementById('analyze-btn-spinner');
  const analyzeBtnLabel = document.getElementById('analyze-btn-label');
  const analyzeLoadingNote = document.getElementById('analyze-loading-note');

  function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function buildScoreRingSvg(score, size, strokeWidth) {
    const clamped = Math.max(0, Math.min(100, Math.round(score)));
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (clamped / 100) * circumference;
    const gradId = `scoreGrad_${size}_${Math.floor(Math.random() * 10000)}`;

    return `
      <div class="relative inline-flex items-center justify-center shrink-0" style="width:${size}px;height:${size}px" role="img" aria-label="${clamped}% Match Score">
        <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" class="-rotate-90">
          <defs>
            <linearGradient id="${gradId}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#5421D6" />
              <stop offset="52%" stop-color="#7652EA" />
              <stop offset="100%" stop-color="#06B6D4" />
            </linearGradient>
          </defs>
          <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" fill="none" stroke="#ECE8F8" stroke-width="${strokeWidth}" />
          <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" fill="none" stroke="url(#${gradId})" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" class="score-ring-arc" />
        </svg>
        <div class="absolute inset-0 flex flex-col items-center justify-center text-center px-2">
          <span class="font-display text-3xl sm:text-4xl font-extrabold tracking-tight text-[#17152F] tabular-nums leading-none">${clamped}%</span>
          <span class="mt-1 text-xs font-medium text-[#77758C]">Match Score</span>
        </div>
      </div>
    `;
  }

  function switchSection(sectionName) {
    activeSection = PAGE_META[sectionName] ? sectionName : 'dashboard';

    Object.keys(PAGE_META).forEach((key) => {
      const el = document.getElementById(`section-${key}`);
      if (el) el.classList.toggle('hidden', key !== activeSection);
    });

    if (headerTitle) headerTitle.textContent = PAGE_META[activeSection].title;
    if (headerSubtitle) headerSubtitle.textContent = PAGE_META[activeSection].subtitle;
    if (headerScanBtn) headerScanBtn.classList.toggle('hidden', activeSection === 'scanner');

    navButtons.forEach((btn) => {
      const target = btn.getAttribute('data-nav');
      const isActive = target === activeSection;
      btn.classList.toggle('bg-gradient-to-r', isActive);
      btn.classList.toggle('from-[#5421D6]', isActive);
      btn.classList.toggle('to-[#7652EA]', isActive);
      btn.classList.toggle('text-white', isActive);
      btn.classList.toggle('shadow-[0_8px_20px_rgba(84,33,214,0.35)]', isActive);
      btn.classList.toggle('text-white/75', !isActive);
    });

    closeMobileDrawer();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function openMobileDrawer() {
    if (mobileDrawer) mobileDrawer.classList.remove('hidden');
  }

  function closeMobileDrawer() {
    if (mobileDrawer) mobileDrawer.classList.add('hidden');
  }

  if (collapseBtn && desktopSidebar) {
    collapseBtn.addEventListener('click', () => {
      const collapsed = desktopSidebar.classList.toggle('sidebar-collapsed');
      if (collapseIcon) {
        collapseIcon.style.transform = collapsed ? 'rotate(180deg)' : 'rotate(0deg)';
      }
    });
  }

  if (mobileOpenBtn) mobileOpenBtn.addEventListener('click', openMobileDrawer);
  if (mobileCloseBtn) mobileCloseBtn.addEventListener('click', closeMobileDrawer);
  if (mobileBackdrop) mobileBackdrop.addEventListener('click', closeMobileDrawer);

  navButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      switchSection(btn.getAttribute('data-nav'));
    });
  });

  goScannerButtons.forEach((btn) => {
    btn.addEventListener('click', () => switchSection('scanner'));
  });

  if (headerScanBtn) {
    headerScanBtn.addEventListener('click', () => switchSection('scanner'));
  }

  const overviewViewResultsBtn = document.getElementById('overview-view-results-btn');
  if (overviewViewResultsBtn) {
    overviewViewResultsBtn.addEventListener('click', () => switchSection('results'));
  }

  // File Selection & Dropzone Logic
  function setFileStatus(status, message) {
    if (!uploadStatusEl || !dropzone) return;
    dropzone.classList.remove(
      'border-[#16A66A]/60',
      'bg-[#E8F8F1]/65',
      'border-[#DC2626]/50',
      'bg-[#FEF2F2]/60',
      'border-[#D5CEF0]',
      'bg-[#F7F6FC]'
    );

    if (status === 'ready') {
      dropzone.classList.add('border-[#16A66A]/60', 'bg-[#E8F8F1]/65');
      uploadStatusEl.className = 'font-semibold text-[#16A66A]';
      uploadStatusEl.textContent = message;
    } else if (status === 'error') {
      dropzone.classList.add('border-[#DC2626]/50', 'bg-[#FEF2F2]/60');
      uploadStatusEl.className = 'font-semibold text-[#DC2626]';
      uploadStatusEl.textContent = message;
    } else {
      dropzone.classList.add('border-[#D5CEF0]', 'bg-[#F7F6FC]');
      uploadStatusEl.className = 'text-[#77758C]';
      uploadStatusEl.textContent = message;
    }
  }

  function validateAndSetFile(file) {
    const lowerName = file.name.toLowerCase();
    const validExt = ALLOWED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));

    if (!validExt) {
      selectedFile = null;
      dropzoneEmpty?.classList.remove('hidden');
      dropzoneSelected?.classList.add('hidden');
      removeFileBtn?.classList.add('hidden');
      setFileStatus('error', 'Unsupported format. Upload .pdf or .docx');
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      selectedFile = null;
      dropzoneEmpty?.classList.remove('hidden');
      dropzoneSelected?.classList.add('hidden');
      removeFileBtn?.classList.add('hidden');
      setFileStatus('error', 'File exceeds the 5MB maximum limit');
      return;
    }

    if (file.size === 0) {
      selectedFile = null;
      dropzoneEmpty?.classList.remove('hidden');
      dropzoneSelected?.classList.add('hidden');
      removeFileBtn?.classList.add('hidden');
      setFileStatus('error', 'Selected file is empty');
      return;
    }

    selectedFile = file;
    if (selectedFilenameEl) selectedFilenameEl.textContent = file.name;
    if (selectedFilesizeEl) {
      selectedFilesizeEl.textContent = `${formatBytes(file.size)} · Ready for PyMuPDF / python-docx parsing`;
    }
    dropzoneEmpty?.classList.add('hidden');
    dropzoneSelected?.classList.remove('hidden');
    removeFileBtn?.classList.remove('hidden');
    setFileStatus('ready', 'Verified & Ready');
    hideValidationError();
  }

  function clearSelectedFile() {
    selectedFile = null;
    if (fileInput) fileInput.value = '';
    dropzoneEmpty?.classList.remove('hidden');
    dropzoneSelected?.classList.add('hidden');
    removeFileBtn?.classList.add('hidden');
    setFileStatus('idle', 'Waiting for document');
  }

  if (browseFilesBtn) {
    browseFilesBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!isAnalyzing) fileInput?.click();
    });
  }

  if (replaceFileBtn) {
    replaceFileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!isAnalyzing) fileInput?.click();
    });
  }

  if (removeFileBtn) {
    removeFileBtn.addEventListener('click', () => {
      if (!isAnalyzing) clearSelectedFile();
    });
  }

  if (dropzone) {
    dropzone.addEventListener('click', () => {
      if (!isAnalyzing) fileInput?.click();
    });
    dropzone.addEventListener('keydown', (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && !isAnalyzing) {
        e.preventDefault();
        fileInput?.click();
      }
    });
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('border-[#5421D6]', 'bg-[#F3F0FF]');
    });
    dropzone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      dropzone.classList.remove('border-[#5421D6]', 'bg-[#F3F0FF]');
    });
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('border-[#5421D6]', 'bg-[#F3F0FF]');
      const file = e.dataTransfer?.files?.[0];
      if (file) validateAndSetFile(file);
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (file) validateAndSetFile(file);
      e.target.value = '';
    });
  }

  function updateJdCounter() {
    const val = jdInput?.value || '';
    const trimmed = val.trim();
    const words = trimmed ? trimmed.split(/\s+/).length : 0;
    if (jdCounterEl) jdCounterEl.textContent = `${val.length} chars · ${words} words`;
    if (clearJdBtn) clearJdBtn.disabled = val.length === 0 || isAnalyzing;
  }

  if (jdInput) {
    jdInput.addEventListener('input', () => {
      updateJdCounter();
      hideValidationError();
    });
  }

  if (clearJdBtn) {
    clearJdBtn.addEventListener('click', () => {
      if (jdInput) jdInput.value = '';
      updateJdCounter();
      hideValidationError();
    });
  }

  if (loadSampleBtn) {
    loadSampleBtn.addEventListener('click', () => {
      if (isAnalyzing) return;
      const sampleBlob = new Blob([SAMPLE_RESUME_TEXT], { type: 'text/plain' });
      const sampleFile = new File([sampleBlob], SAMPLE_RESUME_FILENAME, { type: 'text/plain' });
      validateAndSetFile(sampleFile);
      if (jdInput) jdInput.value = SAMPLE_JOB_DESCRIPTION;
      updateJdCounter();
      hideValidationError();
    });
  }

  function showValidationError(message) {
    if (!validationErrorEl) return;
    validationErrorEl.textContent = message;
    validationErrorEl.classList.remove('hidden');
  }

  function hideValidationError() {
    if (!validationErrorEl) return;
    validationErrorEl.classList.add('hidden');
  }

  function setLoadingState(loading) {
    isAnalyzing = loading;
    if (analyzeBtn) analyzeBtn.disabled = loading;
    if (analyzeBtnSpinner) analyzeBtnSpinner.classList.toggle('hidden', !loading);
    if (analyzeBtnLabel) {
      analyzeBtnLabel.textContent = loading
        ? 'Analyzing Resume & Computing Match…'
        : 'Analyze Resume';
    }
    if (analyzeLoadingNote) analyzeLoadingNote.classList.toggle('hidden', !loading);
    if (jdInput) jdInput.disabled = loading;
    updateJdCounter();
  }

  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', async () => {
      if (!selectedFile) {
        showValidationError('Please upload a PDF or DOCX resume before starting analysis.');
        return;
      }

      const jdText = (jdInput?.value || '').trim();
      if (jdText.length < 30) {
        showValidationError(
          'Please paste a job description of at least 30 characters so spaCy and scikit-learn can compute accurate matching.'
        );
        return;
      }

      hideValidationError();
      setLoadingState(true);

      try {
        const formData = new FormData();
        formData.append('resume', selectedFile);
        formData.append('jobDescription', jdText);

        const response = await fetch('/api/analyze', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data?.error || 'Analysis failed. Please check your file and try again.');
        }

        latestAnalysis = data;
        renderAnalysisData(data);
        switchSection('results');
      } catch (err) {
        showValidationError(
          err instanceof Error ? err.message : 'Unable to reach Flask analysis server.'
        );
      } finally {
        setLoadingState(false);
      }
    });
  }

  function renderSkillChips(skills, tone) {
    if (!skills || skills.length === 0) return '';
    return skills
      .map((skill) => {
        if (tone === 'matched') {
          return `<span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#E8F8F1] border border-[#C6EEDB] text-[#14532D] text-xs sm:text-sm font-semibold">
            <svg class="w-4 h-4 text-[#16A66A] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg>
            <span>${escapeHtml(skill)}</span>
          </span>`;
        }
        return `<span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#FFF4E8] border border-[#FDE2C4] text-[#9A3412] text-xs sm:text-sm font-semibold">
          <svg class="w-4 h-4 text-[#EA580C] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>
          <span>${escapeHtml(skill)}</span>
        </span>`;
      })
      .join('');
  }

  function renderAnalysisData(data) {
    // 1. Update 3 Summary Cards
    const cardResumeTitle = document.getElementById('card-resume-title');
    const cardResumeSub = document.getElementById('card-resume-sub');
    const cardSkillsCount = document.getElementById('card-skills-count');
    const cardSkillsSub = document.getElementById('card-skills-sub');
    const cardScoreValue = document.getElementById('card-score-value');
    const cardScoreSub = document.getElementById('card-score-sub');

    if (cardResumeTitle) cardResumeTitle.textContent = data.fileName;
    if (cardResumeSub) {
      cardResumeSub.textContent = `${data.fileType} · ${formatBytes(data.fileSizeBytes)} · ${data.stats.resumeWordCount} words`;
    }
    if (cardSkillsCount) cardSkillsCount.textContent = String(data.resumeSkills.length);
    if (cardSkillsSub) {
      cardSkillsSub.textContent = `${data.matchedSkills.length} of ${data.jdSkills.length} job skills matched`;
    }
    if (cardScoreValue) cardScoreValue.textContent = `${data.overallScore}%`;
    if (cardScoreSub) {
      cardScoreSub.textContent = `${data.interpretation.label} · ${data.cosineSimilarity}% text similarity`;
    }

    // Sidebar Ready indicator
    document.getElementById('sidebar-results-ready')?.classList.remove('hidden');

    // 2. Dashboard Overview populated panel
    document.getElementById('dashboard-empty-state')?.classList.add('hidden');
    document.getElementById('dashboard-populated-state')?.classList.remove('hidden');

    const overviewRing = document.getElementById('overview-ring-container');
    if (overviewRing) overviewRing.innerHTML = buildScoreRingSvg(data.overallScore, 156, 13);

    const overviewTime = document.getElementById('overview-timestamp');
    if (overviewTime) {
      overviewTime.textContent = new Date(data.analyzedAt).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });
    }

    const isPositive =
      data.interpretation.tone === 'excellent' || data.interpretation.tone === 'strong';
    const interpIcon = isPositive
      ? '<svg class="w-5 h-5 text-[#16A66A] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg>'
      : '<svg class="w-5 h-5 text-[#EA580C] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" x2="12" y1="8" y2="12"></line><line x1="12" x2="12.01" y1="16" y2="16"></line></svg>';

    const overviewInterpHeading = document.getElementById('overview-interpretation-heading');
    const overviewInterpDesc = document.getElementById('overview-interpretation-desc');
    if (overviewInterpHeading) {
      overviewInterpHeading.innerHTML = `${interpIcon}<span>${escapeHtml(data.interpretation.label)}</span>`;
    }
    if (overviewInterpDesc) overviewInterpDesc.textContent = data.interpretation.description;

    const overviewCoverage = document.getElementById('overview-coverage-text');
    if (overviewCoverage) overviewCoverage.textContent = `${data.skillCoverage}% coverage`;

    const overviewMatchedLabel = document.getElementById('overview-matched-label');
    if (overviewMatchedLabel) {
      overviewMatchedLabel.textContent = `Matched Skills (${data.matchedSkills.length})`;
    }
    const overviewMatchedList = document.getElementById('overview-matched-list');
    if (overviewMatchedList) {
      overviewMatchedList.innerHTML =
        data.matchedSkills.length > 0
          ? renderSkillChips(data.matchedSkills.slice(0, 8), 'matched')
          : '<p class="text-xs text-[#77758C]">No overlapping structured skills detected.</p>';
    }

    const overviewMissingLabel = document.getElementById('overview-missing-label');
    if (overviewMissingLabel) {
      overviewMissingLabel.textContent = `Missing Target Skills (${data.missingSkills.length})`;
    }
    const overviewMissingList = document.getElementById('overview-missing-list');
    if (overviewMissingList) {
      overviewMissingList.innerHTML =
        data.missingSkills.length > 0
          ? renderSkillChips(data.missingSkills.slice(0, 6), 'missing')
          : '<p class="text-xs text-[#16A66A] font-medium">No missing skills detected from the job description.</p>';
    }

    const overviewCosine = document.getElementById('overview-cosine-text');
    if (overviewCosine) overviewCosine.textContent = `${data.cosineSimilarity}%`;

    // 3. Full Results Page
    document.getElementById('results-empty-state')?.classList.add('hidden');
    document.getElementById('results-populated-state')?.classList.remove('hidden');

    const resultsRing = document.getElementById('results-ring-container');
    if (resultsRing) resultsRing.innerHTML = buildScoreRingSvg(data.overallScore, 176, 15);

    const resultsMetaLine = document.getElementById('results-meta-line');
    if (resultsMetaLine) {
      resultsMetaLine.innerHTML = `
        <span class="font-semibold text-[#5421D6]">${escapeHtml(data.fileName)}</span>
        <span aria-hidden="true">·</span>
        <span>${escapeHtml(data.fileType)}</span>
        <span aria-hidden="true">·</span>
        <span class="tabular-nums">${escapeHtml(new Date(data.analyzedAt).toLocaleString())}</span>
      `;
    }

    const resultsInterpHeading = document.getElementById('results-interpretation-heading');
    const resultsInterpDesc = document.getElementById('results-interpretation-desc');
    if (resultsInterpHeading) {
      resultsInterpHeading.innerHTML = `${interpIcon}<h2 class="font-display text-2xl font-extrabold text-[#17152F]">${escapeHtml(data.interpretation.label)}</h2>`;
    }
    if (resultsInterpDesc) resultsInterpDesc.textContent = data.interpretation.description;

    document.getElementById('stat-skill-coverage').textContent = `${data.skillCoverage}%`;
    document.getElementById('stat-matched-ratio').textContent = `${data.matchedSkills.length}/${data.jdSkills.length}`;
    document.getElementById('stat-missing-count').textContent = String(data.missingSkills.length);
    document.getElementById('stat-cosine-pct').textContent = `${data.cosineSimilarity}%`;

    document.getElementById('results-matched-badge').textContent = `${data.matchedSkills.length} found`;
    const matchedContainer = document.getElementById('results-matched-container');
    if (matchedContainer) {
      matchedContainer.innerHTML =
        data.matchedSkills.length > 0
          ? `<div class="flex flex-wrap gap-2.5">${renderSkillChips(data.matchedSkills, 'matched')}</div>`
          : '<div class="rounded-xl bg-[#F7F6FC] p-4 text-sm text-[#77758C]">No structured taxonomy skills matched directly between the resume and job description.</div>';
    }

    const bonusContainer = document.getElementById('results-bonus-container');
    if (bonusContainer) {
      if (data.bonusSkills && data.bonusSkills.length > 0) {
        bonusContainer.classList.remove('hidden');
        bonusContainer.innerHTML = `
          <p class="text-xs font-semibold text-[#5B5872] mb-2">Additional Resume Skills Detected (${data.bonusSkills.length})</p>
          <p class="text-xs text-[#77758C] leading-relaxed">${escapeHtml(data.bonusSkills.join(' · '))}</p>
        `;
      } else {
        bonusContainer.classList.add('hidden');
      }
    }

    document.getElementById('results-missing-badge').textContent = `${data.missingSkills.length} gaps`;
    const missingContainer = document.getElementById('results-missing-container');
    if (missingContainer) {
      missingContainer.innerHTML =
        data.missingSkills.length > 0
          ? `<div class="flex flex-wrap gap-2.5">${renderSkillChips(data.missingSkills, 'missing')}</div>`
          : '<div class="rounded-xl bg-[#E8F8F1] border border-[#C6EEDB] p-4 text-sm text-[#14532D]">Great coverage! Every structured skill identified in the job description was found in your resume.</div>';
    }

    document.getElementById('sim-cosine-label').textContent = `${data.cosineSimilarity}%`;
    document.getElementById('sim-cosine-bar').style.width = `${data.cosineSimilarity}%`;
    document.getElementById('sim-overlap-label').textContent = `${data.keywordOverlap}%`;
    document.getElementById('sim-overlap-bar').style.width = `${data.keywordOverlap}%`;
    document.getElementById('stat-resume-words').textContent = String(data.stats.resumeWordCount);
    document.getElementById('stat-jd-words').textContent = String(data.stats.jdWordCount);
    document.getElementById('stat-shared-terms').textContent = String(data.stats.sharedTermCount);

    document.getElementById('summary-overview').textContent = data.summary.overview;
    document.getElementById('summary-strengths').innerHTML = data.summary.strengths
      .map(
        (s) =>
          `<li class="flex items-start gap-2.5"><span class="text-[#16A66A] font-bold">✓</span><span>${escapeHtml(s)}</span></li>`
      )
      .join('');
    document.getElementById('summary-recommendations').innerHTML = data.summary.recommendations
      .map(
        (r) =>
          `<li class="flex items-start gap-2.5"><span class="text-[#5421D6] font-bold">•</span><span>${escapeHtml(r)}</span></li>`
      )
      .join('');
  }

  const exportReportBtn = document.getElementById('export-report-btn');
  if (exportReportBtn) {
    exportReportBtn.addEventListener('click', () => {
      if (!latestAnalysis) return;
      const blob = new Blob([JSON.stringify(latestAnalysis, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `skillalign-report-${latestAnalysis.id}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });
  }

  // Initialize active section
  switchSection(activeSection);
  updateJdCounter();
})();
