/**
 * THINKWISE — AI Decision Thinking Companion Frontend Application
 * Pure Vanilla JavaScript ES modules, WCAG 2.1 AA accessible, zero framework overhead.
 */

const API = '/v1';

/* ── Application State ── */
const S = {
  decision: '',
  details: '',
  reasons: '',
  type: '',
  analysis: null,
  sessionId: null,
  questions: []
};

/* ── Helper Functions ── */
function esc(t) {
  if (t == null) return '';
  return String(t)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function $(id) {
  return document.getElementById(id);
}

function show(id) {
  const views = ['view-form', 'view-loading', 'view-results', 'view-reflect', 'view-summary'];
  views.forEach(v => {
    const el = $(v);
    if (el) el.classList.add('hidden');
  });
  const target = $(id);
  if (target) {
    target.classList.remove('hidden');
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

/* ── Internship Example Autofill ── */
function fillInternshipExample() {
  $('inp-decision').value = 'Whether to accept a 6-month internship offer';
  $('inp-details').value = 'Good stipend, close to home, working hours 9-5, role in software development, learning opportunities include industry tools, college schedule has classes Monday-Thursday';
  $('inp-reasons').value = 'Mainly considering it because the stipend is good, the company is close to home, and it will provide industry experience';
  $('inp-type').value = 'career';
  $('form-err').textContent = '';
  $('inp-decision').focus();
}

const btnExample = $('btn-internship-example') || $('btn-example');
if (btnExample) {
  btnExample.addEventListener('click', fillInternshipExample);
}
if ($('btn-example') && $('btn-example') !== btnExample) {
  $('btn-example').addEventListener('click', fillInternshipExample);
}

/* ── Web Speech API (Voice Dictation) ── */
const voiceBtn = $('btn-voice-input');
if (voiceBtn) {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRec) {
    const rec = new SpeechRec();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = 'en-US';
    
    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      const dec = $('inp-decision');
      dec.value = dec.value ? (dec.value + ' ' + transcript) : transcript;
      dec.focus();
    };
    
    rec.onstart = () => {
      voiceBtn.setAttribute('aria-pressed', 'true');
      voiceBtn.innerHTML = '<span aria-hidden="true">🔴</span> Listening...';
    };
    
    rec.onend = () => {
      voiceBtn.setAttribute('aria-pressed', 'false');
      voiceBtn.innerHTML = '<span aria-hidden="true">&#x1F399;&#xFE0F;</span> Voice Input';
    };
    
    rec.onerror = () => {
      voiceBtn.setAttribute('aria-pressed', 'false');
      voiceBtn.innerHTML = '<span aria-hidden="true">&#x1F399;&#xFE0F;</span> Voice Input';
    };
    
    voiceBtn.addEventListener('click', () => {
      try {
        rec.start();
      } catch (err) {
        rec.stop();
      }
    });
  } else {
    voiceBtn.style.display = 'none';
  }
}

/* ── Web Speech API (Speech Synthesis / Read Aloud) ── */
const readBtn = $('btn-read-aloud');
if (readBtn && 'speechSynthesis' in window) {
  let isSpeaking = false;
  readBtn.addEventListener('click', () => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      isSpeaking = false;
      readBtn.innerHTML = '<span aria-hidden="true">&#x1F50A;</span> Read Aloud';
      readBtn.setAttribute('aria-pressed', 'false');
    } else {
      const texts = [];
      const cards = document.querySelectorAll('#results-grid .result-card');
      cards.forEach(card => {
        const title = card.querySelector('h3')?.textContent || '';
        const items = Array.from(card.querySelectorAll('.item-title, .item-desc, .stmt-a, .stmt-b, .q-pill, li'))
          .map(el => el.textContent.trim())
          .filter(Boolean);
        if (title) texts.push(title + ': ' + items.join('. '));
      });
      
      const fullText = texts.join('. ') || 'No analysis details to read.';
      const utter = new SpeechSynthesisUtterance(fullText);
      utter.rate = 1.0;
      
      utter.onend = () => {
        isSpeaking = false;
        readBtn.innerHTML = '<span aria-hidden="true">&#x1F50A;</span> Read Aloud';
        readBtn.setAttribute('aria-pressed', 'false');
      };
      
      window.speechSynthesis.speak(utter);
      isSpeaking = true;
      readBtn.innerHTML = '<span aria-hidden="true">⏹️</span> Stop Reading';
      readBtn.setAttribute('aria-pressed', 'true');
    }
  });
}

/* ── Decision Form Submission ── */
$('decision-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  $('form-err').textContent = '';

  const decision = $('inp-decision').value.trim();
  const details = $('inp-details').value.trim();
  const reasons = $('inp-reasons').value.trim();
  const type = $('inp-type').value;

  if (!decision) {
    $('form-err').textContent = 'Please describe the decision you are considering.';
    $('inp-decision').focus();
    return;
  }
  if (!reasons) {
    $('form-err').textContent = 'Please share the reasons you are leaning this way.';
    $('inp-reasons').focus();
    return;
  }

  S.decision = decision;
  S.details = details;
  S.reasons = reasons;
  S.type = type;

  const btn = $('btn-analyze');
  btn.disabled = true;
  btn.textContent = 'Analyzing...';
  
  $('view-results').setAttribute('aria-busy', 'true');
  show('view-loading');

  try {
    const res = await fetch(API + '/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        decision,
        details: details || null,
        reasons,
        decision_type: type || null
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Analysis failed (${res.status})`);
    }

    const data = await res.json();
    S.analysis = data;
    S.sessionId = data.session_id;
    S.questions = data.questions || [];

    renderResults(data);
    show('view-results');
    $('view-results').setAttribute('aria-busy', 'false');

    const heading = $('results-heading');
    if (heading) heading.focus();

  } catch (err) {
    show('view-form');
    $('form-err').textContent = err.message || 'Something went wrong. Please try again.';
    console.error('Analysis error:', err);
    $('inp-decision').focus();
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Analyze My Thinking <span class="btn-arrow" aria-hidden="true">&#8594;</span>';
  }
});

/* ── Results Cards Configuration ── */
const CARDS = [
  { id: 'focus', icon: '🎯', ib: 'rgba(124,58,237,0.12)', ic: '#7C3AED', title: "What you're focusing on", desc: "Factors and reasons most visible in your reasoning", fn: renderFocus },
  { id: 'missing', icon: '🔍', ib: 'rgba(239,68,68,0.12)', ic: '#EF4444', title: "What might be missing", desc: "Critical considerations absent from your current thinking", fn: renderMissing },
  { id: 'assumptions', icon: '⚡', ib: 'rgba(245,158,11,0.12)', ic: '#F59E0B', title: "Assumptions to examine", desc: "Unstated beliefs behind your stated reasons and how to test them", fn: renderAssumptions },
  { id: 'conflicts', icon: '⚖️', ib: 'rgba(56,189,248,0.12)', ic: '#38BDF8', title: "Where your reasoning conflicts", desc: "Tensions or contradictions within your statements", fn: renderConflicts },
  { id: 'questions', icon: '💬', ib: 'rgba(16,185,129,0.12)', ic: '#10B981', title: "Questions to sit with", desc: "Open-ended questions to deepen your reflection", fn: renderQuestions },
  { id: 'biases', icon: '🧠', ib: 'rgba(236,72,153,0.12)', ic: '#EC4899', title: "Possible thinking traps", desc: "Cognitive biases that may be influencing your perspective", fn: renderBiases },
];

function renderResults(a) {
  const grid = $('results-grid');
  grid.innerHTML = '';

  CARDS.forEach((cfg, i) => {
    const card = document.createElement('article');
    card.className = 'result-card';
    card.style.animationDelay = (i * 0.08) + 's';
    card.innerHTML = `
      <div class="card-topbar">
        <div class="card-icon" style="background:${cfg.ib};color:${cfg.ic}" aria-hidden="true">${cfg.icon}</div>
        <div class="card-top-text">
          <h3>${esc(cfg.title)}</h3>
          <p>${esc(cfg.desc)}</p>
        </div>
      </div>
      <div class="card-inner" id="card-${cfg.id}"></div>`;
    grid.appendChild(card);
    cfg.fn(a, $('card-' + cfg.id));
  });
}

function renderFocus(a, el) {
  const rm = a.reasoning_map || {};
  let h = '';
  if (rm.stated_factors?.length) h += makeList('Factors you mentioned:', rm.stated_factors);
  if (rm.stated_reasons?.length) h += makeList('Your stated reasons:', rm.stated_reasons);
  if (rm.most_visible_factors?.length) h += makeList('What dominates your attention:', rm.most_visible_factors);
  if (rm.thin_or_missing_areas?.length) h += makeList('Areas less developed in your thinking:', rm.thin_or_missing_areas);
  el.innerHTML = h || '<p class="placeholder">No specific factors identified.</p>';
}

function makeList(label, items) {
  return `<div class="info-section">
    <span class="info-lbl">${esc(label)}</span>
    <ul class="bullet-list">${items.map(x => `<li>${esc(x)}</li>`).join('')}</ul>
  </div>`;
}

function renderMissing(a, el) {
  if (!a.overlooked_factors?.length) {
    el.innerHTML = '<p class="placeholder">No overlooked factors identified.</p>';
    return;
  }
  el.innerHTML = a.overlooked_factors.map(f => `
    <div class="factor-item">
      <div class="item-title">${esc(f.text)}</div>
      <div class="item-desc">${esc(f.why_it_matters)}</div>
      <button type="button" class="toggle-btn" aria-pressed="false" onclick="this.classList.toggle('on');const on=this.classList.contains('on');this.setAttribute('aria-pressed',on);this.textContent=on?'Noted':'Already considered'">Already considered</button>
    </div>`).join('');
}

function renderAssumptions(a, el) {
  if (!a.assumptions?.length) {
    el.innerHTML = '<p class="placeholder">No assumptions identified.</p>';
    return;
  }
  el.innerHTML = a.assumptions.map(x => `
    <div class="assumption-item">
      <div class="item-title">${esc(x.text)}</div>
      <div class="item-desc"><strong>How to test:</strong> ${esc(x.how_to_test)}</div>
      <button type="button" class="toggle-btn" aria-pressed="false" onclick="this.classList.toggle('on');const on=this.classList.contains('on');this.setAttribute('aria-pressed',on);this.textContent=on?'Exploring':'Worth exploring'">Worth exploring</button>
    </div>`).join('');
}

function renderConflicts(a, el) {
  if (!a.conflicts?.length) {
    el.innerHTML = '<p class="placeholder">No direct conflicts identified.</p>';
    return;
  }
  el.innerHTML = a.conflicts.map(c => `
    <div class="conflict-item">
      <div class="conflict-pair">
        <p class="stmt-a">&#34;${esc(c.statement_a)}&#34;</p>
        <p class="stmt-b">&#34;${esc(c.statement_b)}&#34;</p>
      </div>
      <p class="item-desc"><strong>Tension:</strong> ${esc(c.tension)}</p>
    </div>`).join('');
}

function renderQuestions(a, el) {
  if (!a.questions?.length) {
    el.innerHTML = '<p class="placeholder">No questions generated.</p>';
    return;
  }
  const byTheme = {};
  a.questions.forEach(q => {
    (byTheme[q.theme] = byTheme[q.theme] || []).push(q);
  });
  el.innerHTML = Object.entries(byTheme).map(([theme, qs]) => `
    <div class="info-section">
      <span class="info-lbl">${esc(theme.replace(/_/g, ' '))}</span>
      ${qs.map(q => `<div class="q-pill">${esc(q.text)}</div>`).join('')}
    </div>`).join('');
}

function renderBiases(a, el) {
  if (!a.possible_biases?.length) {
    el.innerHTML = '<p class="placeholder">No thinking traps identified.</p>';
    return;
  }
  el.innerHTML = a.possible_biases.map(b => `
    <div class="bias-item">
      <div class="item-title">${esc(b.name)}</div>
      <div class="item-desc">${esc(b.why_it_may_apply)}</div>
    </div>`).join('');
}

/* ── Results Navigation ── */
$('btn-go-reflect').addEventListener('click', () => {
  if (!S.questions.length) {
    buildSummary(null, []);
    show('view-summary');
    return;
  }
  renderReflection(S.questions);
  show('view-reflect');
});

$('btn-skip-reflect').addEventListener('click', () => {
  buildSummary(null, []);
  show('view-summary');
});

/* ── Reflection Flow ── */
function renderReflection(qs) {
  $('q-list').innerHTML = qs.map((q, i) => `
    <div class="q-item" style="animation-delay:${i * 0.07}s">
      <div class="q-item-head">
        <span class="q-theme">${esc((q.theme || 'reflect').toUpperCase())}</span>
        <p class="q-text">${esc(q.text)}</p>
      </div>
      <textarea class="q-answer form-field" rows="3" placeholder="Take your time to think about this..." data-qid="${esc(q.id)}"></textarea>
    </div>`).join('');
}

$('btn-submit-reflect').addEventListener('click', async () => {
  const answers = Array.from(document.querySelectorAll('.q-answer'))
    .map(ta => ({ question_id: ta.dataset.qid, answer: ta.value.trim() }));
  
  const btn = $('btn-submit-reflect');
  btn.disabled = true;
  btn.textContent = 'Generating...';

  try {
    if (S.sessionId) {
      const res = await fetch(API + '/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: S.sessionId, answers })
      });
      if (res.ok) {
        const data = await res.json();
        buildSummary(data, answers);
        show('view-summary');
        return;
      }
    }
  } catch (e) {
    console.warn('Refine fallback used:', e);
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Generate My Summary <span class="btn-arrow" aria-hidden="true">&#8594;</span>';
  }

  buildSummary(null, answers);
  show('view-summary');
});

$('btn-skip-reflect2').addEventListener('click', () => {
  buildSummary(null, []);
  show('view-summary');
});

/* ── Summary Generation ── */
function buildSummary(refinement, answers) {
  const a = S.analysis;
  if (!a) return;

  let md = '';
  if (refinement?.thinking_summary) {
    md = refinement.thinking_summary;
  } else {
    const L = [
      '# My Thinking Summary',
      '',
      '**Decision:** ' + (a.decision_restated || S.decision),
      S.details ? '**Details:** ' + S.details : '',
      '**Your reasons:** ' + S.reasons,
      S.type ? '**Category:** ' + S.type : '',
      '',
      '---',
      ''
    ];
    const add = (lines) => lines.forEach(l => L.push(l));

    if (a.reasoning_map?.stated_factors?.length) {
      add(["## What You're Focusing On", '']);
      a.reasoning_map.stated_factors.forEach(f => L.push('- ' + f));
      L.push('');
    }
    if (a.overlooked_factors?.length) {
      add(['## What Might Be Missing', '']);
      a.overlooked_factors.forEach(f => add(['### ' + f.text, '', '*Why it matters:* ' + f.why_it_matters, '']));
    }
    if (a.assumptions?.length) {
      add(['## Assumptions to Examine', '']);
      a.assumptions.forEach(x => add(['### ' + x.text, '', '*How to test:* ' + x.how_to_test, '']));
    }
    if (a.conflicts?.length) {
      add(['## Where Your Reasoning Conflicts', '']);
      a.conflicts.forEach(c => add(['> "' + c.statement_a + '"', '> "' + c.statement_b + '"', '', '*Tension:* ' + c.tension, '']));
    }
    if (a.questions?.length && answers.length) {
      add(['## Questions & Your Reflections', '']);
      a.questions.forEach(q => {
        const ans = answers.find(x => x.question_id === q.id);
        add(['**' + q.text + '**', ans?.answer ? '→ ' + ans.answer : '→ (Not answered)', '']);
      });
    }
    if (a.possible_biases?.length) {
      add(['## Possible Thinking Traps', '']);
      a.possible_biases.forEach(b => L.push('- **' + b.name + ':** ' + b.why_it_may_apply));
      L.push('');
    }
    add([
      '---',
      '',
      '**Notice:** The decision stays entirely yours.',
      '',
      '*Generated on: ' + new Date().toLocaleString() + '*'
    ]);
    md = L.filter(x => x !== undefined).join('\n');
  }

  $('summary-body').textContent = md;
}

/* ── Copy & Download Summary ── */
$('btn-copy').addEventListener('click', () => {
  navigator.clipboard.writeText($('summary-body').textContent).then(() => {
    $('btn-copy').textContent = 'Copied!';
    setTimeout(() => { $('btn-copy').textContent = '📋 Copy Summary'; }, 2000);
  });
});

$('btn-download').addEventListener('click', () => {
  const blob = new Blob([$('summary-body').textContent], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `thinkwise-thinking-summary-${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
});

$('btn-new').addEventListener('click', () => {
  $('decision-form').reset();
  $('form-err').textContent = '';
  S.analysis = null;
  S.sessionId = null;
  S.questions = [];
  show('view-form');
  $('inp-decision').focus();
});

/* ── Initial Focus ── */
$('inp-decision').focus();
console.log('Thinkwise AI Companion Initialized');
