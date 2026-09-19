#!/usr/bin/env python3
"""One-time, conservative extraction from the pre-redesign HTML snapshot.

Usage: python scripts/extract_legacy.py --source /path/to/baseline --output .
Requires lxml, used as a build-time HTML parser; no browser dependency.
The source MUST be an immutable baseline, never the generated public files.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

from lxml import etree, html


def normalized(value):
    return " ".join(value.split())


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def drop(node):
    """Remove only this node; preserve its tail text."""
    node.drop_tree()


def normalize_layout_whitespace(root):
    """Drop indentation on blank layout lines, preserving pre/code verbatim.

    Whitespace between inline siblings remains a separator. An element's tail
    belongs to its parent, so the tail after </code> can be normalized while
    text inside code (including tails of nested markup) stays byte-exact.
    """
    changed = 0

    def clean(value):
        if value is None:
            return None
        if not value.strip():
            return "\n" if "\n" in value or "\r" in value else (" " if value else "")
        return re.sub(r"[ \t]+(?=\r?\n)", "", value)

    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        ancestors = list(element.iterancestors())
        text_in_code = element.tag in ("pre", "code") or any(a.tag in ("pre", "code") for a in ancestors)
        tail_in_code = any(a.tag in ("pre", "code") for a in ancestors)
        for attr, protected in (("text", text_in_code), ("tail", tail_in_code)):
            if not protected:
                value = getattr(element, attr)
                replacement = clean(value)
                if replacement != value:
                    setattr(element, attr, replacement)
                    changed += 1
    return changed


def snapshot(root):
    text_segments = [normalized(t) for t in root.itertext() if normalized(t)]
    return {
        "text_segments": text_segments,
        "normalized_text_sha256": digest(" ".join(text_segments)),
        "links": [{"href": e.get("href"), "text": normalized(e.text_content())}
                  for e in root.xpath(".//a[@href]")],
        "images": [{k: e.get(k) for k in ("src", "srcset", "alt", "title") if e.get(k) is not None}
                   for e in root.xpath(".//img")],
        "embeds": [{"tag": e.tag, "src": e.get("src"), "title": e.get("title")}
                   for e in root.xpath(".//iframe|.//video|.//audio|.//source")],
        "code": [{"tag": e.tag, "text": e.text_content()}
                 for e in root.xpath(".//pre|.//code[not(ancestor::pre)]")],
        "headings": [{"tag": e.tag, "text": normalized(e.text_content()), "id": e.get("id")}
                     for e in root.xpath(".//h1|.//h2|.//h3|.//h4|.//h5|.//h6")],
        "ids": [e.get("id") for e in root.xpath(".//*[@id]")],
    }


def materialize_teyolia(root, source):
    """Move the exact published JS dataset into accessible, script-free HTML."""
    match = re.search(r"const steps = \[(.*?)\n    \];", source, re.S)
    if not match:
        raise ValueError("Teyolia step dataset not found in immutable source")
    entries = []
    for raw in re.findall(r"\{(.*?)\}", match.group(1), re.S):
        entry = dict(re.findall(r'(\w+):\s*"([^"\\]*(?:\\.[^"\\]*)*)"', raw))
        entries.append({k: entry[k] for k in ("icon", "title", "desc", "badge")})
    if len(entries) != 3:
        raise ValueError("Expected exactly the three published Teyolia steps")
    controls = root.get_element_by_id("step-controls")
    buttons = controls.xpath("./button")
    panel = root.get_element_by_id("step-content-title").getparent()
    for i, (button, entry) in enumerate(zip(buttons, entries)):
        details = etree.Element("details", {"class": "editorial-step"})
        if i == 0:
            details.set("open", "")
        summary = etree.SubElement(details, "summary")
        summary.text = button.text
        for child in list(button):
            if child.tag in ("h4", "h5", "h6"):
                child.tag = "strong"
            elif child.tag == "p":
                child.tag = "span"
            summary.append(copy.deepcopy(child))
        if i == 0:
            for child in list(panel):
                details.append(copy.deepcopy(child))
        else:
            etree.SubElement(details, "div", {"class": "step-icon"}).text = entry["icon"]
            etree.SubElement(details, "h3").text = entry["title"]
            etree.SubElement(details, "p").text = entry["desc"]
            etree.SubElement(details, "p", {"class": "step-status"}).text = entry["badge"]
        button.getparent().replace(button, details)
    drop(panel)
    chart = root.get_element_by_id("transparencyChart")
    labels_match = re.search(r"labels:\s*\[([^\]]+)\]", source)
    data_match = re.search(r"data:\s*\[(\d+),\s*(\d+)\]", source)
    labels = re.findall(r"'([^']+)'", labels_match.group(1))
    values = [int(x) for x in data_match.groups()]
    if labels != ['Liquidez para THORChain', 'Infraestructura xolosArmy (1%)'] or values != [99, 1]:
        raise ValueError("Unexpected chart dataset; manual review required")
    figure = etree.Element("figure", {"id": "transparencyChart", "class": "editorial-data-chart"})
    meter = etree.SubElement(figure, "meter", {
        "min": "0", "max": "100", "value": "99",
        "aria-label": "Liquidez para THORChain: 99%; Infraestructura xolosArmy (1%): 1%",
    })
    meter.text = "99% / 1%"
    table = etree.SubElement(figure, "table")
    etree.SubElement(table, "caption").text = "Distribución de Transparencia (1% Infraestructura)"
    head = etree.SubElement(etree.SubElement(table, "thead"), "tr")
    etree.SubElement(head, "th", {"scope": "col"}).text = "Concepto"
    etree.SubElement(head, "th", {"scope": "col"}).text = "Porcentaje"
    body = etree.SubElement(table, "tbody")
    for label, value in zip(labels, values):
        row = etree.SubElement(body, "tr")
        etree.SubElement(row, "th", {"scope": "row"}).text = label
        etree.SubElement(row, "td").text = f"{value}%"
    chart.getparent().replace(chart, figure)
    # A legacy CTA had no link, form action or event handler. Keep its wording
    # as a paragraph instead of presenting a non-working control to readers.
    for button in root.xpath(".//button[not(@onclick)]"):
        button.tag = "p"
        button.set("class", "legacy-action-label")
    return {"steps": entries, "chart": {"labels": labels, "values": values},
            "changes": ["Chart.js doughnut replaced by native meter and exact-data table",
                        "Three JS-controlled steps replaced by native details/summary",
                        "Inactive Apoyar a xolosArmy button retained as plain text"]}


def extract(source_path, relative_path):
    source = source_path.read_text(encoding="utf-8")
    document = html.document_fromstring(source)
    root = document.find("body")
    if root is None:
        raise ValueError(f"No parseable body: {relative_path}")
    background_images = []
    for style in document.xpath("//style"):
        for selector, rule in re.findall(r"([^{}]+)\{([^{}]+)\}", style.text_content()):
            urls = re.findall(r"url\(['\"]?([^)'\"]+)['\"]?\)", rule)
            if not urls:
                continue
            selector = re.sub(r"/\*.*?\*/", "", selector, flags=re.S).strip()
            # Baseline contains just these two audited background selectors.
            if selector not in (".hero::before", ".chronology-analysis-hero"):
                raise ValueError(f"Unreviewed CSS image selector: {relative_path}: {selector}")
            class_name = selector.split("::")[0][1:]
            targets = root.xpath(".//*[contains(concat(' ',normalize-space(@class),' '), $class)]",
                                 **{"class": " " + class_name + " "})
            if len(targets) != 1 or len(urls) != 1:
                raise ValueError(f"Ambiguous CSS image: {relative_path}: {selector}")
            # The old CSS image had no textual alternative and was decorative.
            # Preserve that status rather than inventing a scene description.
            image = html.Element("img", src=urls[0], alt="", role="presentation",
                                 **{"class": "editorial-legacy-image"})
            targets[0].insert(0, image)
            background_images.append({"selector": selector, "src": urls[0], "alt": ""})
    removed = []
    source_scripts = []
    for element in list(root.xpath(".//script|.//style|.//link")):
        source_scripts.append({"tag": element.tag, "src": element.get("src"),
                               "type": element.get("type"),
                               "text_sha256": digest(element.text_content())})
        drop(element)
    # This list was checked against every one of the 43 baseline documents.
    # None of the removed headers contains an article headline. All article
    # headers (including those outside <main>) and substantive asides remain.
    shell_nodes = root.xpath(".//header[not(.//h1)]|.//nav|.//*[contains(concat(' ',normalize-space(@class),' '),' scanline ')]")
    shell_nodes += root.xpath(".//footer[not(@class='article-conclusion') and not(@class='mag-metadata-footer') and not(@class='article-footer')]")
    shell_nodes += root.xpath(".//div[contains(concat(' ',normalize-space(@class),' '),' footer ')]")
    shell_ids = {id(n) for n in shell_nodes}
    shell_nodes = [n for n in shell_nodes if not any(id(a) in shell_ids for a in n.iterancestors())]
    translations = []
    for node in shell_nodes:
        for button in node.xpath(".//button[@onclick]"):
            match = re.fullmatch(r"window\.location\.href='([^']+)'", button.get("onclick"))
            if match:
                link = html.Element("a", href=match.group(1))
                link.text = normalized(button.text_content())
                translations.append(link)
        for link in node.xpath(".//a[@href]"):
            href = link.get("href")
            if href.endswith(".html") and not href.endswith("index.html"):
                translations.append(copy.deepcopy(link))
        removed.append({"tag": node.tag, "class": node.get("class"),
                        "text": normalized(node.text_content()),
                        "links": [{"href": a.get("href"), "text": normalized(a.text_content())}
                                  for a in node.xpath(".//a[@href]")]})
        drop(node)
    if translations:
        nav = html.Element("nav", {"class": "article-translations", "aria-label": "Versiones del artículo"})
        for link in translations:
            nav.append(link)
        root.insert(0, nav)
    # Assertions use the full editorial body BEFORE any technical adaptation.
    # This also captures article headers outside main and footers with metadata.
    baseline = snapshot(root)
    dynamic = None
    if str(relative_path) == "analisis/teyolia-direct-to-pool.html":
        dynamic = materialize_teyolia(root, source)
    dropped_styles = 0
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        if element.tag in ("main", "article"):
            element.tag = "div"
        if element.tag == "footer":
            # Article conclusions and article-specific metadata remain intact.
            element.tag = "section"
        if element.get("style") is not None:
            del element.attrib["style"]
            dropped_styles += 1
        for attr in list(element.attrib):
            if attr.lower().startswith("on"):
                raise ValueError(f"Unmigrated event handler {relative_path}: {attr}")
    for comment in root.xpath(".//comment()"):
        drop(comment)
    normalized_whitespace_nodes = normalize_layout_whitespace(root)
    # Use children of body as the fragment; generated pages own their landmark.
    fragment = (root.text or "") + "".join(html.tostring(e, encoding="unicode", method="html") for e in root)
    fragment = fragment.strip() + "\n"
    output_snapshot = snapshot(root)
    baseline_segments = Counter(baseline["text_segments"])
    output_segments = Counter(output_snapshot["text_segments"])
    missing = list((baseline_segments - output_segments).elements())
    # Summary tag normalization and materialization may group a node's words
    # differently, but every original nonempty segment must still be present.
    output_text = " ".join(output_snapshot["text_segments"])
    missing = [segment for segment in missing if segment not in output_text]
    if missing:
        raise ValueError(f"Lost original content in {relative_path}: {missing}")
    for field in ("links", "images", "embeds", "code"):
        if baseline[field] != output_snapshot[field]:
            raise ValueError(f"Unexpected {field} change in {relative_path}")
    duplicate_ids = [i for i, count in Counter(output_snapshot["ids"]).items() if count > 1]
    return fragment, {
        "url": "/" + str(relative_path),
        "fragment": "content/" + str(relative_path),
        "baseline_file_sha256": digest(source),
        "fragment_sha256": digest(fragment),
        "baseline_editorial": baseline,
        "extracted_editorial": output_snapshot,
        "removed_site_shell": removed,
        "removed_style_script_nodes": source_scripts,
        "removed_inline_style_count": dropped_styles,
        "normalized_layout_whitespace_nodes_count": normalized_whitespace_nodes,
        "background_images_materialized": background_images,
        "dynamic_content_materialized": dynamic,
        "duplicate_ids": duplicate_ids,
        "preservation": {"original_text_segments_present": True, "links_unchanged": True,
                         "images_unchanged": True, "embeds_unchanged": True, "code_unchanged": True},
    }


def metadata_tokens(value):
    """Tokens for metadata only: accents/case/date display and two translations."""
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    value = value.replace("technical analysis", "analisis tecnico")
    value = re.sub(r"\bnews\b", "noticia", value)
    months = {name: str(i) for i, names in enumerate([
        ("enero", "ene"), ("febrero", "feb"), ("marzo", "mar"), ("abril", "abr"),
        ("mayo", "may"), ("junio", "jun"), ("julio", "jul"), ("agosto", "ago"),
        ("septiembre", "sept", "sep"), ("octubre", "oct"), ("noviembre", "nov"),
        ("diciembre", "dic")], start=1) for name in names}
    tokens = re.findall(r"[a-z]+|\d+", value)
    return [months.get(token, str(int(token)) if token.isdigit() else token) for token in tokens]


def validate_metadata_replacements(output, article, catalog_article, rules, header):
    """Authorize only matched metadata whose meaning is in the new header.

    The allowlist alone is insufficient: each XPath and expectedText must
    match the immutable fragment, each declared catalogue field must exist,
    and the corresponding structured header slot must show its value.
    """
    path = output / article["fragment"]
    source = path.read_text(encoding="utf-8")
    if digest(source) != article["fragment_sha256"]:
        return article["extracted_editorial"]["text_segments"], [{"error": "Fragment hash differs from preservation manifest"}], []
    fragment = html.fragment_fromstring(source, create_parent="div")
    errors, accepted = [], []
    structural = set(metadata_tokens("Por By Autor Género Fecha de publicación Lectura minutos min Actualización actualizado"))
    allowed_fields = {"genre", "originalGenreLabel", "section", "topics", "tags", "author", "publishedAt", "updatedAt", "readingMinutes"}
    def class_nodes(name):
        return header.xpath(".//*[contains(concat(' ',normalize-space(@class),' '), $class)]", **{"class": " " + name + " "})
    for rule in rules:
        issues = []
        matches = fragment.xpath(rule["xpath"])
        if len(matches) != 1 or normalized(matches[0].text_content()) != rule["expectedText"]:
            errors.append({"expectedText": rule["expectedText"], "error": "XPath/expectedText does not uniquely match original fragment"})
            continue
        node = matches[0]
        if node.xpath(".//a|.//img|.//iframe|.//pre|.//code|.//table|.//blockquote|.//h1|.//h2|.//h3|.//h4|.//h5|.//h6"):
            issues.append("Removal contains non-metadata content")
        available_tokens = set()
        for field in rule.get("fields", []):
            value = catalog_article.get(field)
            if field not in allowed_fields or value is None or value == [] or value == "":
                issues.append(f"Missing or unauthorized catalogue field: {field}")
                continue
            if field == "author":
                values = [value["name"]]
                shown = [normalized(e.text_content()) for e in header.xpath(".//a[@rel='author']")]
            elif field in ("topics", "tags"):
                values = [v["label"] if isinstance(v, dict) else v for v in value]
                shown = [normalized(e.text_content()) for container in class_nodes("tags") for e in container.xpath(".//a")]
            elif field in ("publishedAt", "updatedAt"):
                values = [value[:10]]
                shown = [e.get("datetime", "")[:10] for e in header.xpath(".//time[@datetime]") if normalized(e.text_content())]
            elif field == "readingMinutes":
                values = [str(value)]
                shown = [normalized(" ".join(e.itertext())) for e in class_nodes("story-meta")]
                if not any(re.search(rf"\b{value}\s+min\b", text) for text in shown):
                    issues.append("Reading time absent from header metadata")
            else:
                values = [value]
                css_class = {"genre": "genre", "originalGenreLabel": "original-label", "section": "section-label"}[field]
                shown = [normalized(e.text_content()) for e in class_nodes(css_class)]
            for candidate in values:
                tokens = metadata_tokens(candidate)
                available_tokens.update(tokens)
                if not any(" ".join(tokens) in " ".join(metadata_tokens(display)) for display in shown):
                    issues.append(f"Catalogue {field} value missing from its header slot: {candidate}")
        source_tokens = set(metadata_tokens(" ".join(node.itertext())))
        unexplained = source_tokens - available_tokens - structural
        if unexplained:
            issues.append("Original metadata meaning not covered by declared catalogue fields: " + ", ".join(sorted(unexplained)))
        if not rule.get("fields"):
            issues.append("No explicit catalogue fields")
        if issues:
            errors.append({"expectedText": rule["expectedText"], "errors": issues})
            continue
        accepted.append({"expectedText": rule["expectedText"], "fields": rule["fields"], "verified": True})
        drop(node)
    # Removing only validated source nodes leaves every other original text
    # segment under the same strict, verbatim preservation check as before.
    return snapshot(fragment)["text_segments"], errors, accepted


def verify_generated(output):
    """Check the complete rendered documents, allowing documented migrations."""
    manifest = json.loads((output / "editorial/preservation.json").read_text(encoding="utf-8"))
    media = json.loads((output / "editorial/media-map.json").read_text(encoding="utf-8"))
    catalog = json.loads((output / "editorial/catalog.json").read_text(encoding="utf-8"))
    catalog_by_url = {a["url"]: a for a in catalog["articles"]}
    removals_path = output / "editorial/metadata-removals.json"
    removals = json.loads(removals_path.read_text(encoding="utf-8")) if removals_path.exists() else {}
    unavailable_backgrounds = {
        "https://images.unsplash.com/photo-1614064641913-a5f10665f8df?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1639762681485-074b7f4ec651?auto=format&fit=crop&w=1600&q=80",
    }

    def canonical_ref(value, page):
        url = urlsplit(urljoin("https://magazine.ecash.mx" + page, value))
        path = unquote(url.path)
        if url.netloc == "magazine.ecash.mx" and path == "/archivo.html":
            path = "/blog/index.html"
        if page == "/reportajes/tonalli-faucet-ecash-mexico.html" and value == "./index.html":
            path = "/blog/index.html"
        return urlunsplit((url.scheme, url.netloc, path, url.query, url.fragment))

    results = []
    for article in manifest["articles"]:
        page = article["url"]
        document = html.document_fromstring((output / page.lstrip("/")).read_text(encoding="utf-8"))
        roots = document.xpath("//main")
        if len(roots) != 1:
            results.append({"url": page, "pass": False, "missing": {"main_landmark": len(roots)}})
            continue
        body = roots[0]
        for element in body.xpath(".//script|.//style"):
            drop(element)
        text = normalized(" ".join(body.itertext()))
        # Extracted snapshot includes ALL original segments plus text that used
        # to be present exclusively inside the Teyolia JavaScript dataset.
        expected = article["extracted_editorial"]
        headers = body.xpath(".//header[contains(concat(' ',normalize-space(@class),' '),' article-header ')]")
        metadata_errors, metadata_accepted = [], []
        expected_text = expected["text_segments"]
        if removals.get(page):
            if len(headers) != 1:
                metadata_errors.append({"error": "Expected one structured article header"})
            else:
                expected_text, metadata_errors, metadata_accepted = validate_metadata_replacements(
                    output, article, catalog_by_url[page], removals[page], headers[0])
        missing_text = [s for s in expected_text if s not in text]
        actual_code = [e.text_content() for e in body.xpath(".//pre|.//code[not(ancestor::pre)]")]
        missing_code = [e for e in expected["code"] if e["text"] not in actual_code]
        actual_links = {(canonical_ref(a.get("href"), page), normalized(a.text_content()))
                        for a in body.xpath(".//a[@href]")}
        missing_links = [a for a in expected["links"]
                         if (canonical_ref(a["href"], page), a["text"]) not in actual_links]
        actual_images = {(canonical_ref(i.get("src"), page), i.get("alt"))
                         for i in body.xpath(".//img[@src]")}
        missing_images, exceptions = [], []
        css_images = {i["src"] for i in article.get("background_images_materialized", [])}
        for image in expected["images"]:
            if image["src"] in unavailable_backgrounds and image["src"] in css_images and image.get("alt") == "":
                exceptions.append({"type": "unavailable_decorative_background", "source": image["src"],
                                   "omitted": (canonical_ref(image["src"], page), "") not in actual_images})
                continue
            mapped = media.get(image["src"], {}).get("src", image["src"])
            if (canonical_ref(mapped, page), image.get("alt")) not in actual_images:
                missing_images.append({"original": image, "expected_src": mapped})
        actual_embeds = {(e.tag, e.get("src"), e.get("title"))
                         for e in body.xpath(".//iframe|.//video|.//audio|.//source")}
        missing_embeds = [e for e in expected["embeds"]
                          if (e["tag"], e["src"], e.get("title")) not in actual_embeds]
        actual_ids = {e.get("id") for e in body.xpath(".//*[@id]")}
        missing_ids = [i for i in expected["ids"] if i not in actual_ids]
        failures = {"text": missing_text, "code": missing_code, "links": missing_links,
                    "images": missing_images, "embeds": missing_embeds, "ids": missing_ids,
                    "metadata_replacements": metadata_errors}
        results.append({"url": page, "pass": not any(failures.values()),
                        "missing": {k: v for k, v in failures.items() if v}, "exceptions": exceptions,
                        "verified_metadata_replacements": metadata_accepted})
    report = {"article_count": len(results), "passed": sum(r["pass"] for r in results),
              "failed": sum(not r["pass"] for r in results),
              "verified_metadata_replacements": sum(len(r.get("verified_metadata_replacements", [])) for r in results),
              "articles": results}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["failed"] or report["article_count"] != 43 else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, default=Path.cwd())
    parser.add_argument("--verify-generated", action="store_true", help="Verify generated pages against preservation manifest")
    args = parser.parse_args()
    if args.verify_generated:
        raise SystemExit(verify_generated(args.output))
    if args.source is None:
        parser.error("--source is required for extraction")
    if args.source.resolve() == args.output.resolve():
        parser.error("Source must be a separate immutable baseline")
    entries = []
    paths = sorted(p for p in args.source.rglob("*.html") if p.name != "index.html" and ".git" not in p.parts)
    if len(paths) != 43:
        raise ValueError(f"Expected 43 baseline articles, found {len(paths)}")
    for path in paths:
        relative = path.relative_to(args.source)
        fragment, entry = extract(path, relative)
        target = args.output / "content" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(fragment, encoding="utf-8")
        entries.append(entry)
    manifest = {"version": 1, "article_count": len(entries),
                "purpose": "Immutable pre-redesign editorial content and extraction preservation manifest",
                "articles": entries}
    manifest_path = args.output / "editorial/preservation.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"articles": len(entries), "all_preserved": True,
                      "duplicate_ids": {e["url"]: e["duplicate_ids"] for e in entries if e["duplicate_ids"]}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
