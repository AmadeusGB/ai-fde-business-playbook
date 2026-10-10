#!/usr/bin/env python3
"""Build both reading editions without changing any book source or figure."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import struct
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
import xml.etree.ElementTree as ET

import markdown
from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
REPO = 'https://github.com/AmadeusGB/ai-fde-business-playbook'
ORIGIN = 'https://amadeusgb.github.io'
RELEASE = REPO + '/releases/tag/en-v1.1-20261010'
MARKED = {'fig-01-05', 'fig-03-03', 'fig-05-03', 'fig-07-03', 'fig-09-04', 'fig-12-03', 'fig-15-04', 'fig-18-05'}
PARTS = [
    (1, 3, '看懂问题', 'Understanding the problem'),
    (4, 7, '作出投入决定', 'Deciding what to invest'),
    (8, 11, '完成项目交付', 'Delivering the project'),
    (12, 13, '判断经营结果', 'Assessing business outcomes'),
    (14, 18, '建立持续落地的组织能力', 'Building lasting delivery capability'),
]
LABELS = {
    'zh': dict(title='把AI带进经营', brand='把AI带进经营', author='郭斌 著', home='首页', contents='全书目录', menu='目录', search='搜索', guide='阅读说明', author_page='作者简介', rights='版权与分享', downloads='下载电子版', tools='十八份行动工具', sections='本页目录', skip='跳到正文', previous='上一章', next='下一章', tool='使用本章工具', chapter='返回对应章节', table_hint='宽表可左右滑动查看。', figure='打开原图', description='从业务流程到经营结果的企业AI落地指南。五部十八章，附十八份行动工具。', note='中文 v3.6 · 郭斌', source='查看源稿', part='第{n}部'),
    'en': dict(title='Bringing AI into Business Operations', brand='AI into Business', author='By Guo Bin', home='Home', contents='Contents', menu='Contents', search='Search', guide='Reading guide', author_page='About the author', rights='Copyright & sharing', downloads='Downloads', tools='18 worksheets', sections='On this page', skip='Skip to content', previous='Previous chapter', next='Next chapter', tool='Open this chapter’s worksheet', chapter='Back to the chapter', table_hint='Scroll horizontally to read wide tables.', figure='Open original figure', description='A practical guide to enterprise AI: from business workflows to business results. 18 chapters and 18 worksheets.', note='English edition · Guo Bin', source='View source', part='Part {n}'),
}
PAGES: dict[tuple[str, str], dict] = {}
SOURCE_MAP: dict[Path, tuple[str, str]] = {}
ASSETS: dict[str, dict] = {}
BASE = '/'


def esc(value):
    return html.escape(str(value), quote=True)


def site_url(lang='', slug=''):
    return BASE + (lang + '/' if lang else '') + (slug + '/' if slug else '')


def source_text(path):
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'\A---\n.*?\n---\n', '', text, count=1, flags=re.S)
    return re.sub(r'<!--.*?-->', '', text, flags=re.S).strip()


def register(lang, slug, path=None, title=None, number=0, kind='support'):
    text = source_text(path) if path else ''
    title = title or re.search(r'^# (.+)$', text, re.M)[1]
    row = dict(lang=lang, slug=slug, path=path, title=title, number=number, kind=kind, text=text)
    PAGES[lang, slug] = row
    if path:
        SOURCE_MAP[path.resolve()] = (lang, slug)


def discover():
    for lang in ['zh', 'en']:
        root = ROOT / ('book/en' if lang == 'en' else 'book')
        for path in sorted((root / 'chapters').glob('[0-9][0-9]-*.md')):
            n = int(path.name[:2]); register(lang, f'chapter-{n:02}', path, number=n, kind='chapter')
        tools = root / ('appendices' if lang == 'en' else 'tools')
        for path in sorted(tools.glob('[0-9][0-9]-*.md')):
            n = int(path.name[:2]); register(lang, f'tool-{n:02}', path, number=n, kind='tool')
        support = {'guide': 'frontmatter/reading_guide.md' if lang == 'en' else 'reading-guide.md', 'author': 'frontmatter/author_bio.md' if lang == 'en' else 'author.md', 'rights': 'frontmatter/copyright_and_sharing.md' if lang == 'en' else 'copyright-and-sharing.md'}
        for slug, relative in support.items():
            register(lang, slug, root / relative)
        for slug, label in [('', 'contents'), ('downloads', 'downloads'), ('search', 'search')]:
            register(lang, slug, title=LABELS[lang][label], kind=slug or 'contents')
        assert sum(p['kind'] == 'chapter' for p in PAGES.values() if p['lang'] == lang) == 18
        assert sum(p['kind'] == 'tool' for p in PAGES.values() if p['lang'] == lang) == 18


def copy_asset(source):
    source = source.resolve()
    relative = source.relative_to(ROOT).as_posix()
    if not source.is_file():
        raise FileNotFoundError(relative)
    if source.suffix.lower() not in {'.png', '.svg', '.jpg', '.jpeg'}:
        raise ValueError(f'Unexpected content asset: {relative}')
    target = OUT / relative
    if relative not in ASSETS:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        ASSETS[relative] = dict(path=relative, sha256=digest, bytes=source.stat().st_size, marked_english='book/en/figures/' in relative and source.stem in MARKED and source.suffix == '.png')
    return BASE + quote(relative, safe='/')


def image_size(path):
    if path.suffix == '.png':
        with path.open('rb') as f:
            header = f.read(24)
        return struct.unpack('>II', header[16:24])
    if path.suffix == '.svg':
        svg = ET.parse(path).getroot()
        box = re.split(r'[ ,]+', svg.attrib.get('viewBox', '').strip())
        if len(box) == 4:
            return round(float(box[2])), round(float(box[3]))
        try:
            return round(float(svg.attrib['width'])), round(float(svg.attrib['height']))
        except (KeyError, ValueError):
            return None
    return None


def linkify(soup):
    for node in list(soup.find_all(string=True)):
        if node.parent.name in {'a', 'script', 'style', 'code', 'pre'}:
            continue
        text = str(node)
        parts = []; end = 0
        for match in re.finditer(r'https?://[^\s<>]+', text):
            url = match[0].rstrip('。,，；;、）)]')
            if match.start() > end:
                parts.append(NavigableString(text[end:match.start()]))
            a = soup.new_tag('a', href=url); a.string = url; parts.append(a)
            end = match.start() + len(url)
        if parts:
            parts.append(NavigableString(text[end:])); node.replace_with(*parts)


def render_markdown(row):
    lang = row['lang']; labels = LABELS[lang]
    text = re.sub(r'^# .+\n?', '', row['text'], count=1, flags=re.M)
    rendered = markdown.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists', 'toc'], extension_configs={'toc': {'permalink': False}}, output_format='html')
    soup = BeautifulSoup(rendered, 'html.parser')
    for image in list(soup.find_all('img')):
        source = (row['path'].parent / unquote(image['src'])).resolve()
        if lang == 'en' and source.stem not in MARKED and source.with_suffix('.svg').exists():
            source = source.with_suffix('.svg')
        image['src'] = copy_asset(source)
        image['loading'] = 'lazy'; image['decoding'] = 'async'
        size = image_size(source)
        if size:
            image['width'], image['height'] = map(str, size)
        link = soup.new_tag('a', href=image['src'], target='_blank', rel='noopener', title=labels['figure'], **{'class': 'figure-link'})
        image.wrap(link)
        paragraph = link.parent
        if paragraph.name == 'p':
            paragraph.name = 'figure'; paragraph['class'] = 'book-figure'
            caption = paragraph.find_next_sibling('p')
            if caption and re.match(r'^(图\d|Figure \d)', caption.get_text()):
                caption['class'] = 'figure-caption'
    for table in list(soup.find_all('table')):
        caption = table.find_previous_sibling('p')
        label = (caption.get_text(' ', strip=True) if caption else row['title'])[:150]
        wrapper = soup.new_tag('div', role='region', tabindex='0', **{'class': 'table-scroll', 'aria-label': label})
        table.wrap(wrapper)
        hint = soup.new_tag('p', **{'class': 'table-hint'}); hint.string = labels['table_hint']; wrapper.insert_after(hint)
        for th in table.find_all('th'):
            th['scope'] = 'col'
    for a in soup.find_all('a', href=True):
        href = a['href']; parsed = urlsplit(href)
        if parsed.scheme or href.startswith(('#', '//', BASE + 'book/')):
            continue
        target = (row['path'].parent / unquote(parsed.path)).resolve()
        if target in SOURCE_MAP:
            target_lang, slug = SOURCE_MAP[target]; a['href'] = site_url(target_lang, slug)
            if parsed.fragment:
                a['href'] += '#' + parsed.fragment
        else:
            relative = target.relative_to(ROOT).as_posix()
            a['href'] = REPO + '/blob/main/' + quote(relative, safe='/') + ('#' + parsed.fragment if parsed.fragment else '')
    headings = []
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        if not heading.get('id'):
            continue
        title = heading.get_text(' ', strip=True)
        link = soup.new_tag('a', href='#' + quote(heading['id']), **{'class': 'heading-link'})
        heading.wrap(link)
        # Keep headings as block elements: put the link inside the heading.
        link.unwrap()
        contents = list(heading.contents)
        inner = soup.new_tag('a', href='#' + quote(heading['id']), **{'class': 'heading-link'})
        for child in contents:
            inner.append(child.extract())
        heading.append(inner)
        if heading.name == 'h2':
            headings.append(dict(id=heading['id'], title=title))
    if row['kind'] == 'chapter':
        for p in soup.find_all('p'):
            match = re.match(r'^\[(\d+)\]\s', p.get_text())
            if match:
                p['id'] = f'note-{match[1]}'; p['class'] = 'source-note'
        for node in list(soup.find_all(string=True)):
            if node.parent.name in {'a', 'code', 'pre'} or node.find_parent(class_='source-note'):
                continue
            value = str(node); parts = []; end = 0
            for match in re.finditer(r'\[(\d+)\]', value):
                if not soup.find(id=f'note-{match[1]}'):
                    continue
                parts.append(NavigableString(value[end:match.start()]))
                a = soup.new_tag('a', href=f'#note-{match[1]}', **{'class': 'note-ref'}); a.string = match[0]; parts.append(a); end = match.end()
            if parts:
                parts.append(NavigableString(value[end:])); node.replace_with(*parts)
    linkify(soup)
    row['headings'] = headings
    row['figure_count'] = len(soup.find_all('img'))
    row['table_count'] = len(soup.find_all('table'))
    row['plain_text'] = soup.get_text(' ', strip=True)
    return str(soup)


def nav(lang, current):
    labels = LABELS[lang]; pieces = ['<nav class="book-nav" aria-label="' + esc(labels['contents']) + '"><ul>']
    def link(slug, title):
        active = ' aria-current="page"' if slug == current else ''
        return f'<li><a href="{site_url(lang, slug)}"{active}>{title}</a></li>'
    for slug, label in [('', 'contents'), ('guide', 'guide'), ('search', 'search')]:
        pieces.append(link(slug, esc(labels[label])))
    pieces.append('</ul>')
    for part, (start, end, zh, en) in enumerate(PARTS, 1):
        pieces.append(f'<h2>{esc(labels["part"].format(n=part))} · {esc(en if lang == "en" else zh)}</h2><ul>')
        for n in range(start, end + 1):
            row = PAGES[lang, f'chapter-{n:02}']; short = re.sub(r'^(第\d+章|Chapter \d+)\s+', '', row['title'])
            pieces.append(link(row['slug'], f'<span class="nav-number">{n}</span>{esc(short)}'))
        pieces.append('</ul>')
    pieces.append(f'<h2>{esc(labels["tools"])}</h2><ul>')
    for n in range(1, 19):
        row = PAGES[lang, f'tool-{n:02}']; title = re.sub(r'^(Worksheet|Tool) \d+\s*[|:—–-]?\s*', '', row['title'])
        pieces.append(link(row['slug'], f'<span class="nav-number">{n:02}</span>{esc(title)}'))
    pieces.append('</ul><ul>')
    for slug, label in [('downloads', 'downloads'), ('author', 'author_page'), ('rights', 'rights')]:
        pieces.append(link(slug, esc(labels[label])))
    pieces.append('</ul></nav>')
    return ''.join(pieces)


def downloads(lang):
    if lang == 'zh':
        return '<div class="downloads"><p>中文 v3.6。分页、注释和图文编排以 PDF / Word 为准。</p><ul>' + ''.join(f'<li><a href="{REPO}/raw/refs/heads/main/edition/v3.6/{quote("把AI带进经营." + ext)}">{name}</a></li>' for ext, name in [('pdf', '下载中文 PDF'), ('docx', '下载中文 Word')]) + f'</ul><p>DOI：<a href="https://doi.org/10.5281/zenodo.22827116">10.5281/zenodo.22827116</a></p><p><a href="{site_url("zh", "rights")}">版权与分享说明</a></p></div>'
    asset_base = REPO + '/releases/download/en-v1.1-20261010/'
    files = [('Bringing-AI-into-Business-Operations.pdf', 'English PDF', '454 pages'), ('Bringing-AI-into-Business-Operations.docx', 'English Word document', 'Editable document'), ('Bringing-AI-into-Business-Operations.html', 'Offline HTML', 'Single-file reading edition'), ('Bringing-AI-into-Business-Operations-English-Sources.zip', 'English source package', 'Source text and figures')]
    return '<div class="downloads"><p>Edition en-full-1.1-r2-steg · October 10, 2026.</p><ul>' + ''.join(f'<li><a href="{asset_base}{name}">{title}</a><small>{detail}</small></li>' for name, title, detail in files) + f'</ul><p><a href="{RELEASE}">Release notes and SHA-256 checksums</a></p><p>The English edition has completed AI-assisted translation and production review. Native English editorial review remains pending.</p><p><a href="{site_url("en", "rights")}">Copyright and sharing terms</a></p></div>'


def contents(lang):
    en = lang == 'en'; labels = LABELS[lang]
    cover = copy_asset(ROOT / ('book/en/frontmatter/front-cover.png' if en else 'book/cover/front-cover.png'))
    introduction = 'A practical guide to enterprise AI: from business workflows to business results. Five parts, 18 chapters, and 18 worksheets. Start at Chapter 1, or choose the decision you are working on.' if en else '从业务流程到经营结果的企业AI落地指南。全书五部、十八章，附十八份行动工具。首次阅读可从第1章开始；带着具体问题查阅时，可直接选择章节。'
    out = [f'<div class="edition-intro"><img class="edition-cover" src="{cover}" alt="{esc(labels["title"])}" width="2040" height="2880"><p>{esc(introduction)}</p><p>{esc(labels["author"])}</p><a class="resume-reading" href="{site_url(lang, "chapter-01")}"></a><p><a href="{site_url(lang, "chapter-01")}">{"Start reading Chapter 1" if en else "开始阅读第1章"}</a> · <a href="{site_url(lang, "downloads")}">{esc(labels["downloads"])}</a></p></div><div class="contents">']
    for part, (start, end, zh, english) in enumerate(PARTS, 1):
        out.append(f'<h2>{esc(labels["part"].format(n=part))} · {esc(english if en else zh)}</h2><ul>')
        for n in range(start, end + 1):
            row = PAGES[lang, f'chapter-{n:02}']; title = re.sub(r'^(第\d+章|Chapter \d+)\s+', '', row['title'])
            out.append(f'<li><a href="{site_url(lang, row["slug"])}"><span class="nav-number">{n}</span>{esc(title)}</a></li>')
        out.append('</ul>')
    out.append(f'<h2>{esc(labels["tools"])}</h2><ul>')
    for n in range(1, 19):
        row = PAGES[lang, f'tool-{n:02}']; out.append(f'<li><a href="{site_url(lang, row["slug"])}"><span class="nav-number">{n:02}</span>{esc(row["title"])}</a></li>')
    out.append('</ul></div>'); return ''.join(out)


def page_shell(lang, slug, title, content, landing=False):
    labels = LABELS[lang]; en = lang == 'en'; other = 'zh' if en else 'en'
    navigation = nav(lang, slug)
    menu_icon = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>'
    theme_icon = '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="6" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10 4a6 6 0 0 0 0 12z" fill="currentColor"/></svg>'
    header = f'<a class="brand" href="{site_url()}">{esc(labels["brand"])}</a><div class="header-actions"><a class="header-home" href="{site_url(lang)}">{esc(labels["contents"])}</a><a class="header-search" href="{site_url(lang, "search")}">{esc(labels["search"])}</a><a class="language-switch" href="{site_url(other, slug)}" lang="{other}" hreflang="{other}">{"中文" if en else "English"}</a><button class="theme-toggle" type="button" aria-label="{esc("Use dark theme" if en else "切换深色阅读")}">{theme_icon}</button>'
    if not landing:
        header += f'<details class="mobile-menu"><summary>{menu_icon}{esc(labels["menu"])}</summary><div class="mobile-nav-panel">{navigation}</div></details>'
    header += '</div>'
    if landing:
        layout = content
    else:
        row = PAGES[lang, slug]; context = ''
        if row['kind'] == 'chapter':
            context = ('Chapter ' if en else '第') + str(row['number']) + (' of 18' if en else '章 / 全18章')
        if row['kind'] == 'tool':
            context = ('Worksheet ' if en else '行动工具 ') + f'{row["number"]:02}'
        if not slug:
            title = labels['title']
        crumb = f'<nav class="breadcrumb" aria-label="{"Breadcrumb" if en else "当前位置"}"><a href="{site_url()}">{esc(labels["home"])}</a><span aria-hidden="true">/</span><a href="{site_url(lang)}">{"English" if en else "中文版"}</a></nav>'
        source_link = ''
        if row.get('path'):
            relative = row['path'].relative_to(ROOT).as_posix(); source_link = f'<a href="{REPO}/blob/main/{quote(relative, safe="/")}">{esc(labels["source"])}</a>'
        meta = ' · '.join(x for x in [esc(context), source_link] if x)
        article_header = f'<header class="article-header">{crumb}<h1>{esc(title)}</h1><p class="chapter-context">{meta}</p></header>'
        layout = f'<div class="reader-layout"><aside class="sidebar">{navigation}</aside><main id="main" class="article-shell" tabindex="-1"><div class="article-inner">{article_header}{content}</div></main></div>'
    review = 'AI-assisted translation and production review; native English editorial review pending.' if en else '中文 v3.6 · English edition available'
    footer = f'<span>{esc(labels["note"])}<br>{esc(review)}</span><span><a href="{site_url(lang, "rights")}">{esc(labels["rights"])}</a> · <a href="{site_url(lang, "downloads")}">{esc(labels["downloads"])}</a> · <a href="{REPO}">GitHub</a></span>'
    url = site_url() if landing else site_url(lang, slug)
    canonical = ORIGIN + url
    coversrc = BASE + ('book/en/frontmatter/front-cover.png' if en else 'book/cover/front-cover.png')
    alternates = ''.join(f'<link rel="alternate" hreflang="{code}" href="{ORIGIN}{site_url(code, slug)}">' for code in ['zh', 'en']) if not landing else ''
    values = dict(LANG='en' if en else 'zh-CN', CODE=lang, TITLE=esc(title + (' · ' + labels['title'] if title != labels['title'] else '')), DESCRIPTION=esc(labels['description']), CANONICAL=canonical, COVER=ORIGIN + coversrc, ALTERNATES=alternates, BASE=BASE, BODYCLASS='landing-page' if landing else 'reading-page', PAGE=slug, SKIP=esc(labels['skip']), HEADER=header, LAYOUT=layout, FOOTER=footer)
    template = (ROOT / 'website/index.html').read_text()
    return re.sub(r'@@([A-Z]+)@@', lambda match: str(values[match[1]]), template)


def render_page(row):
    lang = row['lang']; labels = LABELS[lang]; slug = row['slug']; en = lang == 'en'
    if row['path']:
        prose = render_markdown(row)
        sections = ''
        if row['headings']:
            sections = f'<details class="section-index" open><summary>{esc(labels["sections"])}</summary><ul>' + ''.join(f'<li><a href="#{quote(h["id"])}">{esc(h["title"])}</a></li>' for h in row['headings']) + '</ul></details>'
        content = sections + f'<div class="prose" lang="{lang}">{prose}</div>'
        n = row['number']
        if row['kind'] in {'chapter', 'tool'}:
            counterpart = f'tool-{n:02}' if row['kind'] == 'chapter' else f'chapter-{n:02}'
            content += f'<a class="worksheet-link" href="{site_url(lang, counterpart)}">{esc(labels["tool"] if row["kind"] == "chapter" else labels["chapter"])}</a>'
            sequence = 'chapter' if row['kind'] == 'chapter' else 'tool'
            content += '<nav class="page-navigation" aria-label="' + ('Page navigation' if en else '前后篇') + '">'
            for next_n, label in [(n - 1, labels['previous'] if sequence == 'chapter' else ('Previous worksheet' if en else '上一工具')), (n + 1, labels['next'] if sequence == 'chapter' else ('Next worksheet' if en else '下一工具'))]:
                if 1 <= next_n <= 18:
                    following = PAGES[lang, f'{sequence}-{next_n:02}']; content += f'<a href="{site_url(lang, following["slug"])}"><span>{esc(label)}</span>{esc(following["title"])}</a>'
            content += '</nav>'
    elif slug == 'downloads':
        content = downloads(lang)
    elif slug == 'search':
        prompt = 'Search chapters, worksheets and source notes' if en else '搜索章节、行动工具及资料注释'
        content = f'<form class="search-form" role="search" action="{site_url(lang, "search")}"><label class="skip-link" for="search-query">{esc(labels["search"])}</label><input id="search-query" name="q" type="search" placeholder="{esc(prompt)}" maxlength="160" autocomplete="off"><button type="submit">{esc(labels["search"])}</button></form><p class="search-status" role="status" aria-live="polite">{esc("Enter words to search this edition." if en else "输入关键词，搜索本语言全书。")}</p><ul class="search-results"></ul><noscript>{esc("Enable JavaScript to search, or use the chapter contents." if en else "搜索需要开启 JavaScript，也可使用章节目录查阅。")}</noscript>'
    else:
        content = contents(lang)
    output = OUT / lang / slug / 'index.html'; output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page_shell(lang, slug, row['title'], content), encoding='utf-8')


def main():
    global BASE
    parser = argparse.ArgumentParser(); parser.add_argument('--base-path', default='/ai-fde-business-playbook/'); args = parser.parse_args()
    BASE = '/' + args.base_path.strip('/') + '/' if args.base_path.strip('/') else '/'
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(); discover()
    shutil.copytree(ROOT / 'website/assets', OUT / 'assets')
    for row in PAGES.values():
        render_page(row)
    cover = copy_asset(ROOT / 'book/cover/front-cover.png')
    copy_asset(ROOT / 'book/en/frontmatter/front-cover.png')
    landing = f'<main id="main" class="landing" tabindex="-1"><div><img class="cover" src="{cover}" width="2040" height="2880" alt="《把AI带进经营》书封"></div><div><h1>把AI带进经营</h1><p class="english-title" lang="en">Bringing AI into<br>Business Operations</p><p class="landing-description">从业务流程到经营结果的企业AI落地指南。<br>面向企业经营者与技术团队。</p><p class="landing-description" lang="en">A practical guide to enterprise AI:<br>from business workflows to business results.</p><div class="edition-links"><a class="read-link" href="{site_url("zh")}">阅读中文版</a><a class="read-link secondary" href="{site_url("en")}" lang="en">Read in English</a></div><p class="landing-meta">郭斌 著 / By Guo Bin<br>五部 · 十八章 · 十八份行动工具<br><span lang="en">Five parts · 18 chapters · 18 worksheets</span></p><p class="landing-meta"><a href="{site_url("zh", "downloads")}">下载中文 PDF / Word</a><a href="{site_url("en", "downloads")}" lang="en">English downloads</a></p></div></main>'
    (OUT / 'index.html').write_text(page_shell('zh', '', LABELS['zh']['title'], landing, landing=True), encoding='utf-8')
    not_found = f'<main id="main" class="article-shell"><div class="article-inner"><h1>页面未找到 / Page not found</h1><p>可从目录重新查阅。 / Choose a chapter from the contents.</p><p><a href="{site_url("zh")}">中文目录</a> · <a href="{site_url("en")}">English contents</a></p></div></main>'
    (OUT / '404.html').write_text(page_shell('zh', '', '页面未找到 / Page not found', not_found, landing=True), encoding='utf-8')
    for lang in ['zh', 'en']:
        index = [dict(title=p['title'], url=site_url(lang, p['slug']), text=re.sub(r'\s+', ' ', p['plain_text'])) for p in PAGES.values() if p['lang'] == lang and p.get('plain_text')]
        (OUT / 'assets' / f'search-{lang}.json').write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    urls = [ORIGIN + site_url()] + [ORIGIN + site_url(p['lang'], p['slug']) for p in PAGES.values()]
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{esc(url)}</loc></url>' for url in urls) + '</urlset>', encoding='utf-8')
    (OUT / '.nojekyll').touch()
    manifest = dict(base_path=BASE, pages=[dict(language=p['lang'], slug=p['slug'], source=p['path'].relative_to(ROOT).as_posix() if p['path'] else None, source_sha256=hashlib.sha256(p['path'].read_bytes()).hexdigest() if p['path'] else None, figures=p.get('figure_count', 0), tables=p.get('table_count', 0)) for p in PAGES.values()], assets=list(ASSETS.values()))
    # Build evidence is outside the published output.
    (ROOT / 'website-build-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Built {len(PAGES) + 2} HTML pages; {len(ASSETS)} original image assets; prefix {BASE}')


if __name__ == '__main__':
    main()
