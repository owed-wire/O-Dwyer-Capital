/* O'Dwyer Capital - dark mode controller.
   Default: follow system preference. Toggle overrides and is remembered. */
(function () {
    var saved = null;
    try { saved = localStorage.getItem('theme'); } catch (e) {}
    var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (saved === 'dark' || (!saved && prefersDark)) {
        document.documentElement.classList.add('dark');
    }

    function icon() {
        return document.documentElement.classList.contains('dark') ? '☀️' : '🌙';
    }

    window.toggleTheme = function () {
        var el = document.documentElement;
        el.classList.toggle('dark');
        try {
            localStorage.setItem('theme', el.classList.contains('dark') ? 'dark' : 'light');
        } catch (e) {}
        var btn = document.querySelector('.theme-toggle');
        if (btn) btn.textContent = icon();
    };

    document.addEventListener('DOMContentLoaded', function () {
        var nav = document.querySelector('nav');
        if (!nav) return;
        var btn = document.createElement('button');
        btn.className = 'theme-toggle';
        btn.setAttribute('aria-label', 'Toggle dark mode');
        btn.textContent = icon();
        btn.addEventListener('click', window.toggleTheme);
        nav.appendChild(btn);
    });
})();
