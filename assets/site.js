// Untouched site — the only script. Two jobs:
// 1. The hero comparison follows your finger once you touch it.
// 2. A one-line hint pointing Chinese-language visitors to the Chinese page (never a redirect).
(function () {
  // The develop animation is pure CSS (see .reveal in site.css), so the page is right even without JS.
  // JS only hands control to the reader once they touch the slider.
  var reveal = document.querySelector('[data-reveal]');
  var range = reveal && reveal.querySelector('input[type="range"]');
  if (range) {
    range.addEventListener('input', function () {
      reveal.classList.add('touched');
      reveal.style.setProperty('--pos', range.value + '%');
    });
  }

  var hint = document.querySelector('[data-lang-hint]');
  if (hint) {
    var key = 'untouched-lang-hint-dismissed';
    var dismissed = false;
    try { dismissed = localStorage.getItem(key) === '1'; } catch (e) {}
    var langs = (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || '']);
    var prefersZh = String(langs[0] || '').toLowerCase().indexOf('zh') === 0;
    if (prefersZh && !dismissed) hint.classList.add('show');
    var btn = hint.querySelector('button');
    if (btn) btn.addEventListener('click', function () {
      hint.classList.remove('show');
      try { localStorage.setItem(key, '1'); } catch (e) {}
    });
  }
})();
