#!/usr/bin/env python3
"""Build the static magazine from the editorial catalogue and preserved fragments.

No network requests or publication side effects. Run from any directory.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from email.utils import format_datetime
from html import escape
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit
import xml.etree.ElementTree as ET

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://magazine.ecash.mx'
BRAND = 'eCash Magazine México'
GENRES = ['Noticia', 'Entrevista', 'Crónica', 'Reportaje', 'Columna', 'Opinión', 'Editorial', 'Reseña', 'Análisis técnico']
MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
WRITTEN = []
MEDIA = {}
ARTICLES = []
BY_URL = {}
SEARCH_TEXT = {}
SITE = {}
METADATA_REMOVALS = {}


def esc(value):
    return escape(str(value or ''), quote=True)


def norm(value):
    return ' '.join(str(value or '').split())


def slug(value):
    plain = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', plain).strip('-') or 'archivo'


def canonical(route):
    return BASE + quote(route, safe='/%')


def date_label(value):
    if not value:
        return ''
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T.*)?', value):
        year, month, day = map(int, value[:10].split('-'))
        return f'{day} de {MONTHS[month - 1]} de {year}'
    return value


def author_name(article):
    author = article.get('author')
    return author.get('name', '') if isinstance(author, dict) else (author or '')


def topics(article):
    return [t for t in article.get('topics', []) if isinstance(t, dict) and t.get('label')]


def topic_slug(topic):
    return topic.get('slug') or slug(topic['label'])


def article_sort(article):
    return (article.get('publishedAt') or '', article['title'])


def genre_badge(article):
    genre = article.get('genre')
    if genre:
        return f'<a class="genre" href="/generos/{slug(genre)}/">{esc(genre)}</a>'
    return '<span class="genre genre--pending">Género pendiente</span>'


def metadata(article, *, full=False):
    parts = []
    name = author_name(article)
    if name:
        parts.append(f'<a rel="author" href="/autores/{slug(name)}/">{esc(name)}</a>')
    published = article.get('publishedAt')
    if published:
        parts.append(f'<time datetime="{esc(published)}">{esc(date_label(published))}</time>')
    elif full:
        parts.append('<span>Fecha de publicación no consignada</span>')
    if article.get('readingMinutes'):
        parts.append(f'<span>{esc(article["readingMinutes"])} min de lectura</span>')
    modified = article.get('updatedAt')
    if modified and modified != published:
        parts.append(f'<span>Actualizado <time datetime="{esc(modified)}">{esc(date_label(modified))}</time></span>')
    return '<div class="story-meta">' + ''.join(f'<span>{p}</span>' for p in parts) + '</div>' if parts else ''


def image_data(article):
    original = article.get('image')
    if not original or not isinstance(original, dict) or not original.get('src'):
        return None
    data = dict(original)
    mapped = MEDIA.get(original['src'], {})
    data.update({k: v for k, v in mapped.items() if k in ('src', 'width', 'height', 'srcset', 'sizes')})
    return data


def picture(article, css='story-image', *, eager=False):
    data = image_data(article)
    if not data:
        return ''
    attrs = f'src="{esc(data["src"])}" alt="{esc(data.get("alt"))}"'
    if data.get('width') and data.get('height'):
        attrs += f' width="{int(data["width"])}" height="{int(data["height"])}"'
    if data.get('srcset'):
        attrs += f' srcset="{esc(data["srcset"])}" sizes="(max-width: 700px) 90vw, (max-width: 1100px) 45vw, 560px"'
    if eager:
        attrs += ' fetchpriority="high"'
    else:
        attrs += ' loading="lazy" decoding="async"'
    return f'<img class="{css}" {attrs}>'


def tag_links(article, limit=None):
    items = topics(article)
    if limit:
        items = items[:limit]
    if not items:
        return ''
    return '<ul class="tags" aria-label="Temas">' + ''.join(
        f'<li><a class="tag" href="/temas/{esc(topic_slug(t))}/">{esc(t["label"])}</a></li>' for t in items
    ) + '</ul>'


def card(article, *, compact=False, filtering=False, heading='h3', image=True):
    classes = 'story-card story-card--compact' if compact else 'story-card'
    attrs = ''
    if filtering:
        search = ' '.join([article['title'], article.get('summary') or '', article.get('genre') or '', article.get('originalGenreLabel') or '', author_name(article), ' '.join(t['label'] for t in topics(article))])
        attrs = (f' data-article-url="{esc(article["url"])}" data-search="{esc(search)}"'
                 f' data-genre="{esc(article.get("genre") or "pending")}"'
                 f' data-topic="{esc(" ".join(topic_slug(t) for t in topics(article)))}"'
                 f' data-author="{esc(author_name(article))}" data-year="{esc((article.get("publishedAt") or "")[:4])}"')
    img = picture(article) if image and not compact else ''
    if img:
        img = f'<a href="{esc(article["url"])}" tabindex="-1" aria-hidden="true">{img}</a>'
    deck = f'<p class="story-deck">{esc(article["summary"])}</p>' if article.get('summary') and not compact else ''
    return f'''<article class="{classes}"{attrs}>{img}<div class="story-card-body">{genre_badge(article)}
<{heading} class="story-title"><a href="{esc(article['url'])}">{esc(article['title'])}</a></{heading}>
{deck}{metadata(article)}{tag_links(article, 3) if not compact else ''}</div></article>'''


def nav():
    return '''<a class="skip-link" href="#contenido">Saltar al contenido</a>
<header class="site-header"><div class="masthead container">
<a class="brand" href="/" aria-label="eCash Magazine México — Primera Plana"><span class="brand-name">eCash<span>Magazine</span></span><span class="brand-place">México</span></a>
<div class="masthead-tools"><a href="/blog/index.html">Archivo</a><a href="/buscar/">Buscar</a><button type="button" class="nav-toggle" aria-controls="site-nav" aria-expanded="false" hidden>Menú</button></div></div>
<nav class="site-nav" id="site-nav" aria-label="Navegación principal"><div class="container nav-links"><a href="/">Primera Plana</a><a href="/generos/">Géneros</a><a href="/temas/">Temas</a><a href="/autores/">Autores</a><a href="/blog/index.html">Archivo completo</a><a href="/buscar/">Buscar</a><a href="/principios-editoriales/">La revista</a></div></nav></header>''' + '<script>' + (ROOT / 'assets/js/navigation.js').read_text(encoding='utf-8') + '</script>'


def footer():
    return '''<footer class="site-footer"><div class="container"><p class="brand-name">eCash Magazine México</p><p>Tecnología, economía y cultura desde México.</p><nav aria-label="Enlaces editoriales"><a href="/principios-editoriales/">Principios editoriales</a><a href="/correcciones/">Correcciones y actualizaciones</a><a href="/autores/">Autores</a><a href="/feed.xml">RSS</a><a href="https://ecash.mx">Portal eCash México ↗</a></nav><p>XEC es el dinero · RMZ es la llave · La cultura es la red</p><small>Contenidos bajo CC0 · eCash Magazine México</small></div></footer>'''


def breadcrumbs(items):
    html_items = ['<li><a href="/">Inicio</a></li>']
    schema_items = [{'@type': 'ListItem', 'position': 1, 'name': 'Inicio', 'item': BASE + '/'}]
    for i, (label, route) in enumerate(items, 2):
        html_items.append(f'<li><a href="{esc(route)}">{esc(label)}</a></li>' if route else f'<li aria-current="page">{esc(label)}</li>')
        item = {'@type': 'ListItem', 'position': i, 'name': label}
        if route:
            item['item'] = canonical(route)
        schema_items.append(item)
    return '<nav class="breadcrumbs" aria-label="Ruta de navegación"><ol>' + ''.join(html_items) + '</ol></nav>', {'@type': 'BreadcrumbList', 'itemListElement': schema_items}


def page(route, title, body, *, description='', schemas=None, article=None, noindex=False):
    url = canonical(route)
    organization = {'@type': 'NewsMediaOrganization', '@id': BASE + '/#organization', 'name': BRAND, 'url': BASE + '/'}
    graph = [organization] + (schemas or [])
    lang = article.get('language') or 'es-MX' if article else 'es-MX'
    social = '/assets/media/ecash-magazine-social.png'
    width, height = 1200, 630
    alt = BRAND
    if article:
        img = image_data(article)
        if img and (img.get('width') or 0) >= 960:
            social = img['src']
            width, height = img.get('width'), img.get('height')
            alt = img.get('alt') or article['title']
    social_url = urljoin(BASE, social)
    type_meta = 'article' if article else 'website'
    article_dates = ''
    if article:
        for key, prop in [('publishedAt', 'article:published_time'), ('updatedAt', 'article:modified_time')]:
            if article.get(key):
                article_dates += f'<meta property="{prop}" content="{esc(article[key])}">\n'
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ''
    desc = f'<meta name="description" content="{esc(description)}">' if description else ''
    serialized = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False).replace('<', '\\u003c')
    analytics = ''
    tracking = SITE.get('analytics', {})
    if route in tracking.get('paths', []):
        measurement = tracking.get('measurementId', '')
        if not re.fullmatch(r'G-[A-Z0-9]+', measurement):
            raise ValueError('Invalid existing analytics identifier')
        analytics = f'<script async src="https://www.googletagmanager.com/gtag/js?id={measurement}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{measurement}");</script>'
    data = f'''<!DOCTYPE html>
<html lang="{esc(lang)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | {BRAND}</title>{desc}
<link rel="canonical" href="{url}"><link rel="icon" href="/favicon.ico" sizes="any">
<meta name="theme-color" content="#F6F3EC">{robots}
<meta property="og:site_name" content="{BRAND}"><meta property="og:type" content="{type_meta}"><meta property="og:title" content="{esc(title)}"><meta property="og:url" content="{url}">
<meta property="og:description" content="{esc(description)}"><meta property="og:image" content="{esc(social_url)}"><meta property="og:image:alt" content="{esc(alt)}"><meta property="og:image:width" content="{width}"><meta property="og:image:height" content="{height}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{esc(social_url)}"><meta name="twitter:image:alt" content="{esc(alt)}">
{article_dates}<link rel="alternate" type="application/rss+xml" title="eCash Magazine México — publicaciones" href="/feed.xml">
<link rel="stylesheet" href="/assets/css/editorial.css"><script defer src="/assets/js/editorial.js"></script>
<script type="application/ld+json">{serialized}</script>{analytics}
</head><body>{nav()}<main id="contenido">{body}</main>{footer()}</body></html>\n'''
    target = ROOT / route.lstrip('/')
    if route.endswith('/'):
        target /= 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding='utf-8')
    WRITTEN.append({'route': route, 'path': str(target.relative_to(ROOT)), 'article': bool(article), 'indexable': not noindex})


def fragment(article):
    path = ROOT / 'content' / article['url'].lstrip('/')
    source = path.read_text(encoding='utf-8')
    node = html.fragment_fromstring(source, create_parent='div')
    heading_ids = [e.get('id') for e in node.xpath('.//h1[@id]')]
    # Reviewed, exact matches only: the catalogue supplies the shared header.
    # Keep the original fragments intact and fail if a source wrapper changes.
    for rule in METADATA_REMOVALS.get(article['url'], []):
        matches = node.xpath(rule['xpath'])
        if len(matches) != 1 or norm(matches[0].text_content()) != rule['expectedText']:
            raise ValueError(f'Metadata replacement no longer matches: {article["url"]}: {rule["expectedText"]}')
        matches[0].drop_tree()
    # Public shell emits the same heading/deck from the catalogue, once.
    for h1 in list(node.xpath('.//h1')):
        if norm(h1.text_content()) != norm(article['title']):
            raise ValueError(f'H1 differs from catalogue: {article["url"]}')
        h1.drop_tree()
    summary = article.get('summary')
    if summary:
        for p in node.xpath('.//p'):
            if norm(p.text_content()) == norm(summary):
                p.drop_tree()
                break
    for element in node.iter():
        # Remove old appearance without editing words, IDs, links or data.
        for attr in list(element.attrib):
            if attr == 'style' or attr.lower().startswith('on'):
                del element.attrib[attr]
        if element.tag in ('main', 'article', 'header', 'footer'):
            element.tag = 'div'
        if element.tag == 'div' and (element.get('aria-label') or element.get('aria-labelledby') or element.get('role') == 'region'):
            element.tag = 'section'
            if element.get('role') == 'region':
                del element.attrib['role']
    for e in node.xpath('.//script | .//style'):
        e.drop_tree()
    for a in node.xpath('.//a[@href]'):
        href = a.get('href')
        if article['url'] == '/reportajes/tonalli-faucet-ecash-mexico.html' and href == './index.html':
            a.set('href', '/blog/index.html')
        if a.get('target') == '_blank':
            a.set('rel', 'noopener noreferrer')
    for i, image in enumerate(node.xpath('.//img')):
        src = image.get('src', '')
        if 'editorial-legacy-image' in image.get('class', '') and any(x in src for x in ('photo-1614064641913-a5f10665f8df', 'photo-1639762681485-074b7f4ec651')):
            # These decorative CSS backgrounds already return 404. Their source
            # is retained in the preservation manifest; do not add broken images.
            image.drop_tree()
            continue
        data = MEDIA.get(src)
        if data:
            for attr in ('src', 'width', 'height', 'srcset', 'sizes'):
                if data.get(attr):
                    image.set(attr, str(data[attr]))
            if data.get('width') and int(data['width']) < 960:
                image.set('style', f'max-width:min(100%, {int(data["width"])}px)')
        if not image.get('alt'):
            image.set('alt', image.get('alt', ''))
        image.set('decoding', 'async')
        if i == 0:
            image.attrib.pop('loading', None)
        else:
            image.set('loading', 'lazy')
    for frame in node.xpath('.//iframe'):
        frame.set('loading', 'lazy')
        if not frame.get('title'):
            frame.set('title', 'Video adjunto a ' + article['title'])
        frame.set('width', '560')
        frame.set('height', '315')
    for table_number, table in enumerate(node.xpath('.//table'), 1):
        for th in table.xpath('.//th'):
            if not th.get('scope'):
                th.set('scope', 'col' if th.getparent() == table.xpath('.//tr')[0] else 'row')
        parent = table.getparent()
        wrapper = html.Element('section', {'class': 'table-scroll', 'tabindex': '0', 'aria-label': f'Tabla {table_number}: ' + article['title']})
        index = parent.index(table)
        parent.remove(table)
        wrapper.append(table)
        parent.insert(index, wrapper)
    for pre_number, pre in enumerate(node.xpath('.//pre'), 1):
        pre.set('tabindex', '0')
        pre.attrib.pop('aria-label', None)
        parent = pre.getparent()
        wrapper = html.Element('section', {'class': 'code-region', 'aria-label': f'Bloque de código o datos técnicos {pre_number}'})
        index = parent.index(pre)
        parent.remove(pre)
        wrapper.append(pre)
        parent.insert(index, wrapper)
    for box_number, box in enumerate(node.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " codebox ")]'), 1):
        if box.tag != 'pre':
            box.tag = 'section'
            box.set('tabindex', '0')
            box.set('aria-label', f'Datos técnicos {box_number} de la publicación')
    for aside_number, aside in enumerate(node.xpath('.//aside'), 1):
        if not aside.get('aria-label') and not aside.get('aria-labelledby'):
            headings = aside.xpath('.//h2 | .//h3 | .//h4')
            label = norm(headings[0].text_content()) if headings else f'Contexto de la publicación {aside_number}'
            aside.set('aria-label', label)
    # Preserve heading wording and deep-link IDs while repairing skipped levels.
    previous_level = 1
    for heading in node.xpath('.//h2 | .//h3 | .//h4 | .//h5 | .//h6'):
        level = min(int(heading.tag[1]), previous_level + 1)
        heading.tag = f'h{level}'
        previous_level = level
    used = {e.get('id') for e in node.xpath('.//*[@id]')}
    toc_items = []
    for heading in node.xpath('.//h2 | .//h3'):
        label = norm(heading.text_content())
        if not label or len(label) <= 2:
            continue
        if not heading.get('id'):
            stem, idx = slug(label), 2
            identifier = stem
            while identifier in used or identifier in ('contenido', 'fuentes-evidencia', 'lectura', 'relacionados'):
                identifier = f'{stem}-{idx}'
                idx += 1
            heading.set('id', identifier)
            used.add(identifier)
        if heading.tag == 'h2':
            toc_items.append((label, heading.get('id')))
    # Formatting-only whitespace outside literal code; never rewrite code bytes.
    for element in node.iter():
        if element.tag not in ('pre', 'code') and not element.xpath('ancestor::pre | ancestor::code'):
            if element.text and not element.text.strip():
                element.text = '\n' if '\n' in element.text else ' '
        parent = element.getparent()
        if parent is not None and parent.tag not in ('pre', 'code') and not parent.xpath('ancestor::pre | ancestor::code'):
            if element.tail and not element.tail.strip():
                element.tail = '\n' if '\n' in element.tail else ' '
    toc = ''
    if len(toc_items) >= 5:
        toc = '<details class="toc"><summary>En este artículo</summary><ol>' + ''.join(f'<li><a href="#{esc(anchor)}">{esc(label)}</a></li>' for label, anchor in toc_items) + '</ol></details>'
    text = norm(node.text_content())
    SEARCH_TEXT[article['url']] = text
    return ''.join(html.tostring(c, encoding='unicode', method='html') for c in node), toc, heading_ids


def evidence(article):
    refs = article.get('references') or []
    limitations = article.get('evidenceLimitations') or []
    if not refs and not limitations:
        return ''
    categories = {'primary': 'Fuente primaria', 'secondary': 'Referencia secundaria', 'technical': 'Evidencia técnica'}
    items = []
    for ref in refs:
        label = ref.get('label') or ref.get('locator') or ref.get('url')
        if not label:
            continue
        link = f'<a href="{esc(ref["url"])}">{esc(label)}</a>' if ref.get('url') else esc(label)
        cat = categories.get(ref.get('category'), 'Referencia · clasificación pendiente')
        locator = ref.get('locator')
        if isinstance(locator, (dict, list)):
            locator = json.dumps(locator, ensure_ascii=False)
        loc = f'<p><code>{esc(locator)}</code></p>' if locator and locator != label else ''
        items.append(f'<li class="evidence-item"><span class="evidence-kind">{cat}</span><p>{link}</p>{loc}</li>')
    limits = ''.join(f'<p>{esc(item.get("text") if isinstance(item, dict) else item)}</p>' for item in limitations)
    return f'''<section class="evidence" id="fuentes-evidencia" aria-labelledby="fuentes-title"><h2 id="fuentes-title">Fuentes y evidencia</h2>
<p>Referencias consignadas en esta publicación. Su presencia no equivale por sí sola a una verificación independiente.</p><ul>{''.join(items)}</ul>
{f'<div class="notice"><h3>Limitaciones de comprobación consignadas</h3>{limits}</div>' if limits else ''}</section>'''


def related_articles(article):
    explicit = []
    for ref in article.get('related') or []:
        url = ref.get('url') if isinstance(ref, dict) else ref
        if url and url.startswith(BASE):
            url = url[len(BASE):]
        if url in BY_URL and url != article['url']:
            explicit.append(BY_URL[url])
    topic_set = {topic_slug(t) for t in topics(article)}
    # Matching only existing explicit tags: this chooses links, not article metadata.
    scored = []
    for candidate in ARTICLES:
        if candidate['url'] == article['url'] or candidate in explicit:
            continue
        score = len(topic_set & {topic_slug(t) for t in topics(candidate)})
        if score:
            scored.append((score, article_sort(candidate), candidate))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return (explicit + [row[2] for row in scored])[:3]


def render_article(article):
    content, toc, heading_ids = fragment(article)
    genre = article.get('genre')
    parent = (genre, f'/generos/{slug(genre)}/') if genre else ('Archivo', '/blog/index.html')
    crumbs, breadcrumb_schema = breadcrumbs([parent, (article['title'], None)])
    breadcrumb_schema['itemListElement'][-1]['item'] = canonical(article['url'])
    deck = f'<p class="article-deck">{esc(article["summary"])}</p>' if article.get('summary') else ''
    original = ''
    if not genre and article.get('originalGenreLabel'):
        original = f'<p class="original-label">Rótulo original: {esc(article["originalGenreLabel"])}. Clasificación editorial pendiente.</p>'
    section = f'<span class="section-label">{esc(article["section"])}</span>' if article.get('section') else ''
    sources = evidence(article)
    reading = '<p class="reading-links"><a href="#fuentes-evidencia">Consultar fuentes y evidencia ↓</a></p>' if sources else ''
    related = related_articles(article)
    following = ''
    if related:
        following = '<section class="related-stories section-block" id="relacionados"><div class="section-heading"><h2>Lecturas relacionadas</h2></div><div class="story-grid">' + ''.join(card(a, compact=True) for a in related) + '</div></section>'
    latest = [a for a in sorted(ARTICLES, key=article_sort, reverse=True) if a.get('publishedAt') and a['url'] != article['url']][:3]
    latest_html = '<section class="section-block"><div class="section-heading"><h2>Últimas publicaciones</h2><a href="/blog/index.html">Ver el archivo completo →</a></div><div class="story-grid">' + ''.join(card(a, compact=True) for a in latest) + '</div></section>'
    title_id = f' id="{esc(heading_ids[0])}"' if heading_ids else ''
    body = f'''<div class="container">{crumbs}<header class="article-header"><div class="eyebrow">{genre_badge(article)} {section}</div><h1 class="article-title"{title_id}>{esc(article['title'])}</h1>{deck}{metadata(article, full=True)}{original}{tag_links(article)}{reading}</header>
<div class="article-layout">{toc}<article class="article-content" id="lectura" aria-label="Texto de la publicación">{content}</article>{sources}</div>{following}{latest_html}</div>'''
    schema_type = 'NewsArticle' if genre == 'Noticia' else ('BlogPosting' if genre in ('Opinión', 'Columna') else 'Article')
    schema = {'@type': schema_type, '@id': canonical(article['url']) + '#article', 'headline': article['title'], 'url': canonical(article['url']), 'mainEntityOfPage': canonical(article['url']), 'publisher': {'@id': BASE + '/#organization'}}
    for key, out in [('publishedAt', 'datePublished'), ('updatedAt', 'dateModified'), ('summary', 'description'), ('language', 'inLanguage'), ('section', 'articleSection')]:
        if article.get(key):
            schema[out] = article[key]
    name = author_name(article)
    if name and isinstance(article.get('author'), dict) and article['author'].get('type') in ('Person', 'Organization'):
        schema['author'] = {'@type': article['author']['type'], 'name': name, 'url': canonical(f'/autores/{slug(name)}/')}
    image = image_data(article)
    if image:
        schema['image'] = urljoin(BASE, image['src'])
    page(article['url'], article['title'], body, description=article.get('summary') or article['title'], schemas=[schema, breadcrumb_schema], article=article)


def section(title, articles, route=None, *, compact=False):
    if not articles:
        return ''
    link = f'<a href="{esc(route)}">Ver más →</a>' if route else ''
    return f'<section class="section-block"><div class="section-heading"><h2>{esc(title)}</h2>{link}</div><div class="{"story-list" if compact else "story-grid"}">' + ''.join(card(a, compact=compact) for a in articles) + '</div></section>'


def render_home():
    config = json.loads((ROOT / 'editorial/frontpage.json').read_text())
    lead = BY_URL[config['lead']]
    sorted_articles = sorted(ARTICLES, key=article_sort, reverse=True)
    latest = [a for a in sorted_articles if a.get('publishedAt') and a['url'] != lead['url']][:4]
    used = {lead['url']}
    lead_image = image_data(lead)
    image = picture(lead, 'lead-image', eager=True) if lead_image and (lead_image.get('width') or 0) >= 960 else ''
    intro = f'''<div class="container"><div class="section-heading section-block"><div><p class="eyebrow">Tecnología · Economía · Cultura</p><p>Una revista especializada en eCash, hecha desde México.</p></div><a href="/blog/index.html">Explorar el archivo · {len(ARTICLES)} publicaciones →</a></div>
<section class="lead-grid" aria-labelledby="primera-plana"><div class="lead-story"><p class="eyebrow" id="primera-plana">Primera Plana</p>{genre_badge(lead)}
<h1 class="lead-title"><a href="{esc(lead['url'])}">{esc(lead['title'])}</a></h1>{f'<p class="lead-deck">{esc(lead["summary"])}</p>' if lead.get('summary') else ''}{metadata(lead)}{tag_links(lead,3)}{image}<p><a class="read-link" href="{esc(lead['url'])}">Leer la historia →</a></p></div>
<aside class="news-rail" aria-labelledby="actualidad"><h2 id="actualidad">Últimas publicaciones</h2>{''.join(card(a,compact=True) for a in latest)}<a href="/blog/index.html">Todo el archivo →</a></aside></section>'''
    parts = [intro]
    def choose(predicate, count):
        selected = [a for a in sorted_articles if a['url'] not in used and predicate(a)][:count]
        used.update(a['url'] for a in selected)
        return selected
    parts.append(section('Últimas noticias', choose(lambda a: a.get('genre') == 'Noticia', 3), '/generos/noticia/', compact=True))
    parts.append(section('Grandes Reportajes', choose(lambda a: a.get('genre') == 'Reportaje', 2), '/generos/reportaje/'))
    parts.append(section('Análisis técnico', choose(lambda a: a.get('genre') == 'Análisis técnico', 3), '/generos/analisis-tecnico/'))
    parts.append('<div class="split-sections">' + section('Crónicas', choose(lambda a: a.get('genre') == 'Crónica', 2), '/generos/cronica/') + section('Cultura', choose(lambda a: 'cultura' in (a.get('section') or '').lower() or any(topic_slug(t) == 'cultura' for t in topics(a)), 2), '/temas/') + '</div>')
    opinions = choose(lambda a: a.get('genre') in ('Opinión', 'Columna'), 3)
    if opinions:
        parts.append('<div class="opinion-band">' + section('Opinión / Columnas', opinions, '/generos/opinion/', compact=True) + '</div>')
    parts.append(section('Entrevistas', choose(lambda a: a.get('genre') == 'Entrevista', 2), '/generos/entrevista/'))
    parts.append(section('Breves', choose(lambda a: a.get('format') == 'breve', 4), '/generos/noticia/', compact=True))
    parts.append('''<section class="section-block"><div class="section-heading"><h2>Radio y conversaciones</h2></div><p>Discusión abierta sobre sistemas monetarios, infraestructura y soberanía técnica.</p><p><a href="https://www.youtube.com/watch?v=4eO4hWRv4x0" target="_blank" rel="noopener noreferrer">Abrir conversación en YouTube ↗</a></p></section>''')
    parts.append('''<section class="archive-callout"><div><p class="eyebrow">Memoria y contexto</p><h2>El archivo de la revista</h2><p>Publicaciones, fuentes y debates del ecosistema eCash. Consulta por fecha, género, tema o firma.</p></div><a href="/blog/index.html">Entrar al archivo completo →</a></section></div>''')
    page('/', 'Primera Plana', ''.join(parts), description='eCash Magazine México: periodismo, análisis técnico, economía y cultura. Primera Plana y archivo de publicaciones sobre eCash desde México.', schemas=[{'@type': 'WebSite', '@id': BASE + '/#website', 'name': BRAND, 'url': BASE + '/'}])


def option(value, text):
    return f'<option value="{esc(value)}">{esc(text)}</option>'


def filter_form():
    genre_opts = ''.join(option(g, g) for g in GENRES if any(a.get('genre') == g for a in ARTICLES))
    genre_opts += option('pending', 'Género pendiente')
    topic_map = {topic_slug(t): t['label'] for a in ARTICLES for t in topics(a)}
    topic_opts = ''.join(option(k, v) for k, v in sorted(topic_map.items(), key=lambda x: x[1]))
    names = sorted({author_name(a) for a in ARTICLES if author_name(a)})
    authors = ''.join(option(n, n) for n in names)
    years = sorted({a['publishedAt'][:4] for a in ARTICLES if a.get('publishedAt')}, reverse=True)
    return f'''<form class="archive-tools" id="search-form" action="/buscar/" role="search"><div class="filter-group"><label class="filter-label" for="search-input">Buscar en las publicaciones</label><input class="search-input" type="search" name="q" id="search-input" placeholder="Título, texto, autor o tema" autocomplete="off"></div>
<div class="filter-group"><label class="filter-label" for="filter-genre">Género</label><select id="filter-genre" name="genre"><option value="">Todos los géneros</option>{genre_opts}</select></div>
<div class="filter-group"><label class="filter-label" for="filter-topic">Tema</label><select id="filter-topic" name="topic"><option value="">Todos los temas</option>{topic_opts}</select></div>
<div class="filter-group"><label class="filter-label" for="filter-author">Firma</label><select id="filter-author" name="author"><option value="">Todas las firmas</option>{authors}</select></div>
<div class="filter-group"><label class="filter-label" for="filter-year">Año</label><select id="filter-year" name="year"><option value="">Todos los años</option>{''.join(option(y,y) for y in years)}</select></div>
<button type="submit">Buscar</button><button type="reset">Limpiar filtros</button></form><noscript><p class="notice">La búsqueda y los filtros interactivos requieren JavaScript. Puedes recorrer el archivo completo a continuación o consultar los <a href="/generos/">géneros</a> y <a href="/temas/">temas</a>.</p></noscript>'''


def render_archive(route='/blog/index.html', search=False):
    title = 'Buscar en la revista' if search else 'Archivo completo'
    crumbs, schema = breadcrumbs([(title, None)])
    schema['itemListElement'][-1]['item'] = canonical(route)
    dated, undated = [], []
    for a in sorted(ARTICLES, key=article_sort, reverse=True):
        (dated if a.get('publishedAt') else undated).append(a)
    groups = defaultdict(list)
    for a in dated:
        groups[a['publishedAt'][:7]].append(a)
    groups['Sin fecha consignada'] = undated
    listing = []
    for period, items in groups.items():
        if not items:
            continue
        label = period
        if re.fullmatch(r'\d{4}-\d{2}', period):
            y, m = map(int, period.split('-'))
            label = f'{MONTHS[m-1].capitalize()} {y}'
        listing.append(f'<section class="archive-year" data-archive-group><h2>{esc(label)}</h2><div class="archive-list">' + ''.join(card(a, compact=True, filtering=True) for a in items) + '</div></section>')
    external = '' if search else '''<section class="section-block"><h2>Lecturas en el portal eCash México</h2><p>Enlaces externos conservados del archivo anterior.</p><ul><li><a href="https://ecash.mx/blog/que-es-ecash.html">Por qué eCash necesita cultura, no solo tecnología.</a></li><li><a href="https://ecash.mx/blog/integracion-ecash-thorchain.html">Liquidez nativa sin wrapped tokens</a></li><li><a href="https://ecash.mx/blog/teyolia-crowdfunding-xec.html">Teyolia: Crowdfunding no custodial con XEC</a></li><li><a href="https://ecash.mx/blog/mineria-ecash-mexico.html">Minería Soberana y Membresías RMZ</a></li></ul></section>'''
    body = f'''<div class="container">{crumbs}<header class="article-header"><p class="eyebrow">Memoria editorial</p><h1>{title}</h1><p class="article-deck">{len(ARTICLES)} publicaciones para consultar por fecha, género, tema o firma.</p></header>{filter_form()}<p class="results-count" id="results-count" role="status" aria-live="polite">{len(ARTICLES)} publicaciones</p><div class="empty-state" id="search-empty" hidden>No hay publicaciones que coincidan con estos filtros.</div><div id="search-results">{''.join(listing)}</div>{external}</div>'''
    page(route, title, body, description='Archivo completo de eCash Magazine México: consulta todas las publicaciones por fecha, género, tema y firma.', schemas=[schema])


def listing_page(route, title, articles, intro, parent=None, extra_schema=None):
    items = [parent, (title, None)] if parent else [(title, None)]
    crumbs, schema = breadcrumbs(items)
    schema['itemListElement'][-1]['item'] = canonical(route)
    listing = '<div class="story-grid">' + ''.join(card(a, heading='h2') for a in sorted(articles, key=article_sort, reverse=True)) + '</div>' if articles else '<p class="empty-state">Todavía no hay publicaciones con esta clasificación confirmada.</p>'
    page(route, title, f'<div class="container">{crumbs}<header class="article-header"><h1>{esc(title)}</h1><p class="article-deck">{esc(intro)}</p></header>{listing}<p class="section-block"><a href="/blog/index.html">Consultar el archivo completo →</a></p></div>', description=intro, schemas=[schema] + (extra_schema or []))


def render_taxonomies():
    definitions = {
        'Noticia': 'Hechos recientes y verificables, separados de la opinión.',
        'Entrevista': 'Información y testimonios con la voz de la fuente identificada.',
        'Crónica': 'Acontecimientos narrados con secuencia, contexto y datos verificables.',
        'Reportaje': 'Investigación, contexto, fuentes y evidencia sobre un tema.',
        'Columna': 'Una voz firmada, personal y reconocible.',
        'Opinión': 'Tesis y argumentos que distinguen datos de juicios.',
        'Editorial': 'La postura institucional de eCash Magazine México.',
        'Reseña': 'Evaluaciones de herramientas, obras y servicios.',
        'Análisis técnico': 'Problemas, conceptos, funcionamiento y límites de la tecnología.'}
    genre_cards = []
    for genre in GENRES:
        articles = [a for a in ARTICLES if a.get('genre') == genre]
        route = f'/generos/{slug(genre)}/'
        listing_page(route, genre, articles, definitions[genre], ('Géneros', '/generos/'))
        genre_cards.append(f'<section><h2><a href="{route}">{genre}</a></h2><p>{definitions[genre]}</p><p>{len(articles)} publicaciones clasificadas</p></section>')
    page('/generos/', 'Géneros periodísticos', '<div class="container"><header class="article-header"><h1>Géneros periodísticos</h1><p class="article-deck">Cada género establece una relación distinta con el lector.</p></header><div class="index-grid">' + ''.join(genre_cards) + '</div><p class="notice">Las piezas con clasificación pendiente permanecen disponibles en el <a href="/blog/index.html">archivo completo</a>, con su rótulo histórico conservado.</p></div>', description='Los nueve géneros periodísticos de eCash Magazine México: información, investigación, narrativa y opinión identificadas.')
    topic_map = {}
    for a in ARTICLES:
        for t in topics(a):
            topic_map.setdefault(topic_slug(t), {'label': t['label'], 'articles': []})['articles'].append(a)
    links = []
    for key, data in sorted(topic_map.items(), key=lambda x:x[1]['label']):
        route = f'/temas/{key}/'
        listing_page(route, data['label'], data['articles'], f'Publicaciones con el tema {data["label"]} consignado en sus metadatos editoriales.', ('Temas', '/temas/'))
        links.append(f'<li><a href="{esc(route)}">{esc(data["label"])}</a> <span>{len(data["articles"])}</span></li>')
    page('/temas/', 'Temas', '<div class="container"><header class="article-header"><h1>Temas</h1><p class="article-deck">Explora las etiquetas ya consignadas en las publicaciones.</p></header><ul class="topic-list">' + ''.join(links) + '</ul></div>', description='Índice de temas documentados en las publicaciones de eCash Magazine México.')
    names = sorted({author_name(a) for a in ARTICLES if author_name(a)})
    author_links = []
    for name in names:
        articles = [a for a in ARTICLES if author_name(a) == name]
        route = f'/autores/{slug(name)}/'
        kinds = {a['author'].get('type') for a in articles if isinstance(a.get('author'),dict)}
        kind = next(iter(kinds)) if len(kinds) == 1 else None
        extra = [{'@type': kind, '@id': canonical(route) + '#author', 'name': name, 'url': canonical(route)}] if kind in ('Person','Organization') else []
        listing_page(route, name, articles, 'Publicaciones que incluyen esta firma en su ficha editorial original.', ('Autores', '/autores/'), extra)
        author_links.append(f'<li><a href="{route}">{esc(name)}</a> <span>{len(articles)}</span></li>')
    page('/autores/', 'Autores y firmas', '<div class="container"><header class="article-header"><h1>Autores y firmas</h1><p class="article-deck">Firmas personales e institucionales que constan en las publicaciones.</p></header><ul class="topic-list">' + ''.join(author_links) + '</ul><p>Las publicaciones sin firma consignada siguen disponibles en el <a href="/blog/index.html">archivo</a>.</p></div>', description='Índice de las firmas consignadas en eCash Magazine México.')


def render_editorial_pages():
    body = '''<div class="container"><header class="article-header"><p class="eyebrow">La revista</p><h1>Principios editoriales</h1><p class="article-deck">Hechos, contexto, narrativa y postura: cada texto debe decirle al lector qué está leyendo.</p></header><div class="article-layout"><article class="article-content"><h2>Periodismo desde México</h2><p>eCash Magazine México aborda tecnología, economía y cultura. Su identidad se expresa en «XEC es el dinero · RMZ es la llave · La cultura es la red». Esa identidad no sustituye la evidencia ni convierte la cobertura de un proyecto en una recomendación.</p><h2>Nueve géneros, funciones distintas</h2><p>Una noticia informa; un reportaje investiga y presenta evidencia; una entrevista distingue la voz de la fuente; una crónica puede narrar. Columna y Opinión admiten una postura firmada. Editorial expresa la posición institucional. Reseña evalúa; Análisis técnico explica funcionamiento, consecuencias y límites.</p><p><a href="/generos/">Consultar los géneros periodísticos →</a></p><h2>Fuentes y límites</h2><p>Las referencias se presentan con su alcance real. Un commit identifica código; no demuestra por sí solo su despliegue o seguridad. Una transacción acredita un registro; no demuestra la verdad de todas sus afirmaciones.</p><h2>Archivo y atribución</h2><p>Se conservan los textos y sus URLs. Cuando una firma, fecha o clasificación histórica no está consignada de forma inequívoca, se mantiene pendiente. No se completa por suposición.</p><h2>Correcciones y actualizaciones</h2><p>Una corrección periodística debe explicar qué cambió y cuándo. Cambiar el diseño o la estructura técnica de una página no equivale a actualizar su información.</p><p><a href="/correcciones/">Correcciones y actualizaciones →</a></p><h2>Base editorial</h2><p>Estos criterios se basan en la Guía editorial de eCash Magazine México, elaborada a partir del Manual de periodismo de Vicente Leñero y Carlos Marín.</p></article></div></div>'''
    page('/principios-editoriales/', 'Principios editoriales', body, description='Criterios de eCash Magazine México para distinguir información, investigación, narrativa, opinión y evidencia.')
    updated = [a for a in ARTICLES if a.get('updatedAt') and a.get('updatedAt') != a.get('publishedAt')]
    body = '''<div class="container"><header class="article-header"><h1>Correcciones y actualizaciones</h1><p class="article-deck">Las fechas y notas editoriales pertenecen a la historia de cada publicación.</p></header><div class="article-content"><p>Las correcciones documentadas se presentan junto a cada artículo. Una actualización consignada no se clasifica automáticamente como corrección de hechos.</p><p>La migración de diseño conserva las fechas editoriales existentes. Los datos ausentes no se sustituyen por la fecha del rediseño.</p></div>''' + section('Artículos con actualización consignada', updated, compact=True) + '</div>'
    page('/correcciones/', 'Correcciones y actualizaciones', body, description='Cómo se presentan las correcciones y fechas de actualización editorial en eCash Magazine México.')
    page('/404.html', 'Página no encontrada', '<div class="container"><header class="article-header"><h1>Esta página no está aquí</h1><p class="article-deck">Puedes buscar la publicación o recorrer el archivo de la revista.</p><p><a href="/buscar/">Buscar</a> · <a href="/blog/index.html">Archivo completo</a></p></header></div>', description='Acceso al archivo y buscador de eCash Magazine México.', noindex=True)


def render_xml():
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    sitemap = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for item in WRITTEN:
        if not item['indexable']:
            continue
        entry = ET.SubElement(sitemap, 'url')
        ET.SubElement(entry, 'loc').text = canonical(item['route'])
        article = BY_URL.get(item['route'])
        if article:
            changed = article.get('updatedAt') or article.get('publishedAt')
            if changed:
                ET.SubElement(entry, 'lastmod').text = changed
    (ROOT / 'sitemap.xml').write_bytes(ET.tostring(sitemap, encoding='utf-8', xml_declaration=True))
    rss = ET.Element('rss', {'version':'2.0'})
    channel = ET.SubElement(rss, 'channel')
    for tag, value in [('title',BRAND),('link',BASE + '/'),('description','Publicaciones sobre tecnología, economía y cultura desde México.'),('language','es-MX')]:
        ET.SubElement(channel,tag).text = value
    for a in sorted(ARTICLES,key=article_sort,reverse=True):
        item = ET.SubElement(channel,'item')
        for tag, value in [('title',a['title']),('link',canonical(a['url'])),('guid',canonical(a['url'])),('description',a.get('summary') or a['title'])]:
            ET.SubElement(item,tag).text = value
        date = a.get('publishedAt')
        # RSS pubDate is optional. A date-only source cannot support an invented time/zone.
        if date and 'T' in date:
            parsed = datetime.fromisoformat(date.replace('Z','+00:00'))
            if parsed.tzinfo:
                ET.SubElement(item,'pubDate').text = format_datetime(parsed)
        if a.get('genre'):
            ET.SubElement(item,'category').text = a['genre']
    (ROOT / 'feed.xml').write_bytes(ET.tostring(rss,encoding='utf-8',xml_declaration=True))
    (ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n',encoding='utf-8')


def main():
    global ARTICLES, BY_URL, MEDIA, SITE, METADATA_REMOVALS
    catalog = json.loads((ROOT / 'editorial/catalog.json').read_text())
    SITE = json.loads((ROOT / 'editorial/site.json').read_text())
    METADATA_REMOVALS = json.loads((ROOT / 'editorial/metadata-removals.json').read_text())
    ARTICLES = catalog['articles']
    if len(ARTICLES) < 43 or len({a['url'] for a in ARTICLES}) != len(ARTICLES):
        raise ValueError('Expected at least the 43 historical articles and unique catalogue URLs')
    for a in ARTICLES:
        if a.get('genre') not in GENRES + [None]:
            raise ValueError(f'Unknown genre {a.get("genre")}')
        if not a['url'].startswith('/') or '..' in a['url']:
            raise ValueError('Unsafe article URL')
    BY_URL = {a['url']:a for a in ARTICLES}
    MEDIA = json.loads((ROOT / 'editorial/media-map.json').read_text())
    if 'media' in MEDIA:
        MEDIA = MEDIA['media']
    for article in ARTICLES:
        render_article(article)
    render_home()
    render_archive()
    render_archive('/buscar/',search=True)
    render_taxonomies()
    render_editorial_pages()
    render_xml()
    search_path = ROOT / 'assets/data/search.json'
    search_path.parent.mkdir(parents=True, exist_ok=True)
    search_path.write_text(json.dumps({'articles': [{'url': a['url'], 'searchText': SEARCH_TEXT[a['url']]} for a in ARTICLES]}, ensure_ascii=False, separators=(',', ':'))+'\n')
    (ROOT / 'editorial/generated-pages.json').write_text(json.dumps(WRITTEN,ensure_ascii=False,indent=2)+'\n')
    print(f'Generated {len(WRITTEN)} static HTML pages, sitemap and RSS; 43 historical article URLs preserved; {len(ARTICLES)} total publications.')


if __name__ == '__main__':
    main()
