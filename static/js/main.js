const slider = document.getElementById('slider');
const progressDots = [...document.querySelectorAll('.progress-dot')];
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');

const startBtn = document.getElementById('startBtn');
const restartBtn = document.getElementById('restartBtn');
const websiteInput = document.getElementById('websiteInput');

const ideaModal = document.getElementById('ideaModal');
const regenerateModal = document.getElementById('regenerateModal');

const ideaForm = document.getElementById('ideaForm');
const regenerateForm = document.getElementById('regenerateForm');

const modalStoryline = document.getElementById('modalStoryline');
const modalCharacters = document.getElementById('modalCharacters');
const modalLocation = document.getElementById('modalLocation');

const ideasGrid = document.getElementById('ideasGrid');
const scriptView = document.getElementById('scriptView');
const storyboardGrid = document.getElementById('storyboardGrid');

const loadingSteps = [
  'Preparing next step…',
  'Clara (Brand Strategist) is working…',
  'Ava (Creative Director) is brainstorming concepts…',
  'Theo (Screenwriter) is drafting the narrative…',
  'Arlo (Storyboard Artist) is sketching frames…',
  'Kai (Video Generator) is producing the final cut…',
];

// Demo fallback images for hackathon (place files at /static/demo/storyboard/1.jpg ... 6.jpg)
const DEMO_STORYBOARD_IMAGES = [
  '/static/demo/storyboard/1.jpg',
  '/static/demo/storyboard/2.jpg',
  '/static/demo/storyboard/3.jpg',
  '/static/demo/storyboard/4.jpg',
  '/static/demo/storyboard/5.jpg',
  '/static/demo/storyboard/6.jpg',
];

let currentPage = 0;
let selectedIdeaIndex = 0;

// Central state
const appState = {
  url: '',
  brand: {
    domain: '',
    name: '',
    mission: '',
    values: [],
    logoUrl: '',
    typography: '',
    colors: [],
    product: '',
    tone: '',
    tagline: '',
  },
  concepts: [],
  selectedConceptIndex: 0,
  script: null,
  storyboard: [],
};

// --------------- API helper ---------------
async function apiPost(path, body) {
  const resp = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });
  if (!resp.ok) throw new Error(`Request failed: ${resp.status}`);
  return await resp.json();
}

// --------------- Brand (Page 1) ---------------
function decodeHtmlEntities(str) {
  if (!str) return '';
  const el = document.createElement('textarea');
  el.innerHTML = str;
  return el.value;
}

function pickBrandName(info, fallbackDomain) {
  const clean = (s) => decodeHtmlEntities(String(s || '').trim());
  // 1) Prefer API-provided name if looks like a brand
  let apiName = clean(info?.name || '');
  if (apiName) {
    // If apiName looks like a composite title, split and choose likely brand part
    const separators = ['|', '—', '-', '–', '·', '\\'];
    for (const sep of separators) {
      if (apiName.includes(sep)) {
        const parts = apiName.split(sep).map(p => p.trim()).filter(Boolean);
        const candidates = parts.filter(p => !/^home$/i.test(p) && !/^welcome$/i.test(p));
        // Prefer parts with 2+ words or containing the domain root
        const domainRoot = String(fallbackDomain || '').replace(/^www\./, '').split('.')[0];
        const scored = candidates.map(p => ({
          p,
          score: (p.split(/\s+/).length >= 2 ? 2 : 0) + (domainRoot && p.toLowerCase().includes(domainRoot.toLowerCase()) ? 3 : 0) + (/^[A-Z]/.test(p) ? 1 : 0)
        }));
        scored.sort((a, b) => b.score - a.score);
        if (scored.length && scored[0].score > 0) {
          apiName = scored[0].p;
        } else if (candidates.length) {
          apiName = candidates[candidates.length - 1];
        }
        break;
      }
    }
    if (apiName && !/^home\b/i.test(apiName)) return apiName;
  }

  // 2) Try page title parts (common formats: "Tagline | Brand", "Brand — Home")
  const title = clean(info?.pageTitle || '');
  if (title) {
    const separators = ['|', '—', '-', '–', '·'];
    let parts = [title];
    for (const sep of separators) {
      if (title.includes(sep)) {
        parts = title.split(sep).map(p => p.trim()).filter(Boolean);
        break;
      }
    }
    // Heuristic: prefer the longest part that is not "Home"/"Welcome" and has capitalized words
    const domainRoot = String(fallbackDomain || '').replace(/^www\./, '').split('.')[0];
    const candidates = parts.filter(p => !/^home$/i.test(p) && !/^welcome$/i.test(p));
    const scored = candidates.map(p => ({
      p,
      score: (p.split(/\s+/).length >= 2 ? 2 : 0) + (domainRoot && p.toLowerCase().includes(domainRoot.toLowerCase()) ? 3 : 0) + (/^[A-Z]/.test(p) ? 1 : 0)
    }));
    scored.sort((a, b) => b.score - a.score);
    if (scored.length) return scored[0].p;
  }

  // 3) Fallback to domain root word
  const domain = String(fallbackDomain || '').replace(/^www\./, '').split('.')[0];
  return domain ? domain.charAt(0).toUpperCase() + domain.slice(1) : '';
}

function extractPalette(info) {
  const out = [];
  const pushHex = (h) => {
    if (!h) return;
    const hex = String(h).trim();
    if (/^#?[0-9a-fA-F]{6}$/.test(hex.replace('#', ''))) {
      const withHash = hex.startsWith('#') ? hex : `#${hex}`;
      if (!out.includes(withHash)) out.push(withHash);
    }
  };
  const colors = Array.isArray(info?.colors) ? info.colors : [];
  colors.forEach(c => {
    if (c && typeof c === 'object') {
      pushHex(c.hex || c.value || c.color);
    } else if (typeof c === 'string') {
      pushHex(c);
    }
  });
  return out.slice(0, 6);
}

function pickLogoUrl(info) {
  const logos = Array.isArray(info?.logos) ? info.logos : [];
  // Prefer type=logo, theme=light, png/webp, else svg
  const scored = [];
  logos.forEach(item => {
    const type = (item?.type || '').toLowerCase();
    const theme = (item?.theme || '').toLowerCase();
    const formats = Array.isArray(item?.formats) ? item.formats : [];
    formats.forEach(f => {
      const fmt = (f?.format || '').toLowerCase();
      const src = f?.src;
      if (!src) return;
      let score = 0;
      if (type === 'logo') score += 3; else if (type === 'symbol') score += 1;
      if (theme === 'light') score += 2; else if (theme === 'dark') score += 1;
      if (fmt === 'png' || fmt === 'webp') score += 2; else if (fmt === 'svg') score += 1;
      scored.push({ src, score });
    });
  });
  scored.sort((a, b) => b.score - a.score);
  return scored[0]?.src || '';
}

function firstSentence(text) {
  const s = String(text || '').split(/(?<=[\.\!\?])\s+/)[0] || '';
  return s.trim();
}

function deriveToneFromText(text) {
  const t = (text || '').toLowerCase();
  const picks = [];
  const candidates = [
    { key: 'trust', label: 'trustworthy' },
    { key: 'safety', label: 'safety-first' },
    { key: 'innov', label: 'innovative' },
    { key: 'ambit', label: 'ambitious' },
    { key: 'collab', label: 'collaborative' },
    { key: 'transparen', label: 'transparent' },
    { key: 'support', label: 'supportive' },
    { key: 'human', label: 'human-centered' },
  ];
  candidates.forEach(c => { if (t.includes(c.key)) picks.push(c.label); });
  return picks.length ? picks.slice(0, 3).join(', ') : 'thoughtful, collaborative, empowering';
}

function deriveBrandFromCompanyInfo(info, fallbackDomain) {
  const derived = {
    name: pickBrandName(info, fallbackDomain),
    mission: info?.description || info?.metaDescription || '',
    values: [],
    logoUrl: '',
    typography: (info?.fonts && info.fonts[0]?.name) || 'Inter',
    colors: extractPalette(info),
    product: '',
    tone: '',
    tagline: '',
  };

  derived.logoUrl = pickLogoUrl(info);

  // Heuristic values from longDescription/description
  const text = (info?.longDescription || info?.description || info?.metaDescription || '').toLowerCase();
  const candidates = [
    { key: 'safety', label: 'Safety-first' },
    { key: 'reliable', label: 'Reliable' },
    { key: 'interpretable', label: 'Interpretable' },
    { key: 'steerable', label: 'Steerable' },
    { key: 'transparent', label: 'Transparency' },
    { key: 'collaborat', label: 'Collaborative' },
    { key: 'research', label: 'Research-driven' },
    { key: 'human', label: 'Human-centered' },
  ];
  const values = [];
  for (const c of candidates) {
    if (text.includes(c.key)) values.push(c.label);
    if (values.length >= 6) break;
  }
  derived.values = values.length ? values : ['Trusted', 'Innovative', 'Customer-focused'];

  // Product: first sentence of metaDescription/description
  const productSource = info?.metaDescription || info?.description || '';
  derived.product = firstSentence(productSource);

  // Tagline: use pageTitle if distinct from brand name and short
  const pageTitle = decodeHtmlEntities(info?.pageTitle || '');
  const nameDecoded = decodeHtmlEntities(derived.name);
  if (pageTitle && pageTitle.toLowerCase() !== nameDecoded.toLowerCase() && pageTitle.length <= 60) {
    derived.tagline = pageTitle;
  }

  // Tone: extract from long description
  derived.tone = deriveToneFromText(info?.longDescription || info?.description || info?.metaDescription || '');

  return derived;
}

function renderBrandFromState() {
  const missionEl = document.getElementById('brandMission');
  const valuesList = document.getElementById('brandValues');
  const diffList = document.getElementById('pointsDifference');
  const paletteContainer = document.getElementById('colorPalette');

  const productEl = document.getElementById('brandProduct');

  const nameEl = document.getElementById('brandName');
  const logoEl = document.getElementById('brandLogo');
  const typoEl = document.getElementById('brandTypography');
  const toneEl = document.getElementById('brandTone');
  const taglineEl = document.getElementById('brandTagline');

  if (missionEl) missionEl.textContent = appState.brand.mission || '';
  if (productEl) productEl.textContent = appState.brand.product || '';

  if (valuesList) {
    valuesList.innerHTML = '';
    (appState.brand.values || []).forEach((value) => {
    const li = document.createElement('li');
    li.textContent = value;
    valuesList.appendChild(li);
  });
  }

  if (diffList) {
    diffList.innerHTML = '';
  }

  if (paletteContainer) {
    paletteContainer.innerHTML = '';
    (appState.brand.colors || []).forEach((color) => {
    const swatch = document.createElement('div');
    swatch.className = 'color-swatch';
    swatch.style.background = color;
    paletteContainer.appendChild(swatch);
  });
}

  if (nameEl) nameEl.textContent = decodeHtmlEntities(appState.brand.name) || '';
  if (typoEl) typoEl.textContent = appState.brand.typography || 'Inter';
  if (logoEl) logoEl.innerHTML = appState.brand.logoUrl
    ? `<img src="${appState.brand.logoUrl}" alt="${appState.brand.name} logo" style="max-width:100%;height:auto" />`
    : 'Logo';
  if (toneEl) toneEl.textContent = appState.brand.tone || toneEl.textContent || '';
  if (taglineEl) taglineEl.textContent = appState.brand.tagline || taglineEl.textContent || '';
}

async function loadAndRenderBrandStrategy() {
  try {
    const res = await apiPost('/api/brand-strategy', {});
    const text = (res && res.strategy) || '';
    const clean = String(text).replace(/\r/g, '');
    // Split on numbered points (1. 2. 3.)
    const parts = clean.split(/\n?\s*\d+\.\s*/).filter(Boolean);
    const [coreRaw, diffRaw, audienceRaw] = [parts[0] || '', parts[1] || '', parts[2] || ''];
    const stripLabel = (s) => s.replace(/^\s*Brand Core\s*:\s*/i, '')
                               .replace(/^\s*Brand Positioning \(Key Differentiator\)\s*:\s*/i, '')
                               .replace(/^\s*Brand Positioning \(Target Audience\)\s*:\s*/i, '')
                               .trim();
    const core = stripLabel(coreRaw);
    const diff = stripLabel(diffRaw);
    const audience = stripLabel(audienceRaw);

    const missionEl = document.getElementById('brandMission');
    const diffList = document.getElementById('pointsDifference');
    const audienceEl = document.getElementById('targetAudience');
    const promiseEl = document.getElementById('brandPromise');

    if (missionEl && core) missionEl.textContent = core;
    if (audienceEl && audience) audienceEl.textContent = audience;
    if (diffList && diff) {
      diffList.innerHTML = '';
      const li = document.createElement('li');
      li.textContent = diff;
      diffList.appendChild(li);
    }

    // Brand promise: prefer tagline, else differentiator, else core
    if (promiseEl && !promiseEl.textContent.trim()) {
      const bp = appState.brand.tagline || diff || core;
      if (bp) promiseEl.textContent = bp;
    }

    // If no values yet, derive naive values from core sentence
    if ((appState.brand.values || []).length === 0 && core) {
      const tokens = core.split(/[,.;]/).map(t => t.trim()).filter(Boolean).slice(0, 4);
      appState.brand.values = tokens;
      const valuesList = document.getElementById('brandValues');
      if (valuesList) {
        valuesList.innerHTML = '';
        appState.brand.values.forEach(v => {
          const li = document.createElement('li');
          li.textContent = v;
          valuesList.appendChild(li);
        });
      }
    }
  } catch (e) {
    console.error('Brand strategy load failed', e);
  }
}

// --------------- Creative (Page 2) ---------------
function parseConceptTextToIdea(text) {
  const titleMatch = text.match(/Idea\s*(\d+)/i);
  const title = titleMatch ? `Idea ${titleMatch[1]}` : 'Idea';
  const getBlock = (label) => {
    const regex = new RegExp(label + '\\s*\\n([\\s\\S]*?)(?=\\n[A-Z][A-Za-z ]+\\n|$)', 'i');
    const m = text.match(regex);
    return m ? m[1].trim() : '';
  };
  const storyline = getBlock('Storyline');
  const charactersBlock = getBlock('Characters');
  const location = getBlock('Location');
  const characters = charactersBlock
    .split(/\n+/)
    .map((l) => l.replace(/^\d+\.\s*/, '').replace(/^[-–]\s*/, '').trim())
    .filter(Boolean);
  return { title, storyline, characters, location, raw: text };
}

function renderIdeasFromState() {
  ideasGrid.innerHTML = '';
  appState.concepts.forEach((idea, index) => {
    const card = document.createElement('article');
    card.className = 'idea-card';
    if (index === selectedIdeaIndex) card.classList.add('active');
    card.dataset.index = index;
    card.innerHTML = `
      <h3>${idea.title}</h3>
      <p><strong>Storyline:</strong> ${idea.storyline}</p>
      <p><strong>Characters:</strong><br>${idea.characters.join('<br>')}</p>
      <p><strong>Location:</strong> ${idea.location}</p>
      <div style="display:flex;gap:8px;margin-top:8px;">
        <button class="accent" data-action="select">Use this idea</button>
        <button class="secondary" data-action="edit">Edit</button>
      </div>
    `;
    card.addEventListener('click', (e) => {
      const action = (e.target && e.target.getAttribute('data-action')) || '';
      if (action === 'select') {
        selectedIdeaIndex = index;
        markActiveIdea();
      } else if (action === 'edit') {
        openIdeaModal(index);
      }
    });
    ideasGrid.appendChild(card);
  });
}

function openIdeaModal(index) {
  selectedIdeaIndex = index;
  const idea = appState.concepts[index];
  modalStoryline.value = idea.storyline || '';
  modalCharacters.value = (idea.characters || []).join('\n');
  modalLocation.value = idea.location || '';
  ideaModal.classList.add('open');
  ideaModal.setAttribute('aria-hidden', 'false');
  markActiveIdea();
}

function closeIdeaModal() {
  ideaModal.classList.remove('open');
  ideaModal.setAttribute('aria-hidden', 'true');
}

function markActiveIdea() {
  document.querySelectorAll('.idea-card').forEach((card) => {
    card.classList.toggle(
      'active',
      Number(card.dataset.index) === Number(selectedIdeaIndex),
    );
  });
}

function openRegenerateModal() {
  regenerateModal.classList.add('open');
  regenerateModal.setAttribute('aria-hidden', 'false');
  document.getElementById('feedbackInput').focus();
}

function closeRegenerateModal() {
  regenerateModal.classList.remove('open');
  regenerateModal.setAttribute('aria-hidden', 'true');
  regenerateForm.reset();
}

// --------------- Script (Page 3) ---------------
function renderScriptFromState() {
  if (!scriptView) return;
  scriptView.innerHTML = '';
  const scenes = (appState.script && appState.script.script) || [];
  if (!Array.isArray(scenes) || scenes.length === 0) {
    scriptView.innerHTML = '<p>No script generated yet.</p>';
    return;
  }
  const container = document.createElement('div');
  scenes.forEach((scene) => {
    const block = document.createElement('article');
    block.className = 'scene-block';
    const num = scene.scene_number ?? '';
    const start = scene.timestamp_start ?? '';
    const end = scene.timestamp_end ?? '';
    const timing = start && end ? `${start} - ${end}` : start || '';
    block.innerHTML = `
      <header class="scene-header">
        <span class="scene-number">Scene ${num}</span>
        <span class="scene-time">${timing}</span>
      </header>
      <div class="scene-meta">
        <div><strong>Setting:</strong> ${scene.setting || ''}</div>
        <div><strong>Visual:</strong> ${scene.visual_description || ''}</div>
        <div><strong>Text on screen:</strong> ${scene.text_on_screen || ''}</div>
        <div><strong>Audio/Mood:</strong> ${scene.audio_cue || ''}</div>
      </div>
    `;
    container.appendChild(block);
  });
  scriptView.appendChild(container);
}

// --------------- Storyboard (Page 4) ---------------
function renderStoryboardFromState() {
  storyboardGrid.innerHTML = '';
  (appState.storyboard || []).forEach((scene, idx) => {
    const card = document.createElement('article');
    card.className = 'shot-card';
    const time = scene.timestamp || `Scene ${scene.scene_number}`;
    const description = scene.visual_description || scene.image_prompt || '';
    const prompt = scene.image_prompt || '';
    const demoSrc = DEMO_STORYBOARD_IMAGES[idx] || '';
    const imageSrc = scene.image_url || demoSrc || 'https://images.unsplash.com/photo-1523475472560-d2df97ec485c?auto=format&fit=crop&w=1400&q=80';
    card.innerHTML = `
      <figure class="shot-media">
        <img src="${imageSrc}" alt="Storyboard shot ${time}" loading="lazy" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1523475472560-d2df97ec485c?auto=format&fit=crop&w=1400&q=80';" />
      </figure>
      <div class="shot-info">
        <span class="shot-time">${time}</span>
        <p class="shot-description">${description}</p>
        ${prompt ? `<p class="shot-description"><strong>Prompt for Scene ${scene.scene_number || (idx+1)}:</strong> ${prompt}</p>` : ''}
      </div>
    `;
    storyboardGrid.appendChild(card);
  });
}

// --------------- Navigation ---------------
function showLoading(nextIndex) {
  const message = loadingSteps[Math.min(nextIndex, loadingSteps.length - 1)];
  loadingMessage.textContent = message;
  loadingOverlay.classList.add('active');
}

function hideLoading() {
  loadingOverlay.classList.remove('active');
}

function updateProgressDots(index) {
  progressDots.forEach((dot, dotIndex) => {
    dot.classList.toggle('active', dotIndex === index);
  });
}

function navigateTo(index) {
  currentPage = index;
  slider.style.transform = `translateX(-${index * 100}vw)`;
  updateProgressDots(index);
}

async function preNextFlow(pageIndex) {
  switch (pageIndex) {
    case 0: {
      // Already handled on Start
      return;
    }
    case 1: {
      // Load creative concepts from backend
      const res = await apiPost('/api/creative-concepts', {});
      const concepts = (res.concepts || []).map((c) => parseConceptTextToIdea(c.content));
      appState.concepts = concepts;
      appState.selectedConceptIndex = 0;
      selectedIdeaIndex = 0;
      renderIdeasFromState();
      return;
    }
    case 2: {
      // Select concept and generate script
      const current = appState.concepts[selectedIdeaIndex] || appState.concepts[0];
      if (!current) return;
      await apiPost('/api/select-concept', { concept_id: selectedIdeaIndex + 1, content: current.raw });
      const res = await apiPost('/api/generate-script', {});
      appState.script = res.script || null;
      renderScriptFromState();
      return;
    }
    case 3: {
      // Persist current script (no JSON editing) and generate storyboard
      if (appState.script) {
        await apiPost('/api/update-script', { script: appState.script });
      }
      const res = await apiPost('/api/generate-storyboard', {});
      let board = res && Array.isArray(res.storyboard) ? res.storyboard : [];
      if (!board.length) {
        board = new Array(6).fill(null).map((_, i) => ({
          scene_number: i + 1,
          timestamp: '',
          setting: '',
          visual_description: '',
          text_on_screen: '',
          audio_cue: '',
          image_prompt: '',
          image_url: DEMO_STORYBOARD_IMAGES[i] || ''
        }));
      }
      appState.storyboard = board;
      renderStoryboardFromState();
      return;
    }
    case 4: {
      // Load demo video URL from backend and set it on the player
      const res = await apiPost('/api/generate-video', {});
      const videoUrl = res && res.video_url;
      const video = document.getElementById('finalVideo');
      if (video && videoUrl) {
        video.setAttribute('src', videoUrl);
        try { video.load(); } catch (e) {}
      }
      return;
    }
    default:
      return;
  }
}

function handleNavigation(direction) {
  const nextIndex = direction === 'next' ? currentPage + 1 : currentPage - 1;
  if (nextIndex < 0 || nextIndex > 5) return;

  showLoading(nextIndex);

  (async () => {
    try {
      if (direction === 'next') {
        await preNextFlow(currentPage);
      }
    navigateTo(nextIndex);
    } finally {
    hideLoading();
    }
  })();
}

// --------------- Event bindings ---------------
const navButtons = [...document.querySelectorAll('[data-nav]')];
navButtons.forEach((btn) => {
  btn.addEventListener('click', () => handleNavigation(btn.dataset.nav));
});

// Click brand mark to return home (page 0)
const brandMark = document.querySelector('.brand-mark');
if (brandMark) {
  brandMark.addEventListener('click', (e) => {
    e.preventDefault();
    navigateTo(0);
  });
}

startBtn.addEventListener('click', async () => {
  const url = websiteInput.value.trim();
  if (!url) {
    websiteInput.focus();
    return;
  }
  startBtn.disabled = true;
  showLoading(1);
  try {
    appState.url = url;
    // Kick off backend; returns company_info
    const analyzed = await apiPost('/api/analyze-url', { url });
    const info = analyzed.company_info || {};
    appState.brand.domain = analyzed.domain || '';
    appState.brand = deriveBrandFromCompanyInfo(info, analyzed.domain);
    renderBrandFromState();
    await loadAndRenderBrandStrategy();
    navigateTo(1);
  } catch (e) {
    console.error(e);
  } finally {
    hideLoading();
    startBtn.disabled = false;
  }
});

websiteInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    startBtn.click();
  }
});

restartBtn.addEventListener('click', () => {
  navigateTo(0);
});

document
  .getElementById('closeIdeaModal')
  .addEventListener('click', closeIdeaModal);
document
  .getElementById('cancelIdeaEdit')
  .addEventListener('click', closeIdeaModal);

document
  .getElementById('closeRegenerateModal')
  .addEventListener('click', closeRegenerateModal);
document
  .getElementById('cancelRegenerate')
  .addEventListener('click', closeRegenerateModal);

ideaForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const updatedIdea = appState.concepts[selectedIdeaIndex];
  updatedIdea.storyline = modalStoryline.value;
  updatedIdea.characters = modalCharacters.value.split('\n').map((c) => c.trim()).filter(Boolean);
  updatedIdea.location = modalLocation.value;
  closeIdeaModal();
  renderIdeasFromState();
});

document
  .getElementById('regenerateIdeasBtn')
  .addEventListener('click', openRegenerateModal);

regenerateForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const feedback = document.getElementById('feedbackInput').value || '';
    const res = await apiPost('/api/regenerate-concepts', { feedback });
    const concepts = (res.concepts || []).map((c) => parseConceptTextToIdea(c.content));
    appState.concepts = concepts;
    appState.selectedConceptIndex = 0;
  selectedIdeaIndex = 0;
  closeRegenerateModal();
  renderIdeasFromState();
  } catch (e) {
    console.error(e);
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    if (ideaModal.classList.contains('open')) closeIdeaModal();
    if (regenerateModal.classList.contains('open')) closeRegenerateModal();
  }
});

function init() {
  // Initial render for empty state; real data comes after URL submit
  renderBrandFromState();
}

init();


