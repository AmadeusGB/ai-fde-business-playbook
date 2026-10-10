(() => {
  const en = document.body.dataset.language === 'en';
  const base = document.body.dataset.base;
  const themeButton = document.querySelector('.theme-toggle');
  if (themeButton) {
    const labelTheme = () => {
      const dark = getComputedStyle(document.documentElement).colorScheme === 'dark';
      themeButton.setAttribute('aria-label', en ? (dark ? 'Use light theme' : 'Use dark theme') : (dark ? '切换浅色阅读' : '切换深色阅读'));
      themeButton.title = themeButton.getAttribute('aria-label');
    };
    themeButton.style.display = 'inline-flex';
    labelTheme();
    themeButton.addEventListener('click', () => {
      const theme = getComputedStyle(document.documentElement).colorScheme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = theme;
      try { localStorage.setItem('book-theme', theme); } catch (_) {}
      labelTheme();
    });
  }

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') document.querySelector('.mobile-menu')?.removeAttribute('open');
  });
  const sidebar = document.querySelector('.sidebar');
  const selected = sidebar?.querySelector('[aria-current="page"]');
  if (selected && selected.offsetTop > sidebar.clientHeight / 2) sidebar.scrollTop = selected.offsetTop - sidebar.clientHeight / 3;

  const progressKey = `book-position-${en ? 'en' : 'zh'}`;
  const page = document.body.dataset.page;
  if (/^(chapter|tool)-\d\d$/.test(page)) {
    const savePosition = heading => {
      const url = `${en ? 'en' : 'zh'}/${page}/${heading ? '#' + encodeURIComponent(heading) : ''}`;
      try { localStorage.setItem(progressKey, JSON.stringify({ url, title: document.querySelector('h1').textContent })); } catch (_) {}
    };
    savePosition(decodeURIComponent(location.hash.slice(1)));
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(entries => {
        for (const entry of entries) if (entry.isIntersecting) savePosition(entry.target.id);
      }, { rootMargin: '-10% 0px -65% 0px' });
      document.querySelectorAll('.prose h2[id], .prose h3[id]').forEach(h => observer.observe(h));
    }
  }
  const resume = document.querySelector('.resume-reading');
  if (resume) {
    try {
      const saved = JSON.parse(localStorage.getItem(progressKey));
      if (saved && /^(zh|en)\/(chapter|tool)-\d\d\/(#[^\s]*)?$/.test(saved.url)) {
        resume.href = base + saved.url;
        resume.textContent = (en ? 'Continue reading: ' : '继续阅读：') + saved.title;
        resume.style.display = 'inline-block';
      }
    } catch (_) {}
  }

  const form = document.querySelector('.search-form');
  if (!form) return;
  const input = form.querySelector('input');
  const results = document.querySelector('.search-results');
  const status = document.querySelector('.search-status');
  let index = null;
  let requestNumber = 0;
  const addHighlightedText = (parent, text, terms) => {
    const pattern = new RegExp(terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'gi');
    let last = 0;
    for (const match of text.matchAll(pattern)) {
      parent.append(document.createTextNode(text.slice(last, match.index)));
      const mark = document.createElement('mark'); mark.textContent = match[0]; parent.append(mark);
      last = match.index + match[0].length;
    }
    parent.append(document.createTextNode(text.slice(last)));
  };
  const search = async () => {
    const request = ++requestNumber;
    const query = input.value.trim().slice(0, 160);
    results.replaceChildren();
    if (!query) { status.textContent = en ? 'Enter words to search this edition.' : '输入关键词，搜索本语言全书。'; return; }
    const url = new URL(location.href); url.searchParams.set('q', query); history.replaceState(null, '', url);
    status.textContent = en ? 'Searching…' : '正在搜索…';
    try {
      if (!index) {
        const response = await fetch(`${base}assets/search-${en ? 'en' : 'zh'}.json`);
        if (!response.ok) throw new Error('Search index unavailable');
        index = await response.json();
      }
      if (request !== requestNumber) return;
      const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
      const matches = index.filter(row => terms.every(t => (row.title + ' ' + row.text).toLowerCase().includes(t)));
      matches.sort((a, b) => terms.filter(t => b.title.toLowerCase().includes(t)).length - terms.filter(t => a.title.toLowerCase().includes(t)).length);
      status.textContent = en ? `${matches.length} matching pages${matches.length > 40 ? '; showing the first 40' : ''}.` : `找到 ${matches.length} 个页面${matches.length > 40 ? '，显示前 40 个' : ''}。`;
      if (!matches.length) status.textContent += en ? ' Try fewer words or search the other edition.' : '可缩短关键词，或切换到另一语言搜索。';
      for (const row of matches.slice(0, 40)) {
        const item = document.createElement('li');
        const link = document.createElement('a'); link.href = row.url; addHighlightedText(link, row.title, terms); item.append(link);
        const position = Math.max(0, row.text.toLowerCase().indexOf(terms[0]) - 60);
        const snippet = (position ? '…' : '') + row.text.slice(position, position + 220) + (row.text.length > position + 220 ? '…' : '');
        const paragraph = document.createElement('p'); addHighlightedText(paragraph, snippet, terms); item.append(paragraph);
        results.append(item);
      }
    } catch (_) {
      if (request === requestNumber) status.textContent = en ? 'Search could not load. Check your connection and press Search to retry.' : '搜索资料加载失败。请检查网络，再点击“搜索”重试。';
    }
  };
  form.addEventListener('submit', event => { event.preventDefault(); search(); });
  input.value = new URLSearchParams(location.search).get('q') || '';
  if (input.value) search();
})();
