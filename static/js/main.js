// ============================================================
// Work cards — click anywhere (except the link) to open the project
// ============================================================
document.querySelectorAll('.work__card').forEach(card => {
  card.addEventListener('click', (e) => {
    if (e.target.tagName !== 'A') {
      window.open(card.dataset.link, '_blank');
    }
  });
});

// ============================================================
// Skill bars — fill in when scrolled into view
// ============================================================
const barObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      barObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.4 });
document.querySelectorAll('.skill-row__track').forEach(el => barObserver.observe(el));

// ============================================================
// Sticky nav — highlight the section currently in view
// ============================================================
const navLinks = document.querySelectorAll('#navLinks a');
const sections = document.querySelectorAll('main section[id]');
const spyObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(a => a.classList.remove('active'));
      const active = document.querySelector(`#navLinks a[href="#${entry.target.id}"]`);
      if (active) active.classList.add('active');
    }
  });
}, { rootMargin: '-40% 0px -50% 0px', threshold: 0 });
sections.forEach(s => spyObserver.observe(s));

// ============================================================
// Fade sections in on scroll
// ============================================================
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      fadeObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-in').forEach(el => fadeObserver.observe(el));

// ============================================================
// AI ASSISTANT — talks to the Flask backend at POST /api/chat.
// The matching logic itself lives in Python (see app.py).
// ============================================================
const aiFab = document.getElementById('aiFab');
const aiPanel = document.getElementById('aiPanel');
const aiClose = document.getElementById('aiClose');
const aiBody = document.getElementById('aiBody');
const aiForm = document.getElementById('aiForm');
const aiInput = document.getElementById('aiInput');
const aiChips = document.getElementById('aiChips');

function addMessage(text, sender) {
  const msg = document.createElement('div');
  msg.className = 'ai-msg ' + sender;
  msg.innerHTML = '<div class="ai-msg__bubble"></div>';
  msg.querySelector('.ai-msg__bubble').textContent = text;
  aiBody.appendChild(msg);
  aiBody.scrollTop = aiBody.scrollHeight;
}

function showTyping() {
  const t = document.createElement('div');
  t.className = 'ai-msg bot';
  t.id = 'aiTyping';
  t.innerHTML = '<div class="ai-typing"><span></span><span></span><span></span></div>';
  aiBody.appendChild(t);
  aiBody.scrollTop = aiBody.scrollHeight;
}

async function respond(text) {
  addMessage(text, 'user');
  showTyping();
  let result;
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    result = await res.json();
  } catch (err) {
    result = { answer: "Couldn't reach the server — make sure the Flask app is running." };
  }
  const t = document.getElementById('aiTyping');
  if (t) t.remove();
  addMessage(result.answer, 'bot');
  if (result.scrollTo) {
    setTimeout(() => {
      document.querySelector(result.scrollTo)?.scrollIntoView({ behavior: 'smooth' });
    }, 400);
  }
}

const CHIPS = ['Skills', 'Projects', 'Resume', 'Contact'];
aiChips.innerHTML = CHIPS.map(c => `<button class="ai-chip">${c}</button>`).join('');
aiChips.querySelectorAll('.ai-chip').forEach(chip => {
  chip.addEventListener('click', () => respond(chip.textContent));
});

aiFab.addEventListener('click', () => {
  aiFab.classList.add('is-open');
  aiPanel.classList.add('is-open');
  if (!aiBody.hasChildNodes()) {
    setTimeout(() => addMessage(
      "Hi, I'm an AI assistant trained on this portfolio. Ask me anything — skills, projects, resume, or contact info.",
      'bot'
    ), 300);
  }
  aiInput.focus();
});

aiClose.addEventListener('click', () => {
  aiFab.classList.remove('is-open');
  aiPanel.classList.remove('is-open');
});

aiForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const val = aiInput.value.trim();
  if (!val) return;
  respond(val);
  aiInput.value = '';
});
