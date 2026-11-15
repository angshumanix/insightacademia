/* Progressive enhancement: all navigation, product content and contact links work without JS. */
(() => {
  'use strict';
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#site-nav');
  const narrow = window.matchMedia('(max-width: 900px)');
  if (toggle && nav) {
    toggle.hidden = false;
    const setOpen = (open, restoreFocus = false) => {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.firstChild.textContent = open ? 'Close ' : 'Menu ';
      nav.hidden = narrow.matches && !open;
      if (restoreFocus) toggle.focus();
    };
    const sync = () => setOpen(!narrow.matches);
    sync();
    narrow.addEventListener('change', sync);
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    nav.addEventListener('click', e => {
      if (narrow.matches && e.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && narrow.matches && toggle.getAttribute('aria-expanded') === 'true') setOpen(false, true);
    });
    document.addEventListener('click', e => {
      if (narrow.matches && !e.target.closest('.site-header')) setOpen(false);
    });
  }
  const tools = document.querySelector('[data-catalogue-tools]');
  if (!tools) return;
  tools.hidden = false;
  const query = tools.querySelector('input');
  const category = tools.querySelector('select');
  const cards = [...document.querySelectorAll('[data-product]')];
  const count = document.querySelector('[data-result-count]');
  const empty = document.querySelector('[data-no-results]');
  const filter = () => {
    const term = query.value.trim().toLocaleLowerCase();
    let total = 0;
    cards.forEach(card => {
      const show = (!category.value || card.dataset.category === category.value) && card.textContent.toLocaleLowerCase().includes(term);
      card.hidden = !show;
      if (show) total += 1;
    });
    count.textContent = `${total} ${total === 1 ? 'demonstration' : 'demonstrations'} shown${tools.dataset.demo === 'true' ? ' · educational samples' : ''}`;
    empty.hidden = total !== 0;
  };
  query.addEventListener('input', filter);
  category.addEventListener('change', filter);
  tools.querySelector('button').addEventListener('click', () => {
    query.value = '';
    category.value = '';
    filter();
    query.focus();
  });
})();
