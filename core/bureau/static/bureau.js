// Zelij Core — bureau : comportements communs. Aucun script en ligne dans les pages (politique de sécurité du contenu stricte).
(function () {
  'use strict';
  // Confirmation avant un formulaire marqué data-confirmer="question".
  document.addEventListener('submit', function (ev) {
    var f = ev.target;
    if (f && f.hasAttribute && f.hasAttribute('data-confirmer') && !window.confirm(f.getAttribute('data-confirmer'))) ev.preventDefault();
  });
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  // Compte à rebours doux des montants : du zéro à la valeur, 900 ms.
  document.querySelectorAll('[data-compte]').forEach(function (el) {
    var cible = parseFloat(el.getAttribute('data-compte')); if (isNaN(cible)) return;
    var dec = (el.getAttribute('data-dec') || '2') | 0, debut = null, suffixe = el.getAttribute('data-suffixe') || '';
    function pas(t) { if (!debut) debut = t; var p = Math.min(1, (t - debut) / 900); p = 1 - Math.pow(1 - p, 3);
      el.textContent = (cible * p).toFixed(dec) + suffixe; if (p < 1) requestAnimationFrame(pas); }
    requestAnimationFrame(pas);
  });
  document.querySelectorAll('.bloc, .decision').forEach(function (el, i) { el.style.setProperty('--i', Math.min(i, 8)); });
})();
