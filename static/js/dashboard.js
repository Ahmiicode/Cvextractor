(() => {
  'use strict';

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
      subtitle: 'Upload a PDF, DOCX, or TXT resume and compare it against a target job description',
    },
    results: {
      title: 'Analysis Results',
      subtitle: 'Detailed matching score, skill gaps, industry, experience, and education analysis',
    },
    'how-it-works': {
      title: 'How It Works',
      subtitle: 'Explore the PyMuPDF, spaCy, and scikit-learn matching pipeline',
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

  const $ = (id) => document.getElementById(id);

  function setText(id, value) {
    const element = $(id);
    if (element) element.textContent = value ?? '';
  }

  function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = String(value ?? '');
    return div.innerHTML;
  }

  function formatBytes(bytes = 0) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function displayValue(value, fallback = 'Not identified in the provided document.') {
    if (value === null || value === undefined || value === '') return fallback;
    return String(value);
  }

  function buildScoreRingSvg(score, size, strokeWidth) {
    const numericScore = Number(score) || 0;
    const clamped = Math.max(0, Math.min(100, Math.round(numericScore)));
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (clamped / 100) * circumference;
    const gradId = `scoreGrad_${size}_${Math.random().toString(36).slice(2, 9)}`;

    return `
      <div class="relative inline-flex items-center justify-center shrink-0"
           style="width:${size}px;height:${size}px"
           role="img"
           aria-label="${clamped}% Match Score">
        <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" class="-rotate-90">
          <defs>
            <linearGradient id="${gradId}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#5421D6" />
              <stop offset="52%" stop-color="#7652EA" />
              <stop offset="100%" stop-color="#06B6D4" />
            </linearGradient>
          </defs>
          <circle cx="${size / 2}" cy="${size / 2}" r="${radius}"
                  fill="none" stroke="#ECE8F8" stroke-width="${strokeWidth}" />
          <circle cx="${size / 2}" cy="${size / 2}" r="${radius}"
                  fill="none" stroke="url(#${gradId})"
                  stroke-width="${strokeWidth}" stroke-linecap="round"
                  stroke-dasharray="${circumference}"
                  stroke-dashoffset="${offset}"
                  class="score-ring-arc" />
        </svg>
        <div class="absolute inset-0 flex flex-col items-center justify-center text-center px-2">
          <span class="font-display text-3xl sm:text-4xl font-extrabold tracking-tight text-[#17152F] tabular-nums leading-none">
            ${clamped}%
          </span>
          <span class="mt-1 text-xs font-medium text-[#77758C]">Match Score</span>
        </div>
      </div>
    `;
  }

  // ---------------------------------------------------------
  // NAVIGATION
  // ---------------------------------------------------------

  const desktopSidebar = $('desktop-sidebar');
  const collapseBtn = $('sidebar-collapse-btn');
  const collapseIcon = $('sidebar-collapse-icon');
  const mobileDrawer = $('mobile-sidebar-drawer');
  const mobileBackdrop = $('mobile-sidebar-backdrop');
  const mobileOpenBtn = $('mobile-sidebar-open');
  const mobileCloseBtn = $('mobile-sidebar-close');
  const headerTitle = $('header-page-title');
  const headerSubtitle = $('header-page-subtitle');
  const headerScanBtn = $('header-scan-btn');

  const navButtons = document.querySelectorAll('[data-nav]');
  const goScannerButtons = document.querySelectorAll('[data-go-scanner]');

  function closeMobileDrawer() {
    mobileDrawer?.classList.add('hidden');
  }

  function openMobileDrawer() {
    mobileDrawer?.classList.remove('hidden');
  }

  function switchSection(sectionName) {
    activeSection = PAGE_META[sectionName] ? sectionName : 'dashboard';

    Object.keys(PAGE_META).forEach((key) => {
      const section = $(`section-${key}`);
      if (section) section.classList.toggle('hidden', key !== activeSection);
    });

    if (headerTitle) headerTitle.textContent = PAGE_META[activeSection].title;
    if (headerSubtitle) headerSubtitle.textContent = PAGE_META[activeSection].subtitle;

    headerScanBtn?.classList.toggle('hidden', activeSection === 'scanner');

    navButtons.forEach((button) => {
      const isActive = button.getAttribute('data-nav') === activeSection;

      button.classList.toggle('bg-gradient-to-r', isActive);
      button.classList.toggle('from-[#5421D6]', isActive);
      button.classList.toggle('to-[#7652EA]', isActive);
      button.classList.toggle('text-white', isActive);
      button.classList.toggle(
        'shadow-[0_8px_20px_rgba(84,33,214,0.35)]',
        isActive
      );
      button.classList.toggle('text-white/75', !isActive);
    });

    closeMobileDrawer();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (collapseBtn && desktopSidebar) {
    collapseBtn.addEventListener('click', () => {
      const collapsed = desktopSidebar.classList.toggle('sidebar-collapsed');

      if (collapseIcon) {
        collapseIcon.style.transform = collapsed ? 'rotate(180deg)' : 'rotate(0deg)';
      }
    });
  }

  mobileOpenBtn?.addEventListener('click', openMobileDrawer);
  mobileCloseBtn?.addEventListener('click', closeMobileDrawer);
  mobileBackdrop?.addEventListener('click', closeMobileDrawer);

  navButtons.forEach((button) => {
    button.addEventListener('click', () => {
      switchSection(button.getAttribute('data-nav'));
    });
  });

  goScannerButtons.forEach((button) => {
    button.addEventListener('click', () => switchSection('scanner'));
  });

  headerScanBtn?.addEventListener('click', () => switchSection('scanner'));
  $('overview-view-results-btn')?.addEventListener('click', () => switchSection('results'));

  // ---------------------------------------------------------
  // FILE UPLOAD
  // ---------------------------------------------------------

  const fileInput = $('resume-file-input');
  const dropzone = $('resume-dropzone');
  const dropzoneEmpty = $('dropzone-empty');
  const dropzoneSelected = $('dropzone-selected');
  const browseFilesBtn = $('browse-files-btn');
  const replaceFileBtn = $('replace-file-btn');
  const removeFileBtn = $('remove-file-btn');
  const selectedFilenameEl = $('selected-filename');
  const selectedFilesizeEl = $('selected-filesize');
  const uploadStatusEl = $('upload-status-text');

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
    } else if (status === 'error') {
      dropzone.classList.add('border-[#DC2626]/50', 'bg-[#FEF2F2]/60');
      uploadStatusEl.className = 'font-semibold text-[#DC2626]';
    } else {
      dropzone.classList.add('border-[#D5CEF0]', 'bg-[#F7F6FC]');
      uploadStatusEl.className = 'text-[#77758C]';
    }

    uploadStatusEl.textContent = message;
  }

  const validationErrorEl = $('scanner-validation-error');

  function showValidationError(message) {
    if (!validationErrorEl) return;
    validationErrorEl.textContent = message;
    validationErrorEl.classList.remove('hidden');
  }

  function hideValidationError() {
    validationErrorEl?.classList.add('hidden');
  }

  function validateAndSetFile(file) {
    if (!file) return;

    const lowerName = file.name.toLowerCase();
    const validExt = ALLOWED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));

    if (!validExt) {
      selectedFile = null;
      dropzoneEmpty?.classList.remove('hidden');
      dropzoneSelected?.classList.add('hidden');
      removeFileBtn?.classList.add('hidden');
      setFileStatus('error', 'Unsupported format. Upload PDF, DOCX, or TXT.');
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      selectedFile = null;
      dropzoneEmpty?.classList.remove('hidden');
      dropzoneSelected?.classList.add('hidden');
      removeFileBtn?.classList.add('hidden');
      setFileStatus('error', 'File exceeds the 5MB maximum limit.');
      return;
    }

    if (file.size === 0) {
      selectedFile = null;
      dropzoneEmpty?.classList.remove('hidden');
      dropzoneSelected?.classList.add('hidden');
      removeFileBtn?.classList.add('hidden');
      setFileStatus('error', 'Selected file is empty.');
      return;
    }

    selectedFile = file;

    if (selectedFilenameEl) selectedFilenameEl.textContent = file.name;

    if (selectedFilesizeEl) {
      selectedFilesizeEl.textContent =
        `${formatBytes(file.size)} · Ready for document parsing`;
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

  browseFilesBtn?.addEventListener('click', (event) => {
    event.stopPropagation();
    if (!isAnalyzing) fileInput?.click();
  });

  replaceFileBtn?.addEventListener('click', (event) => {
    event.stopPropagation();
    if (!isAnalyzing) fileInput?.click();
  });

  removeFileBtn?.addEventListener('click', () => {
    if (!isAnalyzing) clearSelectedFile();
  });

  dropzone?.addEventListener('click', () => {
    if (!isAnalyzing) fileInput?.click();
  });

  dropzone?.addEventListener('keydown', (event) => {
    if ((event.key === 'Enter' || event.key === ' ') && !isAnalyzing) {
      event.preventDefault();
      fileInput?.click();
    }
  });

  dropzone?.addEventListener('dragover', (event) => {
    event.preventDefault();
    dropzone.classList.add('border-[#5421D6]', 'bg-[#F3F0FF]');
  });

  dropzone?.addEventListener('dragleave', (event) => {
    event.preventDefault();
    dropzone.classList.remove('border-[#5421D6]', 'bg-[#F3F0FF]');
  });

  dropzone?.addEventListener('drop', (event) => {
    event.preventDefault();
    dropzone.classList.remove('border-[#5421D6]', 'bg-[#F3F0FF]');

    const file = event.dataTransfer?.files?.[0];
    if (file && !isAnalyzing) validateAndSetFile(file);
  });

  fileInput?.addEventListener('change', (event) => {
    const file = event.target.files?.[0];
    if (file) validateAndSetFile(file);
    event.target.value = '';
  });

  // ---------------------------------------------------------
  // JOB DESCRIPTION
  // ---------------------------------------------------------

  const jdInput = $('job-description-input');
  const clearJdBtn = $('clear-jd-btn');
  const jdCounterEl = $('jd-counter-text');
  const loadSampleBtn = $('load-sample-btn');

  function updateJdCounter() {
    const value = jdInput?.value || '';
    const trimmed = value.trim();
    const words = trimmed ? trimmed.split(/\s+/).length : 0;

    if (jdCounterEl) {
      jdCounterEl.textContent = `${value.length} chars · ${words} words`;
    }

    if (clearJdBtn) {
      clearJdBtn.disabled = value.length === 0 || isAnalyzing;
    }
  }

  jdInput?.addEventListener('input', () => {
    updateJdCounter();
    hideValidationError();
  });

  clearJdBtn?.addEventListener('click', () => {
    if (jdInput) jdInput.value = '';
    updateJdCounter();
    hideValidationError();
  });

  loadSampleBtn?.addEventListener('click', () => {
    if (isAnalyzing) return;

    const sampleBlob = new Blob([SAMPLE_RESUME_TEXT], { type: 'text/plain' });
    const sampleFile = new File([sampleBlob], SAMPLE_RESUME_FILENAME, {
      type: 'text/plain',
    });

    validateAndSetFile(sampleFile);

    if (jdInput) jdInput.value = SAMPLE_JOB_DESCRIPTION;

    updateJdCounter();
    hideValidationError();
  });

  // ---------------------------------------------------------
  // ANALYSIS LOADING
  // ---------------------------------------------------------

  const analyzeBtn = $('analyze-resume-btn');
  const analyzeBtnSpinner = $('analyze-btn-spinner');
  const analyzeBtnLabel = $('analyze-btn-label');
  const analyzeLoadingNote = $('analyze-loading-note');

  function setLoadingState(loading) {
    isAnalyzing = loading;

    if (analyzeBtn) analyzeBtn.disabled = loading;

    analyzeBtnSpinner?.classList.toggle('hidden', !loading);

    if (analyzeBtnLabel) {
      analyzeBtnLabel.textContent = loading
        ? 'Analyzing Resume & Computing Match…'
        : 'Analyze Resume';
    }

    analyzeLoadingNote?.classList.toggle('hidden', !loading);

    if (jdInput) jdInput.disabled = loading;

    updateJdCounter();
  }

  // ---------------------------------------------------------
  // SKILL CHIP COMPONENT
  // ---------------------------------------------------------

  function renderSkillChips(skills, tone = 'missing', partialSet = null) {
    const items = asArray(skills);

    if (!items.length) return '';

    return items
      .map((skill) => {
        const safeSkill = escapeHtml(skill);

        if (tone === 'matched') {
          return `
            <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#E8F8F1] border border-[#C6EEDB] text-[#14532D] text-xs sm:text-sm font-semibold">
              <svg class="w-4 h-4 text-[#16A66A] shrink-0" viewBox="0 0 24 24"
                   fill="none" stroke="currentColor" stroke-width="2"
                   stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="m9 12 2 2 4-4"></path>
              </svg>
              <span>${safeSkill}</span>
            </span>
          `;
        }

        if (tone === 'partial') {
          return `
            <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] text-[#1D4ED8] text-xs sm:text-sm font-semibold">
              <span class="w-2 h-2 rounded-full bg-[#3B82F6]"></span>
              <span>${safeSkill}</span>
            </span>
          `;
        }

        const isPartial = partialSet && partialSet.has(String(skill).toLowerCase());

        return `
          <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#FFF4E8] border border-[#FDE2C4] text-[#9A3412] text-xs sm:text-sm font-semibold">
            <svg class="w-4 h-4 text-[#EA580C] shrink-0" viewBox="0 0 24 24"
                 fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
              <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path>
              <path d="M12 9v4"></path>
              <path d="M12 17h.01"></path>
            </svg>
            <span>${safeSkill}</span>
            ${isPartial ? '<span class="text-[10px] font-bold text-[#1D4ED8] bg-[#EFF6FF] border border-[#BFDBFE] rounded-md px-1.5 py-0.5">partial</span>' : ''}
          </span>
        `;
      })
      .join('');
  }

  function renderList(items, emptyMessage, marker = '•') {
    const list = asArray(items);

    if (!list.length) {
      return `<p class="text-sm text-[#77758C]">${escapeHtml(emptyMessage)}</p>`;
    }

    return `
      <ul class="space-y-2.5">
        ${list
          .map(
            (item) => `
              <li class="flex items-start gap-2.5 text-sm text-[#4B4862] leading-relaxed">
                <span class="font-bold text-[#5421D6] shrink-0">${marker}</span>
                <span>${escapeHtml(item)}</span>
              </li>
            `
          )
          .join('')}
      </ul>
    `;
  }

  // ---------------------------------------------------------
  // DYNAMIC ANALYSIS SECTIONS
  // ---------------------------------------------------------

  function ensureAdvancedAnalysisContainer() {
    const resultsState = $('results-populated-state');

    if (!resultsState) return null;

    let container = $('advanced-analysis-container');

    if (!container) {
      container = document.createElement('div');
      container.id = 'advanced-analysis-container';
      container.className = 'mt-8 space-y-6';

      resultsState.appendChild(container);
    }

    return container;
  }

  function renderAnalysisCard(title, description, content, icon = '•') {
    return `
      <section class="rounded-2xl border border-[#E8E4F2] bg-white p-5 sm:p-6 shadow-sm">
        <div class="flex items-start gap-3 mb-4">
          <div class="w-10 h-10 rounded-xl bg-[#F1EDFF] text-[#5421D6] flex items-center justify-center font-bold text-lg shrink-0">
            ${icon}
          </div>
          <div>
            <h3 class="font-display text-lg font-bold text-[#17152F]">
              ${escapeHtml(title)}
            </h3>
            <p class="text-xs sm:text-sm text-[#77758C] mt-1">
              ${escapeHtml(description)}
            </p>
          </div>
        </div>
        ${content}
      </section>
    `;
  }

  function toText(value, fallback) {
    // Arrays (evidence lists) -> first item; empty array/null -> fallback.
    if (Array.isArray(value)) {
      const first = value.find((entry) => String(entry ?? '').trim());
      return first ? String(first).trim() : fallback;
    }
    if (value === null || value === undefined || value === '' || value === false) {
      return fallback;
    }
    return String(value);
  }

  function formatYears(value, fallback) {
    if (value === null || value === undefined || value === '') return fallback;
    const number = Number(value);
    if (Number.isNaN(number)) return String(value);
    return `${number} ${number === 1 ? 'year' : 'years'}`;
  }

  function updateIndustryBanner(data) {
    const resultsState = $('results-populated-state');
    if (!resultsState) return;

    let banner = $('industry-mismatch-banner');

    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'industry-mismatch-banner';
      resultsState.insertBefore(banner, resultsState.firstChild);
    }

    const industry = data.industryAnalysis || {};
    const different = Boolean(industry.differentIndustries ?? industry.isDifferentIndustry);

    if (!different) {
      banner.className = 'hidden';
      banner.innerHTML = '';
      return;
    }

    banner.className = 'rounded-2xl border border-[#FED7AA] bg-[#FFF7ED] p-5 text-sm text-[#9A3412] leading-relaxed';
    banner.innerHTML = `
      <p class="font-bold mb-1">Different Industries Detected</p>
      <p>
        Your resume belongs to <strong>${escapeHtml(industry.resumeIndustry || 'Not identified')}</strong>,
        but this job belongs to <strong>${escapeHtml(industry.jobIndustry || 'Not identified')}</strong>.
        A low score here reflects a career-field difference. The complete skill, experience and
        education analysis is still shown below, including every required skill that was not found.
      </p>
    `;
  }

  function renderIndustryAnalysis(analysis) {
    const item = analysis || {};

    const resumeIndustry =
      item.resumeIndustry || item.resume_industry || item.cvIndustry || 'Not identified';

    const jobIndustry =
      item.jobIndustry || item.job_industry || item.targetIndustry || 'Not identified';

    const isDifferent =
      item.isDifferentIndustry ??
      item.is_different_industry ??
      item.differentIndustries ??
      false;

    const message =
      item.message ||
      item.explanation ||
      item.description ||
      (isDifferent
        ? 'The resume and job description appear to belong to different industries. The system has still completed the skill and experience comparison.'
        : 'The resume and job description have been compared using the available industry indicators.');

    return `
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div class="rounded-xl bg-[#F7F6FC] p-4">
          <p class="text-xs text-[#77758C] mb-1">Resume Industry</p>
          <p class="font-semibold text-[#17152F]">${escapeHtml(resumeIndustry)}</p>
        </div>
        <div class="rounded-xl bg-[#F7F6FC] p-4">
          <p class="text-xs text-[#77758C] mb-1">Job Industry</p>
          <p class="font-semibold text-[#17152F]">${escapeHtml(jobIndustry)}</p>
        </div>
      </div>

      <div class="rounded-xl ${isDifferent ? 'bg-[#FFF7ED] border border-[#FED7AA] text-[#9A3412]' : 'bg-[#F0FDF4] border border-[#BBF7D0] text-[#166534]'} p-4 text-sm leading-relaxed">
        <p class="font-semibold mb-1">
          ${isDifferent ? 'Different Industry Detected' : 'Industry Comparison'}
        </p>
        <p>${escapeHtml(message)}</p>
      </div>
    `;
  }

  function renderExperienceAnalysis(analysis) {
    const item = analysis || {};

    const resumeYears = formatYears(
      item.resumeYears ?? item.resume_years ?? item.cvYears ?? item.candidateExperience,
      'Duration not stated'
    );

    const requiredYears = formatYears(
      item.requiredYears ?? item.required_years ?? item.jobYears ?? item.requiredExperience,
      'Not specified'
    );

    const status =
      item.status ||
      item.label ||
      item.matchStatus ||
      'Experience evidence reviewed';

    const message =
      item.message ||
      item.explanation ||
      item.description ||
      'Experience details were reviewed from the resume and job description.';

    const evidence = asArray(item.evidence || item.resumeEvidence || item.details);

    return `
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div class="rounded-xl bg-[#F7F6FC] p-4">
          <p class="text-xs text-[#77758C] mb-1">Experience in Resume</p>
          <p class="font-semibold text-[#17152F]">${escapeHtml(resumeYears)}</p>
        </div>
        <div class="rounded-xl bg-[#F7F6FC] p-4">
          <p class="text-xs text-[#77758C] mb-1">Job Experience Requirement</p>
          <p class="font-semibold text-[#17152F]">${escapeHtml(requiredYears)}</p>
        </div>
      </div>

      <div class="rounded-xl bg-[#F7F6FC] p-4 mb-3">
        <p class="text-xs text-[#77758C] mb-1">Assessment</p>
        <p class="font-semibold text-[#5421D6]">${escapeHtml(status)}</p>
        <p class="text-sm text-[#5B5872] mt-2 leading-relaxed">${escapeHtml(message)}</p>
      </div>

      ${
        evidence.length
          ? `<div>
              <p class="text-xs font-semibold text-[#5B5872] mb-2">Experience Evidence</p>
              ${renderList(evidence, 'No specific evidence found.')}
            </div>`
          : ''
      }
    `;
  }

  function renderEducationAnalysis(analysis) {
    const item = analysis || {};

    const resumeEducationList = asArray(item.resumeEducation || item.resume_education);
    const requiredEducationList = asArray(item.requiredEducation || item.required_education);

    const resumeEducation = toText(
      resumeEducationList.length
        ? resumeEducationList
        : item.candidateEducation,
      'Not identified'
    );

    const requiredEducation = toText(
      requiredEducationList.length
        ? requiredEducationList
        : (item.jobEducation || item.educationRequired),
      'Not specified'
    );

    const status =
      item.status ||
      item.label ||
      item.matchStatus ||
      'Education evidence reviewed';

    const message =
      item.message ||
      item.explanation ||
      item.description ||
      'Education details were reviewed from the available resume and job description text.';

    const evidence = resumeEducationList.length
      ? resumeEducationList
      : asArray(item.evidence || item.resumeEvidence || item.details);

    return `
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div class="rounded-xl bg-[#F7F6FC] p-4">
          <p class="text-xs text-[#77758C] mb-1">Education in Resume</p>
          <p class="font-semibold text-[#17152F]">${escapeHtml(resumeEducation)}</p>
        </div>
        <div class="rounded-xl bg-[#F7F6FC] p-4">
          <p class="text-xs text-[#77758C] mb-1">Job Education Requirement</p>
          <p class="font-semibold text-[#17152F]">${escapeHtml(requiredEducation)}</p>
        </div>
      </div>

      <div class="rounded-xl bg-[#F7F6FC] p-4 mb-3">
        <p class="text-xs text-[#77758C] mb-1">Assessment</p>
        <p class="font-semibold text-[#5421D6]">${escapeHtml(status)}</p>
        <p class="text-sm text-[#5B5872] mt-2 leading-relaxed">${escapeHtml(message)}</p>
      </div>

      ${
        evidence.length
          ? `<div>
              <p class="text-xs font-semibold text-[#5B5872] mb-2">Education Evidence</p>
              ${renderList(evidence, 'No specific evidence found.')}
            </div>`
          : ''
      }
    `;
  }

  function renderAdvancedAnalysis(data) {
    const container = ensureAdvancedAnalysisContainer();
    if (!container) return;

    const partialSkills = asArray(data.partialMatchedSkills);
    const industry = data.industryAnalysis || {};
    const experience = data.experienceAnalysis || {};
    const education = data.educationAnalysis || {};

    const partialDetails = asArray(data.partialSkillEvidence)
      .filter((entry) => entry && entry.skill)
      .map((entry) => {
        const detail = entry.reason || entry.evidence || '';
        return `${entry.skill}${detail ? ': ' + detail : ''}`;
      });

    const partialContent = partialSkills.length
      ? `<div class="flex flex-wrap gap-2.5">${renderSkillChips(partialSkills, 'partial')}</div>
         <p class="text-xs text-[#77758C] mt-3 mb-3">These skills have some related evidence in the resume, but the evidence may not fully satisfy the job requirement. They also remain listed under Missing Skills.</p>
         ${partialDetails.length ? renderList(partialDetails, '', '◐') : ''}`
      : `<p class="text-sm text-[#77758C]">No partial skill matches were identified. Skills that were not found are listed in Missing Skills.</p>`;

    const industryContent = renderIndustryAnalysis(industry);
    const experienceContent = renderExperienceAnalysis(experience);
    const educationContent = renderEducationAnalysis(education);

    container.innerHTML = `
      <div class="mb-2">
        <h2 class="font-display text-xl sm:text-2xl font-extrabold text-[#17152F]">
          Detailed Candidate Analysis
        </h2>
        <p class="text-sm text-[#77758C] mt-1">
          Additional insights from the resume and target job description.
        </p>
      </div>

      ${renderAnalysisCard(
        `Partially Matched Skills (${partialSkills.length})`,
        'Skills with related or incomplete evidence in the resume.',
        partialContent,
        '◐'
      )}

      ${renderAnalysisCard(
        'Industry Comparison',
        'Comparison between the candidate background and target job industry.',
        industryContent,
        '⌂'
      )}

      ${renderAnalysisCard(
        'Experience Analysis',
        'Review of candidate experience against the job requirement.',
        experienceContent,
        '◷'
      )}

      ${renderAnalysisCard(
        'Education Analysis',
        'Review of education evidence against the job requirement.',
        educationContent,
        '▤'
      )}
    `;
  }

  // ---------------------------------------------------------
  // MAIN RESULTS RENDERER
  // ---------------------------------------------------------

  function renderAnalysisData(data) {
    const resumeSkills = asArray(data.resumeSkills);
    const jdSkills = asArray(data.jdSkills);
    const matchedSkills = asArray(data.matchedSkills);
    const missingSkills = asArray(data.missingSkills);
    const bonusSkills = asArray(data.bonusSkills);

    const stats = data.stats || {};
    const interpretation = data.interpretation || {};
    const summary = data.summary || {};

    const overallScore = Number(data.overallScore) || 0;
    const skillCoverage = Number(data.skillCoverage) || 0;
    const cosineSimilarity = Number(data.cosineSimilarity) || 0;
    const keywordOverlap = Number(data.keywordOverlap) || 0;

    // Summary cards
    setText('card-resume-title', data.fileName || 'Uploaded Resume');

    setText(
      'card-resume-sub',
      `${data.fileType || 'Document'} · ${formatBytes(data.fileSizeBytes || 0)} · ${stats.resumeWordCount || 0} words`
    );

    setText('card-skills-count', String(resumeSkills.length));

    setText(
      'card-skills-sub',
      `${matchedSkills.length} of ${jdSkills.length} job skills matched`
    );

    setText('card-score-value', `${overallScore}%`);

    setText(
      'card-score-sub',
      `${interpretation.label || 'Analysis Complete'} · ${cosineSimilarity}% text similarity`
    );

    $('sidebar-results-ready')?.classList.remove('hidden');

    // Dashboard overview
    $('dashboard-empty-state')?.classList.add('hidden');
    $('dashboard-populated-state')?.classList.remove('hidden');

    const overviewRing = $('overview-ring-container');
    if (overviewRing) {
      overviewRing.innerHTML = buildScoreRingSvg(overallScore, 156, 13);
    }

    const overviewTime = $('overview-timestamp');
    if (overviewTime) {
      const date = data.analyzedAt ? new Date(data.analyzedAt) : new Date();

      overviewTime.textContent = date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });
    }

    const isPositive = ['excellent', 'strong'].includes(interpretation.tone);

    const interpIcon = isPositive
      ? `<svg class="w-5 h-5 text-[#16A66A] shrink-0" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
           <circle cx="12" cy="12" r="10"></circle>
           <path d="m9 12 2 2 4-4"></path>
         </svg>`
      : `<svg class="w-5 h-5 text-[#EA580C] shrink-0" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
           <circle cx="12" cy="12" r="10"></circle>
           <line x1="12" x2="12" y1="8" y2="12"></line>
           <line x1="12" x2="12.01" y1="16" y2="16"></line>
         </svg>`;

    const overviewInterpHeading = $('overview-interpretation-heading');

    if (overviewInterpHeading) {
      overviewInterpHeading.innerHTML =
        `${interpIcon}<span>${escapeHtml(interpretation.label || 'Analysis Complete')}</span>`;
    }

    setText(
      'overview-interpretation-desc',
      interpretation.description || 'Your resume analysis has been completed.'
    );

    setText('overview-coverage-text', `${skillCoverage}% coverage`);

    setText(
      'overview-matched-label',
      `Matched Skills (${matchedSkills.length})`
    );

    const overviewMatchedList = $('overview-matched-list');

    if (overviewMatchedList) {
      overviewMatchedList.innerHTML = matchedSkills.length
        ? renderSkillChips(matchedSkills.slice(0, 8), 'matched')
        : '<p class="text-xs text-[#77758C]">No overlapping skills were detected. Review the missing skills below.</p>';
    }

    setText(
      'overview-missing-label',
      `Missing Target Skills (${missingSkills.length})`
    );

    const overviewMissingList = $('overview-missing-list');

    if (overviewMissingList) {
      overviewMissingList.innerHTML = missingSkills.length
        ? renderSkillChips(missingSkills.slice(0, 6), 'missing', new Set(asArray(data.partialMatchedSkills).map((name) => String(name).toLowerCase())))
        : jdSkills.length
          ? '<p class="text-xs text-[#16A66A] font-medium">All identified job skills were found in the resume.</p>'
          : '<p class="text-xs text-[#77758C]">No structured job skills were extracted. Review the job requirements manually.</p>';
    }

    setText('overview-cosine-text', `${cosineSimilarity}%`);

    // Full results page
    $('results-empty-state')?.classList.add('hidden');
    $('results-populated-state')?.classList.remove('hidden');

    const resultsRing = $('results-ring-container');

    if (resultsRing) {
      resultsRing.innerHTML = buildScoreRingSvg(overallScore, 176, 15);
    }

    const resultsMetaLine = $('results-meta-line');

    if (resultsMetaLine) {
      const analyzedDate = data.analyzedAt
        ? new Date(data.analyzedAt).toLocaleString()
        : new Date().toLocaleString();

      resultsMetaLine.innerHTML = `
        <span class="font-semibold text-[#5421D6]">${escapeHtml(data.fileName || 'Resume')}</span>
        <span aria-hidden="true">·</span>
        <span>${escapeHtml(data.fileType || 'Document')}</span>
        <span aria-hidden="true">·</span>
        <span class="tabular-nums">${escapeHtml(analyzedDate)}</span>
      `;
    }

    const resultsInterpHeading = $('results-interpretation-heading');

    if (resultsInterpHeading) {
      resultsInterpHeading.innerHTML = `
        ${interpIcon}
        <h2 class="font-display text-2xl font-extrabold text-[#17152F]">
          ${escapeHtml(interpretation.label || 'Analysis Complete')}
        </h2>
      `;
    }

    setText(
      'results-interpretation-desc',
      interpretation.description || 'The resume has been compared with the job description.'
    );

    setText('stat-skill-coverage', `${skillCoverage}%`);
    setText('stat-matched-ratio', `${matchedSkills.length}/${jdSkills.length}`);
    setText('stat-missing-count', String(missingSkills.length));
    setText('stat-cosine-pct', `${cosineSimilarity}%`);

    setText('results-matched-badge', `${matchedSkills.length} found`);

    const matchedContainer = $('results-matched-container');

    if (matchedContainer) {
      matchedContainer.innerHTML = matchedSkills.length
        ? `<div class="flex flex-wrap gap-2.5">${renderSkillChips(matchedSkills, 'matched')}</div>`
        : `<div class="rounded-xl bg-[#F7F6FC] p-4 text-sm text-[#77758C]">
             No skills were matched directly. This does not stop the analysis.
           </div>`;
    }

    const bonusContainer = $('results-bonus-container');

    if (bonusContainer) {
      if (bonusSkills.length) {
        bonusContainer.classList.remove('hidden');
        bonusContainer.innerHTML = `
          <p class="text-xs font-semibold text-[#5B5872] mb-2">
            Additional Resume Skills Detected (${bonusSkills.length})
          </p>
          <p class="text-xs text-[#77758C] leading-relaxed">
            ${escapeHtml(bonusSkills.join(' · '))}
          </p>
        `;
      } else {
        bonusContainer.classList.add('hidden');
      }
    }

    const partialLookup = new Set(
      asArray(data.partialMatchedSkills).map((name) => String(name).toLowerCase())
    );

    setText('results-missing-badge', `${missingSkills.length} gaps`);

    const missingContainer = $('results-missing-container');

    if (missingContainer) {
      if (missingSkills.length) {
        missingContainer.innerHTML = `
          <div class="flex flex-wrap gap-2.5">
            ${renderSkillChips(missingSkills, 'missing', partialLookup)}
          </div>
          ${partialLookup.size ? '<p class="text-xs text-[#77758C] mt-3">Skills tagged "partial" have related evidence in the resume but are not fully confirmed.</p>' : ''}
        `;
      } else if (jdSkills.length) {
        missingContainer.innerHTML = `
          <div class="rounded-xl bg-[#E8F8F1] border border-[#C6EEDB] p-4 text-sm text-[#14532D]">
            All identified structured skills from the job description were found in the resume.
          </div>
        `;
      } else {
        missingContainer.innerHTML = `
          <div class="rounded-xl bg-[#FFF7ED] border border-[#FED7AA] p-4 text-sm text-[#9A3412]">
            The system could not identify structured skills from this job description.
            Please review the job requirements and try a more detailed description.
          </div>
        `;
      }
    }

    // Similarity metrics
    setText('sim-cosine-label', `${cosineSimilarity}%`);
    setText('sim-overlap-label', `${keywordOverlap}%`);

    const cosineBar = $('sim-cosine-bar');
    const overlapBar = $('sim-overlap-bar');

    if (cosineBar) cosineBar.style.width = `${Math.max(0, Math.min(100, cosineSimilarity))}%`;
    if (overlapBar) overlapBar.style.width = `${Math.max(0, Math.min(100, keywordOverlap))}%`;

    setText('stat-resume-words', String(stats.resumeWordCount || 0));
    setText('stat-jd-words', String(stats.jdWordCount || 0));
    setText('stat-shared-terms', String(stats.sharedTermCount || 0));

    // Summary
    setText(
      'summary-overview',
      summary.overview || 'The resume-to-job analysis has been completed.'
    );

    const strengthsContainer = $('summary-strengths');

    if (strengthsContainer) {
      strengthsContainer.innerHTML = renderList(
        summary.strengths,
        'No specific strengths were identified from the available evidence.',
        '✓'
      );
    }

    const recommendationsContainer = $('summary-recommendations');

    if (recommendationsContainer) {
      recommendationsContainer.innerHTML = renderList(
        summary.recommendations,
        'Review the missing skills and job requirements to identify improvement areas.',
        '•'
      );
    }

    // New detailed sections
    updateIndustryBanner(data);
    renderAdvancedAnalysis(data);
  }

  // ---------------------------------------------------------
  // SEND RESUME TO FLASK API
  // ---------------------------------------------------------

  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', async () => {
      if (isAnalyzing) return;

      if (!selectedFile) {
        showValidationError(
          'Please upload a PDF, DOCX, or TXT resume before starting analysis.'
        );
        return;
      }

      const jdText = (jdInput?.value || '').trim();

      if (jdText.length < 30) {
        showValidationError(
          'Please paste a job description of at least 30 characters.'
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

        let data;

        try {
          data = await response.json();
        } catch {
          throw new Error('The server returned an invalid response. Check the Flask logs.');
        }

        if (!response.ok) {
          throw new Error(
            data?.error || `Analysis failed with status ${response.status}.`
          );
        }

        if (!data || typeof data !== 'object') {
          throw new Error('The analysis response is empty or invalid.');
        }

        latestAnalysis = data;

        // Used by the PDF export in dashboard.html.
        window.SkillAlignLatestAnalysis = data;

        renderAnalysisData(data);
        switchSection('results');
      } catch (error) {
        console.error('SkillAlign analysis error:', error);

        showValidationError(
          error instanceof Error
            ? error.message
            : 'Unable to reach the Flask analysis server.'
        );
      } finally {
        setLoadingState(false);
      }
    });
  }

  // ---------------------------------------------------------
  // EXPORT BUTTON
  // ---------------------------------------------------------
  // Important:
  // PDF export is handled by the custom PDF script in dashboard.html.
  // Do not attach another click listener here, otherwise PDF and JSON
  // downloads may both start from the same button.

  // ---------------------------------------------------------
  // INITIALIZE
  // ---------------------------------------------------------

  switchSection(activeSection);
  updateJdCounter();
})();