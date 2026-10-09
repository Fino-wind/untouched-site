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

  // 3. Dynamic campaign attribution for App Store links based on AI, Agent, or search referrers/UTMs
  try {
    var ref = (document.referrer || '').toLowerCase();
    var params = new URLSearchParams(window.location.search);
    var utm = (params.get('utm_source') || params.get('ref') || params.get('source') || params.get('from') || '').toLowerCase();
    var ct = null;

    // A. Terminal Coding Agents & CLI overrides
    if (utm.indexOf('claudecode') !== -1) {
      ct = 'ai_claudecode';
    } else if (utm.indexOf('agy') !== -1 || utm.indexOf('antigravity') !== -1) {
      ct = 'ai_agy';
    } else if (utm.indexOf('codex') !== -1) {
      ct = 'ai_codex';
    } else if (utm.indexOf('cursor') !== -1) {
      ct = 'ai_cursor';
    } else if (utm.indexOf('windsurf') !== -1) {
      ct = 'ai_windsurf';
    } else if (utm.indexOf('hermes') !== -1) {
      ct = 'ai_hermes';
    } else if (utm.indexOf('openclaw') !== -1) {
      ct = 'ai_openclaw';
    } else if (utm.indexOf('muse') !== -1) {
      ct = 'ai_muse';
    } else if (utm.indexOf('aider') !== -1) {
      ct = 'ai_aider';
    } else if (utm.indexOf('cline') !== -1 || utm.indexOf('roocode') !== -1 || utm.indexOf('roo') !== -1) {
      ct = 'ai_cline';
    } else if (utm.indexOf('agent') !== -1 || utm.indexOf('llmstxt') !== -1 || utm.indexOf('llms') !== -1 || utm.indexOf('mcp') !== -1 || utm.indexOf('bot') !== -1) {
      ct = 'ai_agent';
    }
    // B. AI Chat & Search Platforms (Referrer or UTM)
    else if (ref.indexOf('chatgpt.com') !== -1 || ref.indexOf('chat.openai.com') !== -1 || utm.indexOf('chatgpt') !== -1) {
      ct = 'ai_chatgpt';
    } else if (ref.indexOf('perplexity.ai') !== -1 || utm.indexOf('perplexity') !== -1) {
      ct = 'ai_perplexity';
    } else if (ref.indexOf('claude.ai') !== -1 || utm.indexOf('claude') !== -1) {
      ct = 'ai_claude';
    } else if (ref.indexOf('gemini.google.com') !== -1 || utm.indexOf('gemini') !== -1) {
      ct = 'ai_gemini';
    } else if (ref.indexOf('copilot.microsoft.com') !== -1 || utm.indexOf('copilot') !== -1) {
      ct = 'ai_copilot';
    } else if (ref.indexOf('grok.com') !== -1 || ref.indexOf('x.ai') !== -1 || utm.indexOf('grok') !== -1) {
      ct = 'ai_grok';
    } else if (ref.indexOf('phind.com') !== -1 || utm.indexOf('phind') !== -1) {
      ct = 'ai_phind';
    } else if (ref.indexOf('meta.ai') !== -1 || utm.indexOf('meta_ai') !== -1) {
      ct = 'ai_meta';
    } else if (ref.indexOf('poe.com') !== -1 || utm.indexOf('poe') !== -1) {
      ct = 'ai_poe';
    } else if (ref.indexOf('you.com') !== -1 || utm.indexOf('you') !== -1) {
      ct = 'ai_you';
    } else if (ref.indexOf('genspark.ai') !== -1 || utm.indexOf('genspark') !== -1) {
      ct = 'ai_genspark';
    }
    // C. Search Engines & Developer Ecosystem
    else if (ref.indexOf('google.') !== -1 || utm.indexOf('google') !== -1) {
      ct = 'seo_google';
    } else if (ref.indexOf('bing.') !== -1 || utm.indexOf('bing') !== -1) {
      ct = 'seo_bing';
    } else if (ref.indexOf('duckduckgo.com') !== -1 || utm.indexOf('duckduckgo') !== -1) {
      ct = 'seo_ddg';
    } else if (ref.indexOf('kagi.com') !== -1 || utm.indexOf('kagi') !== -1) {
      ct = 'seo_kagi';
    } else if (ref.indexOf('github.com') !== -1 || utm.indexOf('github') !== -1) {
      ct = 'ref_github';
    } else if (ref.indexOf('pypi.org') !== -1 || utm.indexOf('pypi') !== -1) {
      ct = 'ref_pypi';
    } else if (ref.indexOf('dev.to') !== -1) {
      ct = 'ref_devto';
    } else if (ref.indexOf('medium.com') !== -1) {
      ct = 'ref_medium';
    } else if (ref.indexOf('reddit.com') !== -1) {
      ct = 'ref_reddit';
    } else if (ref.indexOf('v2ex.com') !== -1 || utm.indexOf('v2ex') !== -1) {
      ct = 'ref_v2ex';
    } else if (ref.indexOf('news.ycombinator.com') !== -1) {
      ct = 'ref_hn';
    } else if (ref.indexOf('t.co') !== -1 || ref.indexOf('twitter.com') !== -1 || ref.indexOf('x.com') !== -1) {
      ct = 'ref_x';
    } else if (utm) {
      ct = 'ref_' + utm.replace(/[^a-z0-9_-]/g, '').slice(0, 20);
    }

    if (ct) {
      var applyCt = function() {
        var links = document.querySelectorAll('a[href*="apps.apple.com"]');
        for (var i = 0; i < links.length; i++) {
          try {
            var u = new URL(links[i].href);
            u.searchParams.set('ct', ct);
            links[i].href = u.toString();
          } catch (err) {}
        }
      };
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyCt);
      } else {
        applyCt();
      }
      document.addEventListener('click', function(e) {
        var a = e.target && e.target.closest && e.target.closest('a[href*="apps.apple.com"]');
        if (a) {
          try {
            var u = new URL(a.href);
            u.searchParams.set('ct', ct);
            a.href = u.toString();
          } catch(err) {}
        }
      }, true);
    }
  } catch (e) {}
})();
