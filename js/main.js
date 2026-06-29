/* =====================================================
   INSIGHT ACADEMIA — main.js
   Update CONFIG below with your actual details.
   ===================================================== */

const CONFIG = {
  // Your WhatsApp number — international format, no +, no spaces
  whatsapp: '918779528840',

  // Default pre-filled WhatsApp message
  whatsappMessage: 'Hello! I would like to get a quote for academic writing support.',

  // Create a free form at https://formspree.io — paste your endpoint here
  formspree: 'https://formspree.io/f/YOURFORMID',

  // Your contact email
  email: 'hello@insightacademia.org',
};

// -------------------------------------------------------
// Build WhatsApp links
// -------------------------------------------------------
function buildWhatsAppLinks() {
  const url = `https://wa.me/${CONFIG.whatsapp}?text=${encodeURIComponent(CONFIG.whatsappMessage)}`;
  document.querySelectorAll('.wa-link').forEach(el => {
    el.href = url;
  });
}

// -------------------------------------------------------
// Navigation: scroll shadow + active state
// -------------------------------------------------------
function initNav() {
  const nav = document.getElementById('nav');
  if (!nav) return;

  const onScroll = () => {
    nav.classList.toggle('scrolled', window.scrollY > 50);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll(); // run on load

  // Mark active link by pathname
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  nav.querySelectorAll('.nav__links a').forEach(link => {
    const href = new URL(link.href).pathname.replace(/\/$/, '') || '/';
    if (href === path) link.classList.add('active');
  });
}

// -------------------------------------------------------
// Mobile drawer
// -------------------------------------------------------
function initMobileMenu() {
  const toggle  = document.getElementById('navToggle');
  const drawer  = document.getElementById('navDrawer');
  const closeBtn = document.getElementById('drawerClose');
  if (!toggle || !drawer) return;

  toggle.addEventListener('click', () => drawer.classList.add('open'));
  closeBtn?.addEventListener('click', () => drawer.classList.remove('open'));

  // Close on backdrop click
  drawer.addEventListener('click', e => {
    if (e.target === drawer) drawer.classList.remove('open');
  });

  // Close on link click
  drawer.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => drawer.classList.remove('open'));
  });
}

// -------------------------------------------------------
// FAQ accordion
// -------------------------------------------------------
function initFAQ() {
  document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      item.classList.toggle('open');
    });
  });
}

// -------------------------------------------------------
// Contact form (Formspree AJAX)
// -------------------------------------------------------
function initContactForm() {
  const form = document.getElementById('contactForm');
  if (!form) return;

  const successMsg = document.getElementById('formSuccess');
  const submitBtn  = form.querySelector('[type="submit"]');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    submitBtn.disabled    = true;
    submitBtn.textContent = 'Sending…';

    try {
      const res = await fetch(CONFIG.formspree, {
        method:  'POST',
        body:    new FormData(form),
        headers: { Accept: 'application/json' },
      });

      if (res.ok) {
        form.reset();
        if (successMsg) successMsg.classList.add('visible');
        // Scroll success message into view
        successMsg?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        alert('Something went wrong. Please try WhatsApp or email instead.');
      }
    } catch {
      alert('Network error. Please try WhatsApp or email instead.');
    } finally {
      submitBtn.disabled    = false;
      submitBtn.textContent = 'Send message';
    }
  });
}

// -------------------------------------------------------
// Init
// -------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  buildWhatsAppLinks();
  initNav();
  initMobileMenu();
  initFAQ();
  initContactForm();
});
