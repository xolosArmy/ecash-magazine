/* DOM behavior checks. Requires jsdom as a QA-only dependency; no renderer.
 * NODE_PATH=/path/to/qa/node_modules node docs/qa/check-interactions.cjs
 * These checks do not certify visual layout, browser focus rendering or WCAG.
 */
'use strict';
const { JSDOM } = require('jsdom');
const { readFileSync, writeFileSync } = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const navigationCode = readFileSync(path.join(root, 'assets/js/navigation.js'), 'utf8');
const code = readFileSync(path.join(root, 'assets/js/editorial.js'), 'utf8');
const searchIndex = JSON.parse(readFileSync(path.join(root, 'assets/data/search.json'), 'utf8'));
const checks = [];
function check(name, success, detail) { checks.push({name, passed: Boolean(success), ...(detail === undefined ? {} : {detail})}); }
function create(page, query = '', mobile = true, network = {}) {
  const dom = new JSDOM(readFileSync(path.join(root, page), 'utf8'), {url: 'https://magazine.ecash.mx/' + page + query, runScripts: 'outside-only', pretendToBeVisual: true});
  const media = {matches: mobile, listener: null, addEventListener(type, listener) { this.listener = listener; }};
  dom.window.matchMedia = () => media;
  const state = {fetchCalls: 0, requested: [], resolve: null};
  dom.window.fetch = (url) => {
    state.fetchCalls += 1;
    state.requested.push(url);
    if (network.fail) return Promise.reject(new Error('QA simulated request failure'));
    if (network.deferred) return new Promise(resolve => {state.resolve = () => resolve({ok: true, json: async () => searchIndex});});
    return Promise.resolve({ok: true, json: async () => searchIndex});
  };
  dom.window.eval(navigationCode);
  dom.window.eval(code);
  return {dom, window: dom.window, doc: dom.window.document, media, state};
}
const settle = window => new Promise(resolve => window.setTimeout(resolve, 20));
async function main() {
  const home = create('index.html');
  const toggle = home.doc.querySelector('.nav-toggle');
  const menu = toggle && home.doc.getElementById(toggle.getAttribute('aria-controls'));
  check('Mobile navigation control and target exist', toggle && menu);
  if (toggle && menu) {
    check('Mobile navigation starts collapsed with explicit state', toggle.getAttribute('aria-expanded') === 'false' && menu.hidden);
    toggle.click();
    check('Menu opens when activated', toggle.getAttribute('aria-expanded') === 'true' && !menu.hidden);
    home.doc.dispatchEvent(new home.window.KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
    check('Escape closes navigation and returns focus to control', toggle.getAttribute('aria-expanded') === 'false' && menu.hidden && home.doc.activeElement === toggle);
    home.media.matches = false;
    home.media.listener();
    check('Desktop resize exposes navigation', !menu.hidden);
  }
  home.window.close();

  for (const page of ['blog/index.html', 'buscar/index.html']) {
    const {window, doc, state} = create(page);
    const form = doc.getElementById('search-form');
    const input = doc.getElementById('search-input');
    const count = doc.getElementById('results-count');
    const records = Array.from(doc.querySelectorAll('#search-results [data-article-url]'));
    const visible = () => records.filter(e => !e.hidden);
    check(`${page}: 43 searchable records`, records.length === 43, records.length);
    check(`${page}: all records initially visible`, visible().length === 43, visible().length);
    check(`${page}: labeled query input exists`, Boolean(form && input && (doc.querySelector('label[for="search-input"]') || input.getAttribute('aria-label'))));
    if (!form || !input) { window.close(); continue; }
    check(`${page}: initial archive avoids full-text index download`, state.fetchCalls === 0);
    const genre = doc.getElementById('filter-genre');
    genre.value = Array.from(genre.options).find(o => o.value).value;
    genre.dispatchEvent(new window.Event('change', {bubbles: true}));
    await settle(window);
    check(`${page}: genre filtering avoids index download`, state.fetchCalls === 0 && visible().length > 0);
    genre.value = '';
    genre.dispatchEvent(new window.Event('change', {bubbles: true}));
    async function query(value) {
      input.value = value;
      input.dispatchEvent(new window.Event('input', {bubbles: true}));
      await settle(window);
      return visible().length;
    }
    const avalanche = await query('Avalanche');
    check(`${page}: query narrows results`, avalanche > 0 && avalanche < 43, avalanche);
    check(`${page}: query fetches the generated same-origin index once`, state.fetchCalls === 1 && state.requested[0] === '/assets/data/search.json');
    check(`${page}: URL keeps query`, new URL(window.location.href).searchParams.get('q') === 'Avalanche');
    const accents = await query('aválanche');
    check(`${page}: accent-insensitive matching`, accents === avalanche, accents);
    await query('not-a-real-article-84bad9421');
    const empty = doc.getElementById('search-empty');
    check(`${page}: empty state visible for unmatched query`, visible().length === 0 && empty && !empty.hidden);
    check(`${page}: result status updates`, count && count.textContent.includes('0 publicaciones'));
    await query('');
    for (const key of ['genre', 'topic', 'author', 'year']) {
      const control = doc.getElementById(`filter-${key}`);
      if (!control) { check(`${page}: filter-${key} exists`, false); continue; }
      const option = Array.from(control.options).find(o => o.value);
      if (!option) { check(`${page}: filter-${key} has published options`, false); continue; }
      control.value = option.value;
      control.dispatchEvent(new window.Event('change', {bubbles: true}));
      await settle(window);
      const n = visible().length;
      check(`${page}: ${key} filter returns actual records`, n > 0 && n <= 43, {value: option.value, results: n});
      control.value = '';
      control.dispatchEvent(new window.Event('change', {bubbles: true}));
      await settle(window);
    }
    await query('Tonalli');
    form.reset();
    await settle(window);
    check(`${page}: reset restores entire archive`, visible().length === 43 && input.value === '', visible().length);
    check(`${page}: reset clears known filter parameters`, !new URL(window.location.href).searchParams.has('q'));
    window.history.pushState(null, '', '?q=Avalanche');
    window.dispatchEvent(new window.PopStateEvent('popstate'));
    await settle(window);
    check(`${page}: history navigation restores query and filtered state`, input.value === 'Avalanche' && visible().length === avalanche);
    check(`${page}: repeated queries reuse cached index`, state.fetchCalls === 1);
    const norm = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const metadataText = norm(records.map(e => e.dataset.search || e.textContent).join(' '));
    const bodyOnlyWord = searchIndex.articles.flatMap(a => norm(a.searchText).match(/[a-z]{11,}/g) || []).find(word => !metadataText.includes(word));
    const bodyCount = bodyOnlyWord ? await query(bodyOnlyWord) : 0;
    check(`${page}: full-text search finds a term absent from all card metadata`, Boolean(bodyOnlyWord) && bodyCount > 0, {term: bodyOnlyWord, results: bodyCount});
    window.close();
    const linked = create(page, '?q=Avalanche');
    await settle(linked.window);
    check(`${page}: search links initialize from URL`, linked.doc.getElementById('search-input').value === 'Avalanche' && Array.from(linked.doc.querySelectorAll('#search-results [data-article-url]')).filter(e => !e.hidden).length === avalanche);
    linked.window.close();
  }

  const failure = create('buscar/index.html', '?q=Avalanche', true, {fail: true});
  await settle(failure.window);
  const fallback = Array.from(failure.doc.querySelectorAll('#search-results [data-article-url]')).filter(e => !e.hidden);
  check('Index failure preserves title/metadata search', fallback.length > 0 && fallback.length < 43, fallback.length);
  check('Index failure announces scope limitation', failure.doc.getElementById('results-count').textContent.includes('Búsqueda limitada a títulos y ficha'));
  failure.window.close();

  const race = create('buscar/index.html', '?q=Avalanche', true, {deferred: true});
  const raceInput = race.doc.getElementById('search-input');
  raceInput.value = 'not-a-real-article-84bad9421';
  raceInput.dispatchEvent(new race.window.Event('input', {bubbles: true}));
  check('Concurrent queries share one pending index request', race.state.fetchCalls === 1);
  if (race.state.resolve) race.state.resolve();
  await settle(race.window);
  check('Late index response respects latest query', Array.from(race.doc.querySelectorAll('#search-results [data-article-url]')).filter(e => !e.hidden).length === 0 && raceInput.value === 'not-a-real-article-84bad9421');
  race.window.close();

  const clear = create('buscar/index.html', '?q=Avalanche', true, {deferred: true});
  const clearInput = clear.doc.getElementById('search-input');
  clearInput.value = '';
  clearInput.dispatchEvent(new clear.window.Event('input', {bubbles: true}));
  if (clear.state.resolve) clear.state.resolve();
  await settle(clear.window);
  check('Clearing while loading keeps all 43 articles visible after completion', Array.from(clear.doc.querySelectorAll('#search-results [data-article-url]')).filter(e => !e.hidden).length === 43 && clearInput.value === '');
  clear.window.close();

  const result = {method: 'jsdom 30.1.0 DOM behavior checks with generated search-index fetch fixture, no browser rendering or network', passed: checks.every(x=>x.passed), checks};
  writeFileSync(path.join(__dirname, 'interaction-dom.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({passed: result.passed, count: checks.length, failed: checks.filter(x=>!x.passed)},null,2));
  process.exitCode = result.passed ? 0 : 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
