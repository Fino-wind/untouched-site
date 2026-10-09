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

  // 3. Dynamic campaign attribution for App Store links based on AI/search referrers or UTM
  try {
    var ref = (document.referrer || '').toLowerCase();
    var params = new URLSearchParams(window.location.search);
    var utm = (params.get('utm_source') || '').toLowerCase();
    var ct = null;

    if (ref.indexOf('chatgpt.com') !== -1 || ref.indexOf('chat.openai.com') !== -1 || utm.indexOf('chatgpt') !== -1) {
      ct = 'ai_chatgpt';
    } else if (ref.indexOf('perplexity.ai') !== -1 || utm.indexOf('perplexity') !== -1) {
      ct = 'ai_perplexity';
    } else if (ref.indexOf('claude.ai') !== -1 || utm.indexOf('claude') !== -1) {
      ct = 'ai_claude';
    } else if (ref.indexOf('gemini.google.com') !== -1 || utm.indexOf('gemini') !== -1) {
      ct = 'ai_gemini';
    } else if (ref.indexOf('copilot.microsoft.com') !== -1 || utm.indexOf('copilot') !== -1) {
      ct = 'ai_copilot';
    } else if (ref.indexOf('google.') !== -1 || utm.indexOf('google') !== -1) {
      ct = 'seo_google';
    } else if (ref.indexOf('bing.') !== -1 || utm.indexOf('bing') !== -1) {
      ct = 'seo_bing';
    } else if (ref.indexOf('dev.to') !== -1) {
      ct = 'ref_devto';
    } else if (ref.indexOf('medium.com') !== -1) {
      ct = 'ref_medium';
    } else if (ref.indexOf('reddit.com') !== -1) {
      ct = 'ref_reddit';
    }

    if (ct) {
      var links = document.querySelectorAll('a[href*="apps.apple.com"]');
      for (var i = 0; i < links.length; i++) {
        var a = links[i];
        try {
          var u = new URL(a.href);
          u.searchParams.set('ct', ct);
          a.href = u.toString();
        } catch (err) {}
      }
    }
  } catch (e) {}
})();
