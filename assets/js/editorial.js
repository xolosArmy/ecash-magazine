/* Progressive enhancement only: the complete magazine remains readable without JS. */
(() => {
  'use strict';

  const form = document.getElementById('search-form');
  const results = document.getElementById('search-results');
  if (!form || !results) return;

  const controls = {
    q: document.getElementById('search-input'),
    genre: document.getElementById('filter-genre'),
    topic: document.getElementById('filter-topic'),
    author: document.getElementById('filter-author'),
    year: document.getElementById('filter-year')
  };
  const count = document.getElementById('results-count');
  const empty = document.getElementById('search-empty');
  const normalize = (value) => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim();
  const records = Array.from(results.querySelectorAll('[data-article-url]'), (element) => ({
    element,
    url: element.dataset.articleUrl,
    text: normalize(element.dataset.search || element.textContent),
    genre: normalize(element.dataset.genre),
    topics: normalize(element.dataset.topic || element.dataset.topics).split(/[\s|,]+/).filter(Boolean),
    author: normalize(element.dataset.author),
    year: normalize(element.dataset.year)
  }));
  const groups = Array.from(results.querySelectorAll('[data-archive-group]'));
  let indexState = 'idle';
  let indexPromise;
  let searchRevision = 0;

  function loadFullText() {
    if (indexPromise) return indexPromise;
    indexState = 'loading';
    indexPromise = fetch('/assets/data/search.json', {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' }
    }).then((response) => {
      if (!response.ok) throw new Error('Search index unavailable');
      return response.json();
    }).then((index) => {
      if (!index || !Array.isArray(index.articles)) throw new Error('Invalid search index');
      const fullText = new Map(index.articles
        .filter((entry) => entry && typeof entry.url === 'string' && typeof entry.searchText === 'string')
        .map((entry) => [entry.url, normalize(entry.searchText)]));
      if (records.some((record) => !fullText.has(record.url))) throw new Error('Incomplete search index');
      for (const record of records) record.text += ` ${fullText.get(record.url)}`;
      indexState = 'ready';
    }).catch(() => {
      // Metadata search and all filters remain available if the request fails.
      indexState = 'failed';
    });
    return indexPromise;
  }

  function readLocation() {
    const params = new URLSearchParams(window.location.search);
    for (const [name, control] of Object.entries(controls)) {
      if (!control) continue;
      const value = params.get(name) || '';
      if (control.tagName === 'SELECT') {
        const option = Array.from(control.options).find((entry) => normalize(entry.value) === normalize(value));
        control.value = option ? option.value : '';
      } else {
        control.value = value;
      }
    }
  }

  function renderResults(values) {
    const words = values.q.split(/\s+/).filter(Boolean);
    let visible = 0;

    for (const record of records) {
      const matches = words.every((word) => record.text.includes(word))
        && (!values.genre || record.genre === values.genre)
        && (!values.topic || record.topics.includes(values.topic))
        && (!values.author || record.author === values.author)
        && (!values.year || record.year === values.year);
      record.element.hidden = !matches;
      // A list item may wrap the card; avoid empty list markers and spacing.
      const listItem = record.element.parentElement;
      if (listItem && listItem.tagName === 'LI' && !listItem.hasAttribute('data-article-url')) listItem.hidden = !matches;
      if (matches) visible += 1;
    }

    for (const group of groups) {
      group.hidden = !records.some((record) => group.contains(record.element) && !record.element.hidden);
    }
    const loading = Boolean(values.q) && indexState === 'loading';
    const limited = Boolean(values.q) && indexState === 'failed';
    if (count) {
      count.textContent = `${visible} ${visible === 1 ? 'publicación' : 'publicaciones'} de ${records.length}`
        + (loading ? ' · Buscando en el texto completo…' : '')
        + (limited ? ' · Búsqueda limitada a títulos y ficha: no se pudo cargar el texto completo.' : '');
    }
    if (empty) empty.hidden = loading || visible !== 0;
  }

  function applyFilters(updateUrl) {
    const revision = ++searchRevision;
    const values = Object.fromEntries(Object.entries(controls).map(([key, control]) => [key, normalize(control && control.value)]));
    if (updateUrl) {
      const url = new URL(window.location.href);
      for (const [key, control] of Object.entries(controls)) {
        const value = control ? control.value.trim() : '';
        if (value) url.searchParams.set(key, value);
        else url.searchParams.delete(key);
      }
      // Preserve unrelated parameters and the fragment; avoid a request per keystroke.
      if (url.href !== window.location.href) window.history.replaceState(null, '', url);
    }
    if (values.q && (indexState === 'idle' || indexState === 'loading')) {
      const request = loadFullText();
      renderResults(values);
      request.then(() => {
        if (revision === searchRevision) renderResults(values);
      });
    } else {
      renderResults(values);
    }
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    applyFilters(true);
  });
  form.addEventListener('input', () => applyFilters(true));
  form.addEventListener('change', () => applyFilters(true));
  form.addEventListener('reset', () => {
    // Reset events precede the browser restoring each control's default value.
    window.setTimeout(() => {
      for (const control of Object.values(controls)) if (control) control.value = '';
      applyFilters(true);
    }, 0);
  });
  window.addEventListener('popstate', () => {
    readLocation();
    applyFilters(false);
  });

  readLocation();
  applyFilters(false);
})();
