#!/usr/bin/env python3
"""Structural regression gate for the generated static magazine (Python + lxml).

Usage: python scripts/verify_site.py --baseline ../baseline-ecash \
    --report docs/qa/structural-after.json
Network requests and browser scores are deliberately outside this validator.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
import json
import re
import sys
from lxml import etree, html

BASE = 'https://magazine.ecash.mx/'
GENRES = {'Noticia', 'Entrevista', 'Crónica', 'Reportaje', 'Columna', 'Opinión',
          'Editorial', 'Reseña', 'Análisis técnico'}
SKIP = {'docs', 'content', 'qa', '.github', '.git', 'node_modules'}


def paths(root):
    return sorted(p for p in root.rglob('*.html') if not set(p.relative_to(root).parts) & SKIP)


def normalized(url, source='index.html'):
    parsed = urlparse(urljoin(BASE + source, url))
    path = unquote(parsed.path).lstrip('/')
    if not path or path.endswith('/'):
        path += 'index.html'
    return parsed, path


def schema_types(value):
    if isinstance(value, dict):
        kind = value.get('@type', [])
        yield from (kind if isinstance(kind, list) else [kind])
        for child in value.values():
            yield from schema_types(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_types(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--allow-missing-catalog', action='store_true', help='Baseline inventory only')
    args = parser.parse_args()
    root = args.root.resolve()
    files = paths(root)
    docs = {}
    failures, warnings, checks = [], [], []

    def check(name, ok, detail=None):
        checks.append({'check': name, 'passed': bool(ok), 'detail': detail})
        if not ok:
            failures.append({'check': name, 'detail': detail})

    for file in files:
        rel = file.relative_to(root).as_posix()
        source = file.read_text(encoding='utf-8')
        docs[rel] = (html.document_fromstring(source), source)
    historical = {p.relative_to(args.baseline).as_posix() for p in paths(args.baseline)} if args.baseline else set()
    if historical:
        check('45 historical documents in baseline', len(historical) == 45, len(historical))
        check('All historical URLs preserved', historical <= set(docs), sorted(historical - set(docs)))

    catalog_path = root / 'editorial/catalog.json'
    articles = []
    if catalog_path.exists():
        try:
            catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
            articles = catalog['articles']
            article_paths = [normalized(a['url'])[1] for a in articles]
            check('43 catalog articles', len(articles) == 43, len(articles))
            check('Catalog URLs unique', len(article_paths) == len(set(article_paths)))
            check('Catalog URLs exist', set(article_paths) <= set(docs), sorted(set(article_paths) - set(docs)))
            if historical:
                expected = historical - {'index.html', 'blog/index.html'}
                check('Catalog equals historical article inventory', set(article_paths) == expected,
                      {'missing': sorted(expected - set(article_paths)), 'extra': sorted(set(article_paths) - expected)})
            bad_genres = [{'url': a['url'], 'genre': a.get('genre')} for a in articles if a.get('genre') is not None and a['genre'] not in GENRES]
            check('Genres use approved vocabulary or null', not bad_genres, bad_genres)
            warnings.append({'pending_metadata': [{'url': a['url'], 'fields': [f for f in ['genre','author','publishedAt'] if not a.get(f)]} for a in articles if any(not a.get(f) for f in ['genre','author','publishedAt'])]})
        except (KeyError, ValueError, TypeError) as exc:
            check('Catalog parses', False, str(exc))
    else:
        article_paths = list((historical or set(docs)) - {'index.html', 'blog/index.html'})
        if not args.allow_missing_catalog:
            check('Catalog exists', False, str(catalog_path.relative_to(root)))

    article_by_path = {normalized(a['url'])[1]: a for a in articles}
    if articles:
        invalid_related = []
        for a in articles:
            for r in a.get('related', []):
                value = r if isinstance(r, str) else r.get('url', '')
                target = normalized(value)[1]
                if target not in article_by_path or target == normalized(a['url'])[1]:
                    invalid_related.append({'source': a['url'], 'related': value})
        check('Related references resolve to other catalog articles', not invalid_related, invalid_related)

    links, broken, fragments, metadata, raw_issues = [], [], [], [], []
    all_canonical = {}
    heading_jumps = []
    resource_issues = []
    for path, (doc, source) in docs.items():
        issues = []
        if not re.search(r'<!doctype\s+html', source, re.I): issues.append('missing doctype')
        if not re.search(r'<html\b', source, re.I): issues.append('missing html element')
        if not re.search(r'<head\b', source, re.I): issues.append('missing head element')
        if not re.search(r'<body\b', source, re.I): issues.append('missing body element')
        if not doc.get('lang'): issues.append('missing lang')
        if len(doc.xpath('//h1')) != 1: issues.append(f"h1 count {len(doc.xpath('//h1'))}")
        if len(doc.xpath('//main')) != 1: issues.append(f"main count {len(doc.xpath('//main'))}")
        if not doc.xpath('//meta[@name="viewport" and contains(@content,"width=device-width")]'): issues.append('missing responsive viewport')
        if not doc.xpath('//title[normalize-space()]'): issues.append('missing title')
        ids = Counter(doc.xpath('//@id'))
        duplicates = [i for i, n in ids.items() if n > 1]
        if duplicates: issues.append({'duplicate_ids': duplicates})
        if issues: raw_issues.append({'path': path, 'issues': issues})
        meta = {e.get('name') or e.get('property'): e.get('content') for e in doc.xpath('//meta[@name or @property]')}
        required_meta = ['description', 'og:title', 'og:type', 'og:url', 'og:description', 'og:image', 'twitter:card']
        missing = [key for key in required_meta if not meta.get(key)]
        canonicals = doc.xpath('//link[@rel="canonical"]/@href')
        if len(canonicals) != 1:
            missing.append(f'canonical count {len(canonicals)}')
        else:
            url, target = normalized(canonicals[0], path)
            if url.scheme != 'https' or url.netloc != 'magazine.ecash.mx' or target != path or url.fragment or url.query:
                missing.append({'canonical_not_self': canonicals[0]})
            all_canonical[path] = canonicals[0]
            if meta.get('og:url') != canonicals[0]: missing.append('og:url differs from canonical')
        if missing: metadata.append({'path': path, 'issues': missing})
        for property_name in ['og:image', 'twitter:image']:
            image_url = meta.get(property_name)
            if image_url:
                parsed, target = normalized(image_url, path)
                if parsed.netloc == 'magazine.ecash.mx' and not (root / target).is_file():
                    resource_issues.append({'source': path, 'kind': property_name, 'url': image_url})
        for element in doc.xpath('//*[@srcset]'):
            for candidate in element.get('srcset', '').split(','):
                tokens = candidate.strip().split()
                if not tokens:
                    continue
                parsed, target = normalized(tokens[0], path)
                if parsed.netloc == 'magazine.ecash.mx' and not (root / target).is_file():
                    resource_issues.append({'source': path, 'kind': 'srcset', 'url': tokens[0]})
        schema = []
        for script in doc.xpath('//script[@type="application/ld+json"]'):
            try: schema.extend(schema_types(json.loads(script.text or '')))
            except ValueError as exc: metadata.append({'path': path, 'schema_error': str(exc)})
        if path in article_paths:
            previous_level = 1
            for heading in doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," article-content ")]//*[self::h2 or self::h3 or self::h4 or self::h5 or self::h6]'):
                level = int(heading.tag[1])
                if level > previous_level + 1:
                    heading_jumps.append({'path': path, 'from': previous_level, 'to': level, 'heading': heading.text_content().strip()})
                previous_level = level
            article = article_by_path.get(path)
            if article:
                headline = re.sub(r'\s+', ' ', doc.xpath('string(//h1)')).strip()
                expected = re.sub(r'\s+', ' ', article['title']).strip()
                if headline != expected: metadata.append({'path': path, 'headline_differs_from_catalog': {'expected': expected, 'actual': headline}})
                labels = [re.sub(r'\s+', ' ', node.text_content()).strip() for node in doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," genre ")]')]
                if article.get('genre') and article['genre'] not in labels:
                    metadata.append({'path': path, 'visible_genre_not_from_catalog': labels})
                if article.get('genre') == 'Noticia' and 'NewsArticle' not in schema:
                    metadata.append({'path': path, 'schema_missing_for_news_genre': 'NewsArticle'})
            if 'BreadcrumbList' not in schema: metadata.append({'path': path, 'schema_missing': 'BreadcrumbList'})
            if not {'Article', 'NewsArticle', 'BlogPosting'} & set(schema): metadata.append({'path': path, 'schema_missing': 'Article/NewsArticle/BlogPosting'})
            if not doc.xpath('//nav[contains(@class,"breadcrumb") or contains(@aria-label,"miga") or contains(@aria-label,"readcrumb") or contains(@aria-label,"ruta") or contains(@aria-label,"Ruta")]'):
                warnings.append({'path': path, 'check_breadcrumb_markup': True})
        if doc.xpath('//img[not(@alt)]'): raw_issues.append({'path': path, 'issues': ['image missing alt attribute']})
        for tag, attr in [('a','href'), ('img','src'), ('script','src'), ('source','src'), ('link','href'), ('iframe','src')]:
            for element in doc.xpath(f'//{tag}[@{attr}]'):
                value = element.get(attr)
                parsed, target = normalized(value, path)
                if parsed.scheme not in {'http', 'https'} or parsed.netloc != 'magazine.ecash.mx': continue
                record = {'source': path, 'tag': tag, 'url': value, 'target': target}
                if not (root / target).is_file():
                    broken.append(record)
                elif parsed.fragment and target in docs:
                    fragment = unquote(parsed.fragment)
                    if not docs[target][0].xpath('//*[@id=$s or @name=$s]', s=fragment): fragments.append({**record, 'fragment': fragment})
                if tag == 'a' and target in docs: links.append(record)
    for stylesheet in root.rglob('*.css'):
        css_path = stylesheet.relative_to(root).as_posix()
        if set(stylesheet.relative_to(root).parts) & SKIP:
            continue
        css = stylesheet.read_text(encoding='utf-8')
        for match in re.finditer(r'url\(\s*[\"\']?([^\"\'\)]+)[\"\']?\s*\)', css):
            value = match.group(1).strip()
            parsed, target = normalized(value, css_path)
            if parsed.scheme in {'http', 'https'} and parsed.netloc == 'magazine.ecash.mx' and not (root / target).is_file():
                resource_issues.append({'source': css_path, 'kind': 'CSS resource/font', 'url': value})
    check('Social images, srcset candidates and CSS/font resources resolve', not resource_issues, resource_issues)
    check('Article heading levels do not skip', not heading_jumps, heading_jumps)
    check('HTML structure, landmarks, viewport, IDs and alt', not raw_issues, raw_issues)
    check('SEO metadata, self canonicals and structured data', not metadata, metadata)
    check('Internal links and local resources resolve', not broken, broken)
    check('Internal fragment targets resolve', not fragments, fragments)
    reachable = {'index.html'}
    queue = deque(reachable)
    adjacency = {}
    for link in links: adjacency.setdefault(link['source'], set()).add(link['target'])
    while queue:
        page = queue.popleft()
        for target in adjacency.get(page, set()) - reachable:
            reachable.add(target)
            queue.append(target)
    check('43 articles reachable from homepage without JavaScript', set(article_paths) <= reachable,
          {'reachable_articles': len(set(article_paths) & reachable), 'unreachable': sorted(set(article_paths) - reachable)})
    archive_targets = adjacency.get('blog/index.html', set())
    check('Archive links every article', set(article_paths) <= archive_targets,
          {'linked_articles': len(set(article_paths) & archive_targets), 'missing': sorted(set(article_paths) - archive_targets)})

    sitemap_path = root / 'sitemap.xml'
    try:
        tree = etree.parse(str(sitemap_path))
        urls = tree.xpath('//*[local-name()="loc"]/text()')
        sitemap_paths = [normalized(u)[1] for u in urls]
        indexable = {p for p, (d, _) in docs.items() if not d.xpath('//meta[@name="robots" and contains(@content,"noindex")]')}
        check('Sitemap URLs unique', len(urls) == len(set(urls)))
        check('Sitemap includes all indexable HTML', indexable == set(sitemap_paths), {'missing': sorted(indexable-set(sitemap_paths)), 'extra': sorted(set(sitemap_paths)-indexable)})
        noncanonical = [u for u in urls if all_canonical.get(normalized(u)[1]) != u]
        check('Sitemap uses canonical URLs', not noncanonical, noncanonical)
    except (OSError, etree.XMLSyntaxError) as exc:
        check('Sitemap XML parses', False, str(exc))

    feed_path = root / 'feed.xml'
    try:
        feed = etree.parse(str(feed_path))
        items = feed.xpath('/rss/channel/item')
        feed_urls = [i.findtext('link') for i in items]
        check('RSS 2.0 contains actual article links', bool(items) and all(normalized(u or '')[1] in set(article_paths) for u in feed_urls), len(items))
        check('RSS items unique', len(feed_urls) == len(set(feed_urls)))
        for item in items:
            check(f"RSS required fields: {item.findtext('link')}", all(item.findtext(k) for k in ['title','link','guid','description']))
    except (OSError, etree.XMLSyntaxError) as exc:
        check('RSS XML parses', False, str(exc))

    cdn = [p for p, (_, source) in docs.items() if re.search(r'<script[^>]+src=[\"\'][^\"\']*cdn\.tailwindcss', source)]
    check('No runtime Tailwind CDN', not cdn, cdn)
    result = {'passed': not failures, 'counts': {'html': len(docs), 'historical': len(historical), 'catalog_articles': len(articles), 'article_reachable': len(set(article_paths)&reachable), 'checks': len(checks), 'failures': len(failures)}, 'checks': checks, 'warnings': warnings}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'counts': result['counts'], 'failed_checks': [f['check'] for f in failures]}, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
