#!/usr/bin/env python3
"""Verify source fidelity, whole-book coverage and published local links."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import markdown
from bs4 import BeautifulSoup

from build import ROOT, OUT, source_text, MARKED


def main():
    manifest = json.loads((ROOT / 'website-build-manifest.json').read_text())
    base = manifest['base_path']
    soups = {}
    issues = []
    for path in OUT.rglob('*.html'):
        soup = BeautifulSoup(path.read_text(), 'html.parser')
        soups[path.resolve()] = soup
        ids = [element['id'] for element in soup.select('[id]')]
        if len(ids) != len(set(ids)):
            issues.append(f'Duplicate anchors: {path.relative_to(OUT)}')
        if '@@' in path.read_text():
            issues.append(f'Unresolved template fields: {path.relative_to(OUT)}')
        if len(soup.find_all('h1')) != 1:
            issues.append(f'Expected one page title: {path.relative_to(OUT)}')
    checked_links = 0
    for path, soup in soups.items():
        for element in soup.select('a[href], img[src], script[src], link[href]'):
            url = element.get('href', element.get('src'))
            split = urlsplit(url)
            if split.scheme or url.startswith('//'):
                continue
            if split.path.startswith(base):
                target = OUT / unquote(split.path[len(base):])
            elif not split.path:
                target = path
            else:
                target = path.parent / unquote(split.path)
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                issues.append(f'Missing local target: {path.relative_to(OUT)} -> {url}')
            elif split.fragment and target.suffix == '.html':
                target_soup = soups.get(target.resolve())
                if not target_soup or not target_soup.find(id=unquote(split.fragment)):
                    issues.append(f'Missing anchor: {path.relative_to(OUT)} -> {url}')
            checked_links += 1
    counts = {}
    for lang in ['zh', 'en']:
        pages = [p for p in manifest['pages'] if p['language'] == lang]
        chapters = [p for p in pages if p['slug'].startswith('chapter-')]
        tools = [p for p in pages if p['slug'].startswith('tool-')]
        figures = sum(p['figures'] for p in chapters)
        tables = sum(p['tables'] for p in pages)
        assert len(chapters) == len(tools) == 18 and figures == 247
        assert tables == 125, (lang, tables)
        counts[lang] = dict(chapters=len(chapters), worksheets=len(tools), figures=figures, tables=tables)
    for page in manifest['pages']:
        if not page['source']:
            continue
        source = ROOT / page['source']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == page['source_sha256']
        text = re.sub(r'^# .+\n?', '', source_text(source), count=1, flags=re.M)
        original = BeautifulSoup(markdown.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists', 'toc']), 'html.parser')
        target = (OUT / page['language'] / page['slug'] / 'index.html').resolve()
        actual = BeautifulSoup(str(soups[target].select_one('.prose')), 'html.parser')
        for hint in actual.select('.table-hint'):
            hint.decompose()
        compact = lambda soup: re.sub(r'\s+', '', soup.get_text())
        if compact(original) != compact(actual):
            issues.append(f'Text differs from source: {page["source"]}')
        original_tables = [[cell.get_text() for cell in table.select('th, td')] for table in original.select('table')]
        actual_tables = [[cell.get_text() for cell in table.select('th, td')] for table in actual.select('table')]
        if original_tables != actual_tables:
            issues.append(f'Table cells differ: {page["source"]}')
        if [img.get('alt') for img in original.select('img')] != [img.get('alt') for img in actual.select('img')]:
            issues.append(f'Figure captions differ: {page["source"]}')
    marked = [a for a in manifest['assets'] if a['marked_english']]
    assert {Path(a['path']).stem for a in marked} == MARKED and len(marked) == 8
    for asset in manifest['assets']:
        assert hashlib.sha256((OUT / asset['path']).read_bytes()).hexdigest() == asset['sha256']
    # Only generator-owned assets and approved book image files belong in the artifact.
    allowed = {'.html', '.png', '.svg', '.jpg', '.jpeg', '.css', '.js', '.json', '.xml'}
    for path in OUT.rglob('*'):
        if path.is_file() and path.name != '.nojekyll' and path.suffix not in allowed:
            issues.append(f'Unexpected published file: {path.relative_to(OUT)}')
    if issues:
        raise SystemExit('\n'.join(issues))
    print(json.dumps(dict(status='pass', html_pages=len(soups), local_links=checked_links, source_pages=sum(bool(p['source']) for p in manifest['pages']), editions=counts, marked_pngs=8, all_copied_assets_byte_identical=True), ensure_ascii=False))


if __name__ == '__main__':
    main()
