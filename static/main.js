/* main.js — Online Voting System client-side interactions */

/* ── Role Tab Switching (login page) ────────────────────────────── */
(function () {
  const tabs     = document.querySelectorAll('.role-tab');
  const roleInp  = document.getElementById('role-input');
  if (!tabs.length) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      if (roleInp) roleInp.value = tab.dataset.role;
    });
  });
})();


/* ── Candidate Card Selection (vote page) ───────────────────────── */
(function () {
  const cards = document.querySelectorAll('.cand-card');
  if (!cards.length) return;

  cards.forEach(card => {
    card.addEventListener('click', () => {
      cards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });
})();


/* ── Vote Confirm Modal ──────────────────────────────────────────── */
(function () {
  const confirmBtn  = document.getElementById('confirm-btn');
  const cancelBtn   = document.getElementById('cancel-btn');
  const submitBtn   = document.getElementById('submit-btn');
  const modal       = document.getElementById('vote-modal');
  const pickedName  = document.getElementById('picked-name');
  const voteForm    = document.getElementById('vote-form');

  if (!confirmBtn || !modal) return;

  confirmBtn.addEventListener('click', () => {
    const sel = document.querySelector('.cand-card.selected');
    if (!sel) {
      flash('Please select a candidate first.', 'warning');
      return;
    }
    if (pickedName) {
      pickedName.textContent = sel.querySelector('.cand-name').textContent;
    }
    modal.classList.add('open');
  });

  cancelBtn && cancelBtn.addEventListener('click', () => modal.classList.remove('open'));
  submitBtn && submitBtn.addEventListener('click', () => voteForm && voteForm.submit());
  modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open'); });
})();


/* ── Auto-dismiss flash messages ────────────────────────────────── */
(function () {
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(el => {
      el.style.transition = 'opacity 0.3s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 300);
    });
  }, 4000);
})();


/* ── Result bar animation ───────────────────────────────────────── */
(function () {
  const bars = document.querySelectorAll('.result-fill');
  if (!bars.length) return;
  window.addEventListener('load', () => {
    bars.forEach(bar => {
      const w = bar.dataset.width || '0';
      setTimeout(() => { bar.style.width = w + '%'; }, 150);
    });
  });
})();


/* ── Active nav link ────────────────────────────────────────────── */
(function () {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(a => {
    if (a.getAttribute('href') && path.startsWith(a.getAttribute('href'))) {
      a.classList.add('active');
    }
  });
})();


/* ── Programmatic flash helper ──────────────────────────────────── */
function flash(msg, type) {
  type = type || 'info';
  const container = document.querySelector('.flashes') || document.body;
  const div = document.createElement('div');
  div.className = `flash flash-${type}`;
  div.textContent = msg;
  container.prepend(div);
  setTimeout(() => {
    div.style.transition = 'opacity 0.3s';
    div.style.opacity = '0';
    setTimeout(() => div.remove(), 300);
  }, 3500);
}
