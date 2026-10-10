(() => {
  let theme = null;
  try { theme = localStorage.getItem('book-theme'); } catch (_) {}
  if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme;
})();
