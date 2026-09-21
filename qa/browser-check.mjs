/** Browser verification for a normal CI runner. Never run this to work around
 * local environment policy: the constrained Work runtime cannot open sockets.
 * All pages are served from the checked-out branch and an immutable baseline.
 */
import { chromium } from 'playwright';
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import { createServer } from 'node:http';
import { readFile, stat, mkdir, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const baseline = process.env.ECASH_QA_BASELINE;
if (!baseline) throw new Error('ECASH_QA_BASELINE must identify the immutable baseline checkout');
const out = path.join(root, 'docs/qa/ci');
await mkdir(out, {recursive: true});
const catalog = JSON.parse(await readFile(path.join(root, 'editorial/catalog.json'), 'utf8'));
const searchIndex = JSON.parse(await readFile(path.join(root, 'assets/data/search.json'), 'utf8'));
const axeSource = await readFile(require.resolve('axe-core/axe.min.js'), 'utf8');
const article = '/reportajes/tonalli-memo-alias-xec-identidad-agentes-humanos.html';
const origins = {before: 'http://127.0.0.1:8765', after: 'http://127.0.0.1:8766'};
const checks = [], diagnostics = [], axeReports = [], lighthouseReports = [];
const widths = [320, 390, 768, 1440, 1920];
let browser;
const servers = [];
const summary = {method: 'GitHub Actions runner; local HTTP + Chromium, axe and Lighthouse', commit: process.env.GITHUB_SHA || null, baselineRevision: '7b5cc72c05ee9deb74f26ff85edd209ee2d9b511', createdAt: new Date().toISOString(), lighthouseCaveat: 'Single-run simulated mobile lab measurements. Both copies use the same uncompressed local HTTP server; original third-party resources retain their network behavior. These are not production field Core Web Vitals.', checks, diagnostics, axe: axeReports, lighthouse: lighthouseReports};
const save = (name, value) => writeFile(path.join(out, name), typeof value === 'string' ? value : JSON.stringify(value, null, 2) + '\n');
function check(name, passed, detail) {
  checks.push({name, passed: Boolean(passed), ...(detail === undefined ? {} : {detail})});
  console.log(`${passed ? 'PASS' : 'FAIL'} ${name}${detail === undefined ? '' : ' ' + JSON.stringify(detail)}`);
}
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.xml':'application/xml; charset=utf-8','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.svg':'image/svg+xml','.ico':'image/x-icon','.woff2':'font/woff2','.txt':'text/plain; charset=utf-8'};
async function serve(directory, port) {
  const base = path.resolve(directory);
  const server = createServer(async (req, res) => {
    try {
      if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405); res.end(); return; }
      const url = new URL(req.url, 'http://127.0.0.1');
      let target = path.resolve(base, '.' + decodeURIComponent(url.pathname));
      if (target !== base && !target.startsWith(base + path.sep)) { res.writeHead(403); res.end(); return; }
      if ((await stat(target)).isDirectory()) target = path.join(target, 'index.html');
      const data = await readFile(target);
      res.writeHead(200, {'Content-Type': mime[path.extname(target)] || 'application/octet-stream', 'Cache-Control':'no-cache', 'Content-Length':data.length});
      res.end(req.method === 'HEAD' ? undefined : data);
    } catch { res.writeHead(404, {'Content-Type':'text/plain'}); res.end('Not found'); }
  });
  await new Promise((resolve, reject) => {server.once('error', reject); server.listen(port, '127.0.0.1', resolve);});
  servers.push(server);
}
function observe(page, label, {expectedFailure = false} = {}) {
  const record = {page: label, ownErrors: [], externalErrors: [], navigationAborts: [], expectedFailure};
  diagnostics.push(record);
  const add = (type, message, url = '') => {
    const entry = {type, message, url};
    // A new navigation can intentionally cancel an unfinished image/embed request.
    // Keep this evidence separate from resource failures in a settled document.
    if (message.includes('net::ERR_ABORTED')) { record.navigationAborts.push(entry); return; }
    if (!url || url.includes(origins.after) || url.includes(origins.before)) record.ownErrors.push(entry);
    else record.externalErrors.push(entry);
  };
  page.on('pageerror', error => {
    const stack = error.stack || '';
    const url = stack.match(/https?:\/\/[^\s)]+/)?.[0] || '';
    add('pageerror', String(error), url);
  });
  page.on('console', message => { if (message.type() === 'error') add('console', message.text(), message.location().url || ''); });
  page.on('requestfailed', request => add('requestfailed', request.failure()?.errorText || 'request failed', request.url()));
  page.on('response', response => {if (response.status() >= 400) add('http', String(response.status()), response.url());});
  return record;
}
async function open(page, origin, route) {
  const response = await page.goto(origin + route, {waitUntil: 'domcontentloaded', timeout: 30000});
  if (!response || response.status() !== 200) throw new Error(`HTTP ${response?.status()} ${origin}${route}`);
  await page.evaluate(async () => {if (document.fonts) await Promise.race([document.fonts.ready, new Promise(resolve => setTimeout(resolve, 4000))]);});
  await page.waitForTimeout(100);
}
async function layout(page) {
  return page.evaluate(() => ({
    viewport: innerWidth,
    documentWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
    overflowing: [...document.querySelectorAll('body *')].filter(element => {
      const r = element.getBoundingClientRect();
      return r.width > 0 && r.right > innerWidth + 1 && getComputedStyle(element).position !== 'fixed';
    }).slice(0, 12).map(element => ({tag:element.tagName,id:element.id,class:element.className,right:Math.round(element.getBoundingClientRect().right)}))
  }));
}
async function screenshot(page, filename) {
  // Scroll naturally to load lazy editorial images before a full-page capture.
  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  const step = Math.max(600, page.viewportSize().height - 100);
  for (let y = 0; y < height; y += step) { await page.evaluate(y => scrollTo(0, y), y); await page.waitForTimeout(35); }
  await page.evaluate(() => scrollTo(0, 0));
  await page.waitForTimeout(300);
  await page.screenshot({path:path.join(out, filename),fullPage:true,animations:'disabled'});
}
async function auditAxe(page, label, gate) {
  await page.addScriptTag({content: axeSource});
  const result = await page.evaluate(async () => window.axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}}));
  await save(`axe-${label}.json`, result);
  axeReports.push({page:label, violations:result.violations.length, incomplete:result.incomplete.length, passes:result.passes.length, file:`axe-${label}.json`});
  if (gate) check(`axe WCAG ${label}`, result.violations.length === 0, result.violations.map(v => ({id:v.id,impact:v.impact,nodes:v.nodes.map(n => n.target)})));
}
try {
  await serve(baseline, 8765);
  await serve(root, 8766);
  browser = await chromium.launch({headless:true});
  summary.browserVersion = browser.version();
  summary.viewportWidths = widths;

  // Actual HTTP checks for the 45 historical routes.
  for (const route of ['/', '/blog/index.html', ...catalog.articles.map(a => a.url)]) {
    const response = await fetch(origins.after + route);
    check(`Historical HTTP ${route}`, response.status === 200, response.status);
  }

  for (const phase of ['before', 'after']) {
    for (const width of [1440, 390]) {
      const size = width === 1440 ? 'desktop' : 'mobile';
      const context = await browser.newContext({viewport:{width,height:width === 1440 ? 1000 : 844},deviceScaleFactor:1});
      const page = await context.newPage();
      observe(page, `${phase}-screenshots-${size}`);
      for (const [label, route] of [['home','/'],['article',article],['technical-article','/analisis/multifirma-tonalli-wallet-bovedas-p2sh-ecash.html']]) {
        await open(page, origins[phase], route);
        await screenshot(page, `${phase}-${label}-${size}.png`);
        if (width === 390) await auditAxe(page, `${phase}-${label}-390`, phase === 'after');
      }
      await context.close();
    }
  }

  const responsive = await browser.newContext();
  const page = await responsive.newPage();
  observe(page, 'after-responsive');
  for (const width of widths) {
    await page.setViewportSize({width,height:900});
    for (const [label, route] of [['home','/'],['article',article],['archive','/blog/index.html']]) {
      await open(page, origins.after, route);
      const result = await layout(page);
      check(`Responsive ${label} ${width}`, result.documentWidth <= width + 1, result);
    }
  }
  await page.setViewportSize({width:390,height:844});
  for (const entry of catalog.articles) {
    await open(page, origins.after, entry.url);
    const result = await layout(page);
    check(`Article overflow 390 ${entry.url}`, result.documentWidth <= 391, result);
  }
  for (const [label,route] of [['archive','/blog/index.html'],['search','/buscar/'],['p2sh','/analisis/multifirma-tonalli-wallet-bovedas-p2sh-ecash.html'],['teyolia','/analisis/teyolia-direct-to-pool.html']]) {
    await open(page, origins.after, route);
    await auditAxe(page, `after-${label}-390`, true);
  }
  await page.setViewportSize({width:1440,height:1000});
  await open(page, origins.after, '/');
  await auditAxe(page, 'after-home-1440', true);
  await open(page, origins.after, article);
  await auditAxe(page, 'after-article-1440', true);
  await responsive.close();

  const interactive = await browser.newContext({viewport:{width:390,height:844}});
  const ui = await interactive.newPage();
  observe(ui, 'after-keyboard-search');
  await open(ui, origins.after, '/');
  await ui.keyboard.press('Tab');
  check('Keyboard first focus is skip link', await ui.locator('.skip-link').evaluate(el => el === document.activeElement));
  const focus = await ui.locator('.skip-link').evaluate(el => ({outline:getComputedStyle(el).outlineStyle,width:getComputedStyle(el).outlineWidth,top:el.getBoundingClientRect().top}));
  check('Skip-link focus visible in rendered viewport', focus.outline !== 'none' && focus.width !== '0px' && focus.top >= 0, focus);
  await ui.keyboard.press('Enter');
  check('Skip link targets main content', await ui.evaluate(() => location.hash === '#contenido'));
  await ui.locator('.nav-toggle').focus();
  await ui.keyboard.press('Enter');
  const menuId = await ui.locator('.nav-toggle').getAttribute('aria-controls');
  check('Mobile menu keyboard activation', await ui.locator('.nav-toggle').getAttribute('aria-expanded') === 'true' && await ui.locator(`#${menuId}`).isVisible());
  await ui.keyboard.press('Tab');
  check('Keyboard can enter mobile navigation', await ui.evaluate(id => document.getElementById(id).contains(document.activeElement), menuId));
  await ui.keyboard.press('Escape');
  check('Escape closes menu and returns focus', await ui.locator('.nav-toggle').getAttribute('aria-expanded') === 'false' && await ui.locator('.nav-toggle').evaluate(el => el === document.activeElement));

  let indexRequests = 0;
  ui.on('request', request => {if (request.url().endsWith('/assets/data/search.json')) indexRequests += 1;});
  await open(ui, origins.after, '/buscar/');
  const countVisible = () => ui.locator('#search-results [data-article-url]:visible').count();
  check('Search starts with full catalogue and no index download', await countVisible() === catalog.articles.length && indexRequests === 0);
  await ui.locator('#filter-genre').selectOption({label:'Reportaje'});
  check('Genre filter uses static records without downloading index', await countVisible() > 0 && await countVisible() < catalog.articles.length && indexRequests === 0);
  await ui.locator('#filter-genre').selectOption('');
  await ui.locator('#search-input').fill('Avalanche');
  await ui.waitForFunction(() => !document.getElementById('results-count').textContent.includes('Buscando en el texto completo') && document.getElementById('results-count').textContent.includes('publicaci'));
  const avalancheCount = await countVisible();
  check('Full-text query returns results and downloads index once', avalancheCount > 0 && avalancheCount < catalog.articles.length && indexRequests === 1, avalancheCount);
  const normalized = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const metadataText = normalized(await ui.locator('#search-results [data-search]').evaluateAll(elements => elements.map(el => el.dataset.search).join(' ')));
  const word = searchIndex.articles.flatMap(a => normalized(a.searchText).match(/[a-z]{11,}/g) || []).find(token => !metadataText.includes(token));
  await ui.locator('#search-input').fill(word);
  await ui.waitForTimeout(100);
  check('Real browser full-text search finds body-only term', Boolean(word) && await countVisible() > 0, word);
  await ui.locator('#search-input').fill('aválanche');
  await ui.waitForFunction(expected => [...document.querySelectorAll('#search-results [data-article-url]')].filter(el => !el.hidden).length === expected, avalancheCount);
  check('Real browser search ignores accents and reuses index', await countVisible() === avalancheCount && indexRequests === 1);
  await ui.locator('#search-input').fill('not-a-real-article-84bad9421');
  await ui.locator('#search-empty').waitFor({state:'visible'});
  check('Real browser search displays empty state', await countVisible() === 0 && await ui.locator('#search-empty').isVisible());
  await ui.locator('button[type="reset"]').click();
  await ui.waitForFunction(() => document.getElementById('search-input').value === '' && !location.search.includes('q='));
  check('Search reset restores all articles', await countVisible() === catalog.articles.length);
  await interactive.close();

  const failureContext = await browser.newContext({viewport:{width:390,height:844}});
  const failurePage = await failureContext.newPage();
  observe(failurePage, 'expected-index-failure', {expectedFailure:true});
  await failurePage.route('**/assets/data/search.json', route => route.abort('failed'));
  await open(failurePage, origins.after, '/buscar/?q=Avalanche');
  await failurePage.waitForFunction(() => document.getElementById('results-count').textContent.includes('Búsqueda limitada'));
  check('Failed index load exposes fallback scope to reader', await failurePage.locator('#search-results [data-article-url]:visible').count() > 0);
  await failureContext.close();

  const nojs = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  const staticPage = await nojs.newPage();
  await staticPage.goto(origins.after + '/blog/index.html');
  check('Without JavaScript all catalogue articles remain available', await staticPage.locator('#search-results [data-article-url]:visible').count() === catalog.articles.length);
  check('Without JavaScript mobile navigation remains available', await staticPage.locator('.site-nav').isVisible());
  await nojs.close();

  for (const record of diagnostics.filter(d => d.page.startsWith('after-') && !d.expectedFailure)) {
    check(`Own assets and console ${record.page}`, record.ownErrors.length === 0, record.ownErrors);
  }

  await browser.close(); browser = undefined;
  // Comparable single-run lab measurements; not field Core Web Vitals.
  const chrome = await chromeLauncher.launch({chromePath:chromium.executablePath(),chromeFlags:['--headless','--no-sandbox','--disable-dev-shm-usage']});
  try {
    for (const phase of ['before','after']) {
      for (const [label,route] of [['home','/'],['article',article]]) {
        const result = await lighthouse(origins[phase]+route,{port:chrome.port,logLevel:'error',output:['json','html'],onlyCategories:['performance','accessibility','best-practices','seo']},{extends:'lighthouse:default',settings:{maxWaitForLoad:30000}});
        const stem = `lighthouse-${phase}-${label}-mobile`;
        await save(`${stem}.json`, result.report[0]);
        await save(`${stem}.html`, result.report[1]);
        const lhr = result.lhr;
        lighthouseReports.push({phase,page:label,formFactor:lhr.configSettings.formFactor,version:lhr.lighthouseVersion,score:Object.fromEntries(Object.entries(lhr.categories).map(([key,value])=>[key,value.score])),metrics:Object.fromEntries(['first-contentful-paint','largest-contentful-paint','speed-index','total-blocking-time','cumulative-layout-shift','total-byte-weight'].map(id=>[id,{value:lhr.audits[id]?.numericValue,unit:lhr.audits[id]?.numericUnit}])),runtimeError:lhr.runtimeError || null,report:`${stem}.html`});
        check(`Lighthouse completed ${phase} ${label}`, !lhr.runtimeError, lhr.runtimeError || null);
      }
    }
  } finally {await chrome.kill();}
} catch (error) {
  check('Browser runner completed without exception', false, {message:String(error),stack:error.stack});
} finally {
  if (browser) await browser.close();
  for (const server of servers) await new Promise(resolve => server.close(resolve));
  summary.passed = checks.every(c=>c.passed);
  summary.counts = {checks:checks.length,failed:checks.filter(c=>!c.passed).length,externalErrors:diagnostics.reduce((n,d)=>n+d.externalErrors.length,0)};
  await save('browser-summary.json', summary);
  console.log(JSON.stringify(summary.counts));
  if (!summary.passed) process.exitCode = 1;
}
