const API_BASE = (window.AQG_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const app = document.querySelector('#app');
const state = {
  token: localStorage.getItem('aqg_token'),
  user: null,
  documents: [],
  quizzes: [],
  performance: null,
  resources: [],
  history: [],
  activeQuiz: null,
  assessmentResult: null,
  attemptResult: null,
  activeResourceId: null,
  authMode: 'login',
  intendedAction: null,
  message: '',
};

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

function setMessage(message) {
  state.message = message;
  const target = document.querySelector('#message');
  if (target) target.textContent = message;
}

function openAuth(action) {
  state.intendedAction = action || null;
  render();
  document.querySelector('#auth-modal')?.showModal();
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}

function publicPage() {
  return `
    <header class="site-header" id="home">
      <nav class="nav container" aria-label="Main navigation">
        <a class="brand" href="#home" aria-label="AQG home"><span class="brand-mark">A</span> AQG</a>
        <div class="nav-links">
          <a href="#features">Features</a><a href="#how-it-works">How it works</a><a href="#about">About</a>
          <button class="nav-signin" data-action="signin">Sign in</button>
          <button class="button button-light button-small" data-action="signup">Get started</button>
        </div>
      </nav>
      <section class="hero container">
        <div class="hero-copy">
          <span class="eyebrow"><span class="eyebrow-dot"></span> A smarter way to study</span>
          <h1>Make your learning materials work <em>harder.</em></h1>
          <p>Turn course notes into focused revision, practice questions, and useful feedback — all in one place.</p>
          <div class="hero-actions">
            <button class="button button-primary" data-action="signup">Start learning <span aria-hidden="true">→</span></button>
            <a class="button button-outline" href="#how-it-works">See how it works</a>
          </div>
          <div class="hero-note"><span class="note-check">✓</span> Your study space stays personal and organized</div>
        </div>
        <div class="hero-visual" aria-label="AQG study dashboard preview">
          <div class="visual-orbit orbit-one"></div><div class="visual-orbit orbit-two"></div>
          <div class="study-preview">
            <div class="preview-top"><span class="preview-dot"></span><span class="preview-dot"></span><span class="preview-dot"></span><span class="preview-label">YOUR STUDY SPACE</span></div>
            <div class="preview-title">Learning, in focus <span class="spark">✳</span></div>
            <div class="preview-subtitle">A little progress adds up.</div>
            <div class="preview-progress"><span></span></div>
            <div class="preview-row"><span class="preview-icon blue">▤</span><span><b>Course notes</b><small>Organized and ready to review</small></span><span class="row-arrow">↗</span></div>
            <div class="preview-row"><span class="preview-icon yellow">✎</span><span><b>Practice set</b><small>Questions for your next study session</small></span><span class="row-arrow">↗</span></div>
            <div class="preview-row"><span class="preview-icon lilac">◎</span><span><b>Study insights</b><small>See what you have been working on</small></span><span class="row-arrow">↗</span></div>
          </div>
          <div class="floating-note"><span>✦</span><div><b>Study with purpose</b><small>One step at a time</small></div></div>
        </div>
      </section>
    </header>
    <main>
      <section class="trust-strip"><div class="container trust-inner"><span>BUILT FOR HOW STUDENTS LEARN</span><span>Understand <b>·</b> Practice <b>·</b> Improve</span></div></section>
      <section class="section container" id="features">
        <div class="section-heading"><span class="kicker">YOUR STUDY TOOLKIT</span><h2>Everything you need to move forward.</h2><p>Keep learning resources, practice, and progress connected.</p></div>
        <div class="feature-grid">
          <article class="feature-card"><span class="feature-icon icon-blue">▤</span><h3>Your materials, organized</h3><p>Keep course content and notes together in a personal study space.</p><button class="text-action" data-action="upload">Explore materials <span>→</span></button></article>
          <article class="feature-card"><span class="feature-icon icon-yellow">✳</span><h3>Practice that fits your topic</h3><p>Create practice questions and check your understanding as you go.</p><button class="text-action" data-action="quiz">Try question practice <span>→</span></button></article>
          <article class="feature-card"><span class="feature-icon icon-lilac">◎</span><h3>See your progress</h3><p>Review saved attempts and get a clearer picture of your learning.</p><button class="text-action" data-action="performance">View progress <span>→</span></button></article>
        </div>
      </section>
      <section class="how-section" id="how-it-works"><div class="container how-inner">
        <div><span class="kicker">A SIMPLE STUDY LOOP</span><h2>From course content<br>to confident recall.</h2><p>AQG helps you turn what you are learning into practice you can return to.</p></div>
        <ol class="steps"><li><span>01</span><div><b>Add your study material</b><p>Start with the notes and content you are already using.</p></div></li><li><span>02</span><div><b>Build a focused practice set</b><p>Choose a topic and question style to check your understanding.</p></div></li><li><span>03</span><div><b>Review and keep improving</b><p>Save your attempts and revisit your learning over time.</p></div></li></ol>
      </div></section>
      <section class="about-section container" id="about"><div class="about-card"><div><span class="kicker">MADE FOR LEARNING</span><h2>Useful tools.<br>Clear progress.</h2></div><p>AQG brings study materials and practice into one workspace, so your next revision session has a clear place to begin.</p><button class="button button-primary" data-action="signup">Create your study space <span>→</span></button></div></section>
    </main>
    <footer><div class="container footer-inner"><a class="brand" href="#home"><span class="brand-mark">A</span> AQG</a><span>Learn with intention.</span><a href="mailto:help@aqg.local">Help &amp; support</a></div></footer>
    <dialog class="auth-modal" id="auth-modal"><button class="modal-close" aria-label="Close sign in" data-action="close-auth">×</button><span class="kicker">WELCOME TO AQG</span><h2 id="auth-title">Welcome back</h2><p id="auth-description">Sign in to pick up where you left off.</p><div id="auth-error" class="form-error" role="alert"></div><form id="auth-form">
      <label id="name-field" class="field hidden">Full name<input name="full_name" autocomplete="name" minlength="2"></label>
      <label class="field">Email address<input name="email" type="email" autocomplete="email" required></label>
      <label class="field">Password<input name="password" type="password" autocomplete="current-password" minlength="8" required></label>
      <button class="button button-primary button-wide" type="submit" id="auth-submit">Sign in</button>
    </form><div class="auth-switch"><span id="auth-switch-text">New to AQG?</span> <button data-action="toggle-auth" id="auth-switch-button">Create an account</button></div><p class="auth-disclaimer">Demo email sign-in. Google sign-in is not configured in this local prototype.</p></dialog>`;
}

function dashboardPage() {
  const avg = state.performance?.average_score;
  const documentOptions = state.documents.map(document =>
    `<option value="${escapeHtml(document.id)}">${escapeHtml(document.title)}</option>`
  ).join('');
  return `
    <header class="app-header"><nav class="nav container" aria-label="Main navigation"><a class="brand" href="#home"><span class="brand-mark">A</span> AQG</a><div class="nav-links"><a href="#workspace">Overview</a><a href="#documents">Materials</a><a href="#practice">Practice</a><a href="#progress">Progress</a><button class="nav-signin" data-action="logout">Sign out</button></div></nav></header>
    <main class="container dashboard" id="workspace">
      <div id="message" class="status-message" role="status">${escapeHtml(state.message)}</div>
      <section class="welcome-row"><div><span class="kicker">YOUR STUDY SPACE</span><h1>Good to see you, ${escapeHtml(state.user?.full_name?.split(' ')[0] || 'learner')}.</h1><p>What would you like to work on today?</p></div><span class="user-chip">${escapeHtml(state.user?.email || '')}</span></section>
      <section class="metric-grid" aria-label="Study overview"><div class="metric-card"><span>Study materials</span><strong>${state.documents.length}</strong><small>Saved to your space</small></div><div class="metric-card"><span>Practice sets</span><strong>${state.quizzes.length}</strong><small>Ready when you are</small></div><div class="metric-card"><span>Assessment attempts</span><strong>${state.performance?.total_attempts || 0}</strong><small>Saved attempts</small></div><div class="metric-card"><span>Average score</span><strong>${avg === undefined ? '—' : `${avg}%`}</strong><small>${avg === undefined ? 'Complete an assessment to see this' : 'Across your saved attempts'}</small></div></section>
      <div class="dashboard-grid">
        <section class="workspace-card" id="documents"><div class="card-heading"><div><span class="kicker">YOUR LIBRARY</span><h2>Study materials</h2></div><span class="card-symbol icon-blue">▤</span></div><p>Add study text to create a saved document for your workspace.</p><form id="upload-form"><label class="field">Title<input name="title" required minlength="2" value="My study notes"></label><label class="field">Study text<textarea name="content" rows="4" required minlength="20" placeholder="Paste text from your notes here"></textarea></label><button class="button button-primary" type="submit">Save material <span>→</span></button></form><div class="saved-list">${state.documents.length ? state.documents.map(doc => `<div class="saved-item"><span class="saved-icon">▤</span><span><b>${escapeHtml(doc.title)}</b><small>${escapeHtml(doc.status)} · ${new Date(doc.created_at).toLocaleDateString()}</small></span></div>`).join('') : '<p class="empty-state">Your library is empty. Add your first notes above.</p>'}</div></section>
        <section class="workspace-card" id="practice"><div class="card-heading"><div><span class="kicker">ACTIVE RECALL</span><h2>Build a practice set</h2></div><span class="card-symbol icon-yellow">✳</span></div><p>Choose a topic and start a short practice session.</p><form id="quiz-form"><label class="field">Topic<input name="topic" required minlength="2" value="Machine learning"></label><label class="field">Study document<select name="document_id"><option value="">None — use general knowledge</option>${documentOptions}</select></label><div class="form-columns"><label class="field">Question style<select name="question_type"><option value="multiple_choice">Multiple choice</option><option value="true_false">True or false</option><option value="short_answer">Short answer</option></select></label><label class="field">Difficulty<select name="difficulty"><option value="easy">Easy</option><option value="intermediate" selected>Intermediate</option><option value="hard">Hard</option></select></label></div><label class="field">Number of questions<input name="count" type="number" min="1" max="8" value="3" required></label><button class="button button-primary" type="submit">Generate practice <span>→</span></button></form>
        <div id="quiz-area">${renderActiveQuiz()}</div></section>
      </div>
      <div class="dashboard-grid lower-grid"><section class="workspace-card" id="progress"><div class="card-heading"><div><span class="kicker">YOUR PROGRESS</span><h2>Assessment history</h2></div><span class="card-symbol icon-lilac">◎</span></div>${state.performance?.recent_results?.length ? state.performance.recent_results.map(attempt => `<div class="saved-item"><span class="result-score">${attempt.percentage}%</span><span><b>${attempt.score} of ${attempt.total} correct</b><small>${new Date(attempt.submitted_at).toLocaleString()}</small></span></div>`).join('') : '<p class="empty-state">No completed assessments yet. Finish a practice set to see your results here.</p>'}</section>
      <section class="workspace-card"><div class="card-heading"><div><span class="kicker">STUDY TOOLS</span><h2>Make a study resource</h2></div><span class="card-symbol icon-lilac">✎</span></div><form id="resource-form"><label class="field">Topic<input name="topic" required value="Machine learning"></label><label class="field">Resource<select name="kind"><option value="summary">Summary</option><option value="flashcards">Flashcards</option><option value="concepts">Key concepts</option><option value="revision_notes">Revision notes</option><option value="definitions">Definitions</option></select></label><label class="field">Saved study document<select name="document_id"><option value="">None</option>${documentOptions}</select></label><label class="field">Or source text<textarea name="source_text" rows="3" placeholder="Paste optional source text"></textarea></label><button class="button button-primary" type="submit">Create resource <span>→</span></button></form><div class="saved-list">${state.resources.slice(0, 3).map(item => `<div class="saved-item"><span class="saved-icon">✎</span><span><b>${escapeHtml(item.title)}</b><small>${escapeHtml(item.kind)}</small></span></div>`).join('')}</div></section></div>
    </main><footer><div class="container footer-inner"><a class="brand" href="#home"><span class="brand-mark">A</span> AQG</a><span>Your study space, at your pace.</span><a href="mailto:help@aqg.local">Help &amp; support</a></div></footer>`;
}

function renderActiveQuiz() {
  if (!state.activeQuiz) return '';
  return `<div class="active-quiz"><div class="quiz-title"><span class="kicker">PRACTICE SET</span><h3>${escapeHtml(state.activeQuiz.quiz.title)}</h3></div><form id="assessment-form">${state.activeQuiz.questions.map((q, index) => `<fieldset class="question"><legend><b>${index + 1}.</b> ${escapeHtml(q.question_text)}</legend>${q.options?.length ? q.options.map((option, i) => `<label class="option"><input type="radio" name="${escapeHtml(q.id)}" value="${escapeHtml(option)}"><span>${escapeHtml(option)}</span></label>`).join('') : `<label class="field">Your answer<textarea name="${escapeHtml(q.id)}" rows="3"></textarea></label>`}</fieldset>`).join('')}<button class="button button-primary" type="submit">Submit answers</button></form></div>`;
}

function enhanceDashboard() {
  if (!state.user) return;

  const uploadForm = document.querySelector('#upload-form');
  if (uploadForm && !uploadForm.querySelector('input[type="file"]')) {
    const fileField = document.createElement('label');
    fileField.className = 'field';
    fileField.innerHTML = 'PDF document<input name="file" type="file" accept=".pdf,application/pdf"><small>PDF only, up to 10 MB. Scanned PDFs need OCR and are not supported.</small>';
    uploadForm.prepend(fileField);
    const textInput = uploadForm.querySelector('textarea[name="content"]');
    if (textInput) {
      textInput.required = false;
      textInput.placeholder = 'Optional: paste text instead of uploading a PDF';
    }
  }

  const questionType = document.querySelector('#quiz-form select[name="question_type"]');
  if (questionType) {
    [
      ['essay', 'Essay'],
      ['scenario_based', 'Scenario based'],
      ['case_study', 'Case study'],
      ['application', 'Application / problem solving'],
      ['mixed', 'Mixed question types'],
    ].forEach(([value, label]) => {
      if (!questionType.querySelector(`option[value="${value}"]`)) {
        questionType.add(new Option(label, value));
      }
    });
  }

  document.querySelectorAll('#documents .saved-list .saved-item').forEach((row, index) => {
    const document = state.documents[index];
    if (document && !row.querySelector('[data-action="delete-document"]')) {
      row.insertAdjacentHTML(
        'beforeend',
        `<button class="text-action" type="button" data-action="delete-document" data-document-id="${escapeHtml(document.id)}" aria-label="Delete ${escapeHtml(document.title)}">Delete</button>`,
      );
    }
  });

  const metricGrid = document.querySelector('.metric-grid');
  if (metricGrid && state.performance?.highest_score !== undefined && !metricGrid.querySelector('.highest-score')) {
    const metric = document.createElement('div');
    metric.className = 'metric-card highest-score';
    metric.innerHTML = `<span>Highest score</span><strong>${escapeHtml(state.performance.highest_score)}%</strong><small>From saved assessments</small>`;
    metricGrid.append(metric);
  }

  const navigation = document.querySelector('.app-header .nav-links');
  if (navigation && !navigation.querySelector('[href="#history"]')) {
    navigation.insertAdjacentHTML(
      'beforeend',
      '<a href="#history">Quiz history</a><a href="#study-history">Study resources</a>',
    );
  }

  const lowerGrid = document.querySelector('.lower-grid');
  if (lowerGrid) {
    let historyPanel = document.querySelector('#history');
    if (!historyPanel) {
      historyPanel = document.createElement('section');
      historyPanel.className = 'workspace-card history-panel';
      historyPanel.id = 'history';
      lowerGrid.after(historyPanel);
    }
    historyPanel.innerHTML = `
      <div class="card-heading"><div><span class="kicker">SAVED WORK</span><h2>Quiz history</h2></div></div>
      ${state.quizzes.length ? state.quizzes.map(item => `
        <div class="saved-item">
          <span class="saved-icon">✓</span>
          <span><b>${escapeHtml(item.quiz.title)}</b><small>${escapeHtml(item.quiz.topic)} · ${new Date(item.quiz.created_at).toLocaleDateString()}</small></span>
          <button class="text-action" type="button" data-action="open-saved-quiz" data-quiz-id="${escapeHtml(item.quiz.id)}">Open / retake</button>
        </div>`).join('') : '<p class="empty-state">Generated quizzes will appear here.</p>'}
      <h3>Assessment attempts</h3>
      ${state.history.length ? state.history.map(attempt => `
        <div class="saved-item">
          <span class="result-score">${attempt.percentage}%</span>
          <span><b>${attempt.score} of ${attempt.total} correct</b><small>${new Date(attempt.submitted_at).toLocaleString()}</small></span>
          <button class="text-action" type="button" data-action="open-attempt" data-attempt-id="${escapeHtml(attempt.id)}">Review</button>
        </div>`).join('') : '<p class="empty-state">Completed assessments will appear here.</p>'}
      <div class="card-heading history-subheading" id="study-history"><div><span class="kicker">SAVED RESOURCES</span><h2>Study resources</h2></div></div>
      ${state.resources.length ? state.resources.map(item => `
        <div class="saved-item">
          <span class="saved-icon">✎</span>
          <span><b>${escapeHtml(item.title)}</b><small>${escapeHtml(item.kind)} · ${new Date(item.created_at).toLocaleDateString()}</small></span>
          <button class="text-action" type="button" data-action="open-resource" data-resource-id="${escapeHtml(item.id)}">View</button>
        </div>`).join('') : '<p class="empty-state">Generated study resources will appear here.</p>'}
      ${state.activeResourceId ? renderResourceDetails() : ''}
      ${state.assessmentResult ? renderAssessmentResult(state.assessmentResult) : ''}
      ${state.attemptResult ? renderAttemptResult(state.attemptResult) : ''}
    `;
  }

  const assessmentForm = document.querySelector('#assessment-form');
  if (assessmentForm && !assessmentForm.querySelector('.assessment-progress')) {
    const questions = state.activeQuiz?.questions || [];
    assessmentForm.querySelectorAll('.question').forEach((question, index) => {
      const sourceReference = questions[index]?.source_reference;
      if (sourceReference) {
        const source = document.createElement('p');
        source.className = 'source-reference';
        source.textContent = `Source: ${sourceReference}`;
        question.append(source);
      }
    });
    const progress = document.createElement('progress');
    progress.className = 'assessment-progress';
    progress.max = questions.length || 1;
    progress.value = 0;
    progress.setAttribute('aria-label', 'Assessment answer progress');
    const updateProgress = () => {
      progress.value = questions.filter(question =>
        assessmentForm.querySelector(`[name="${CSS.escape(question.id)}"]:checked`)?.value
        || assessmentForm.querySelector(`[name="${CSS.escape(question.id)}"]`)?.value?.trim(),
      ).length;
    };
    assessmentForm.prepend(progress);
    assessmentForm.addEventListener('input', updateProgress);
    assessmentForm.addEventListener('change', updateProgress);
    assessmentForm.querySelectorAll('.question').forEach((question, index, list) => {
      const navigationControls = document.createElement('div');
      navigationControls.className = 'question-nav';
      navigationControls.innerHTML = `
        <button type="button" data-question-index="${Math.max(0, index - 1)}" ${index === 0 ? 'disabled' : ''}>Previous question</button>
        <span>${index + 1} of ${list.length}</span>
        <button type="button" data-question-index="${Math.min(list.length - 1, index + 1)}" ${index === list.length - 1 ? 'disabled' : ''}>Next question</button>`;
      question.append(navigationControls);
    });
    assessmentForm.addEventListener('click', event => {
      const navigationButton = event.target.closest('[data-question-index]');
      if (!navigationButton || navigationButton.disabled) return;
      const target = assessmentForm.querySelectorAll('.question')[Number(navigationButton.dataset.questionIndex)];
      target?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      target?.querySelector('input, textarea')?.focus({ preventScroll: true });
    });
  }
}

function renderResourceDetails() {
  const item = state.resources.find(resource => resource.id === state.activeResourceId);
  if (!item) return '';
  return `<article class="result-review"><h3>${escapeHtml(item.title)}</h3><pre>${escapeHtml(JSON.stringify(item.content, null, 2))}</pre></article>`;
}

function renderAssessmentResult(result) {
  return `<article class="result-review" role="status">
    <h3>Assessment result: ${result.score} / ${result.total} (${result.percentage}%)</h3>
    ${result.results.map((item, index) => `<div class="answer-review">
      <b>${index + 1}. ${escapeHtml(item.question_text)}</b>
      <p class="${item.is_correct ? 'answer-correct' : 'answer-incorrect'}">${item.is_correct ? 'Correct' : 'Incorrect'} · Your answer: ${escapeHtml(item.user_answer || 'Not answered')}</p>
      ${item.is_correct ? '' : `<p>Expected answer: ${escapeHtml(item.correct_answer)}</p>`}
      <p>${escapeHtml(item.explanation || '')}</p>
    </div>`).join('')}
    <button class="text-action" type="button" data-action="clear-result">Close review</button>
  </article>`;
}

function renderAttemptResult(result) {
  return `<article class="result-review"><h3>${escapeHtml(result.quiz?.title || 'Assessment review')}</h3>
    <p>Score: ${result.attempt.percentage}% (${result.attempt.score} / ${result.attempt.total})</p>
    ${result.results.map((item, index) => `<div class="answer-review">
      <b>${index + 1}. ${escapeHtml(item.question_text)}</b>
      <p class="${item.is_correct ? 'answer-correct' : 'answer-incorrect'}">${item.is_correct ? 'Correct' : 'Incorrect'} · Your answer: ${escapeHtml(item.user_answer || 'Not answered')}</p>
      ${item.is_correct ? '' : `<p>Expected answer: ${escapeHtml(item.correct_answer)}</p>`}
      <p>${escapeHtml(item.explanation)}</p>
    </div>`).join('')}
    <button class="text-action" type="button" data-action="clear-result">Close review</button>
  </article>`;
}

function render() {
  app.innerHTML = state.user ? dashboardPage() : publicPage();
  enhanceDashboard();
  const dialog = document.querySelector('#auth-modal');
  if (dialog && state.authMode) {
    const registering = state.authMode === 'register';
    document.querySelector('#auth-title').textContent = registering ? 'Create your account' : 'Welcome back';
    document.querySelector('#auth-description').textContent = registering ? 'Set up your personal study space.' : 'Sign in to pick up where you left off.';
    document.querySelector('#auth-submit').textContent = registering ? 'Create account' : 'Sign in';
    document.querySelector('#name-field').classList.toggle('hidden', !registering);
    document.querySelector('#name-field input').required = registering;
    document.querySelector('#auth-switch-text').textContent = registering ? 'Already have an account?' : 'New to AQG?';
    document.querySelector('#auth-switch-button').textContent = registering ? 'Sign in instead' : 'Create an account';
  }
}

async function refreshDashboard() {
  const [user, documents, quizzes, performance, resources, history] = await Promise.all([
    request('/api/auth/me'),
    request('/api/documents'),
    request('/api/quizzes'),
    request('/api/performance'),
    request('/api/study_resources'),
    request('/api/assessments/history'),
  ]);
  state.user = user;
  state.documents = documents;
  state.quizzes = quizzes;
  state.performance = performance;
  state.resources = resources;
  state.history = history;
}

function showAuthError(error) {
  const node = document.querySelector('#auth-error');
  if (node) node.textContent = error.message || 'Please try again.';
}

app.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const action = button.dataset.action;
  if (action === 'signin' || action === 'signup') {
    state.authMode = action === 'signup' ? 'register' : 'login';
    openAuth();
  } else if (action === 'close-auth') {
    document.querySelector('#auth-modal')?.close();
  } else if (action === 'toggle-auth') {
    state.authMode = state.authMode === 'login' ? 'register' : 'login';
    render();
    document.querySelector('#auth-modal')?.showModal();
  } else if (action === 'open-saved-quiz') {
    try {
      state.activeQuiz = await request(`/api/quizzes/${encodeURIComponent(button.dataset.quizId)}`);
      state.assessmentResult = null;
      state.attemptResult = null;
      render();
      document.querySelector('#practice')?.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
      setMessage(error.message);
    }
  } else if (action === 'open-resource') {
    state.activeResourceId = button.dataset.resourceId;
    state.assessmentResult = null;
    state.attemptResult = null;
    render();
    document.querySelector('#history')?.scrollIntoView({ behavior: 'smooth' });
  } else if (action === 'delete-document') {
    if (!window.confirm('Delete this study document? Saved quizzes and results will not be deleted.')) return;
    try {
      await request(`/api/documents/${encodeURIComponent(button.dataset.documentId)}`, { method: 'DELETE' });
      await refreshDashboard();
      state.message = 'Study document deleted.';
      render();
    } catch (error) {
      setMessage(error.message);
    }
  } else if (action === 'open-attempt') {
    try {
      state.attemptResult = await request(`/api/assessments/${encodeURIComponent(button.dataset.attemptId)}`);
      state.assessmentResult = null;
      state.activeResourceId = null;
      render();
      document.querySelector('#history')?.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
      setMessage(error.message);
    }
  } else if (action === 'clear-result') {
    state.assessmentResult = null;
    state.attemptResult = null;
    state.activeResourceId = null;
    render();
  } else if (action === 'logout') {
    localStorage.removeItem('aqg_token');
    state.token = null;
    state.user = null;
    state.documents = [];
    state.quizzes = [];
    state.performance = null;
    state.resources = [];
    state.history = [];
    state.activeQuiz = null;
    state.assessmentResult = null;
    state.attemptResult = null;
    state.activeResourceId = null;
    state.message = '';
    render();
  } else if (!state.user) {
    state.authMode = 'login';
    openAuth(action);
  } else if (action === 'upload') {
    document.querySelector('#documents')?.scrollIntoView({ behavior: 'smooth' });
  } else if (action === 'quiz') {
    document.querySelector('#practice')?.scrollIntoView({ behavior: 'smooth' });
  } else if (action === 'performance') {
    document.querySelector('#progress')?.scrollIntoView({ behavior: 'smooth' });
  }
});

app.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    if (form.id === 'auth-form') {
      const registering = state.authMode === 'register';
      const result = await request(registering ? '/api/auth/register' : '/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(registering
          ? { full_name: data.full_name, email: data.email, password: data.password }
          : { email: data.email, password: data.password }),
      });
      state.token = result.access_token;
      localStorage.setItem('aqg_token', state.token);
      await refreshDashboard();
      state.message = 'You are signed in. Your study space is ready.';
      state.authMode = null;
      render();
      if (state.intendedAction) {
        const target = { upload: '#documents', quiz: '#practice', performance: '#progress' }[state.intendedAction];
        document.querySelector(target)?.scrollIntoView({ behavior: 'smooth' });
        state.intendedAction = null;
      }
    } else if (form.id === 'upload-form') {
      if (data.file?.size) {
        if (data.file.size > 10 * 1024 * 1024) throw new Error('The PDF exceeds the 10 MB upload limit.');
        if (data.file.type !== 'application/pdf' || !data.file.name.toLowerCase().endsWith('.pdf')) {
          throw new Error('Choose a valid PDF file.');
        }
        const upload = new FormData();
        upload.append('title', data.title);
        upload.append('file', data.file);
        await request('/api/documents/upload-file', { method: 'POST', body: upload });
      } else {
        if (typeof data.content !== 'string' || data.content.trim().length < 20) {
          throw new Error('Add at least 20 characters of study text or select a PDF.');
        }
        await request('/api/documents/upload', {
          method: 'POST',
          body: JSON.stringify({ title: data.title, content: data.content }),
        });
      }
      await refreshDashboard();
      state.message = 'Study material uploaded and processed.';
      render();
    } else if (form.id === 'quiz-form') {
      const result = await request('/api/quizzes/generate', { method: 'POST', body: JSON.stringify({ topic: data.topic, question_type: data.question_type, difficulty: data.difficulty, count: Number(data.count), document_id: data.document_id || undefined }) });
      state.activeQuiz = result;
      state.assessmentResult = null;
      state.attemptResult = null;
      await refreshDashboard();
      state.message = 'Your practice set is ready.';
      render();
      document.querySelector('#quiz-area')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (form.id === 'assessment-form') {
      if (!window.confirm('Submit this assessment now? You can review your answers after submission.')) return;
      const answers = state.activeQuiz.questions.map(question => {
        const selected = form.querySelector(`[name="${CSS.escape(question.id)}"]:checked`)?.value
          || form.querySelector(`[name="${CSS.escape(question.id)}"]`)?.value
          || '';
        return { question_id: question.id, answer: selected };
      });
      const result = await request('/api/assessments/submit', { method: 'POST', body: JSON.stringify({ quiz_id: state.activeQuiz.quiz.id, answers }) });
      state.assessmentResult = result;
      state.attemptResult = null;
      state.activeQuiz = null;
      await refreshDashboard();
      state.message = `Assessment saved: ${result.score} of ${result.total} correct (${result.percentage}%).`;
      render();
      document.querySelector('#history')?.scrollIntoView({ behavior: 'smooth' });
    } else if (form.id === 'resource-form') {
      const result = await request('/api/study_resources/generate', { method: 'POST', body: JSON.stringify({ kind: data.kind, topic: data.topic, document_id: data.document_id || undefined, source_text: data.source_text || undefined }) });
      state.activeResourceId = result.resource.id;
      await refreshDashboard();
      state.message = 'Study resource saved.';
      render();
    }
  } catch (error) {
    if (form.id === 'auth-form') showAuthError(error);
    else setMessage(error.message);
  }
});

render();
if (state.token) {
  refreshDashboard().then(() => render()).catch(() => {
    localStorage.removeItem('aqg_token');
    state.token = null;
    state.user = null;
    render();
  });
}
