// Zelij Core — bureau : comportements communs. Aucun script en ligne dans les pages (politique de sécurité du contenu stricte).
(function () {
  'use strict';
  // Confirmation avant un formulaire marqué data-confirmer="question".
  document.addEventListener('submit', function (ev) {
    var f = ev.target;
    if (f && f.hasAttribute && f.hasAttribute('data-confirmer') && !window.confirm(f.getAttribute('data-confirmer'))) ev.preventDefault();
  });
  // Jauge du budget : la largeur vient d'un attribut de données, posée ici (un style en ligne serait refusé par la politique de sécurité).
  document.querySelectorAll('[data-part]').forEach(function (el) {
    var part = Math.max(0, Math.min(100, parseFloat(el.getAttribute('data-part')) || 0)); el.style.setProperty('--part', part + '%');
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

// Encart « Une étoile pour Zelij Core » (0.9.1) : révélé après un court délai, fermeture mémorisée trente jours dans ce navigateur.
(function () {
  'use strict';
  var encart = document.getElementById('etoile'); if (!encart) return;
  var cle = 'zelij-etoile-fermee', trenteJours = 30 * 24 * 3600 * 1000, fermee = 0;
  try { fermee = Number(localStorage.getItem(cle) || 0); } catch (e) { fermee = 0; }
  if (fermee && Date.now() - fermee < trenteJours) return;
  window.setTimeout(function () { encart.hidden = false; encart.classList.add('etoile--visible'); }, 1200);
  encart.querySelector('[data-etoile-fermer]').addEventListener('click', function () {
    encart.hidden = true;
    try { localStorage.setItem(cle, String(Date.now())); } catch (e) { /* stockage indisponible : l'encart reviendra à la prochaine page */ }
  });
})();
