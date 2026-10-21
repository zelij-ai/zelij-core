// Décider en swipant (0.9.3) : une carte à la fois, droite = approuver, gauche = refuser, haut = plus tard. Chaque geste ouvre
// une confirmation : rien ne part sans un second geste explicite, et la décision reste un POST vers la même route que le bureau.
// Pointeur, clavier (← → ↑, Entrée, Échap) et trois boutons pour les écrans sans tactile. Aucun script en ligne (CSP stricte).
(function () {
  'use strict';
  var racine = document.getElementById('decider'); if (!racine) return;
  var pile = racine.querySelector('.sw-pile'), feuille = document.getElementById('sw-feuille'), formulaire = document.getElementById('sw-form');
  var compteur = racine.querySelector('[data-sw-compteur]'), csrf = racine.getAttribute('data-csrf');
  var SEUIL = 110, cartes = [].slice.call(pile.querySelectorAll('.sw-carte')), index = 0, courante = null, depart = null, dx = 0, dy = 0;
  var LIBELLES = { approuver: 'Approuver', refuser: 'Refuser', a_modifier: 'Demander une modification' };

  function majPile() {
    cartes.forEach(function (c, i) {
      var k = i - index;
      c.hidden = k < 0 || k > 2;
      c.style.transform = k > 0 ? 'translateY(' + (k * 10) + 'px) scale(' + (1 - k * 0.04) + ')' : '';
      c.style.zIndex = String(10 - Math.max(0, k)); c.classList.toggle('sw-carte--haut', k === 0);
      c.setAttribute('aria-hidden', k === 0 ? 'false' : 'true');
    });
    courante = cartes[index] || null;
    if (compteur) compteur.textContent = courante ? (index + 1) + ' / ' + cartes.length : '0 / ' + cartes.length;
    racine.classList.toggle('sw--vide', !courante);
  }
  function indice(nom) { racine.querySelectorAll('.sw-indice').forEach(function (e) { e.classList.toggle('sw-indice--on', e.getAttribute('data-indice') === nom); }); }
  function poser() {
    if (!courante) return;
    courante.style.transition = 'transform .28s cubic-bezier(.2,.8,.2,1)'; courante.style.transform = ''; indice(null);
    setTimeout(function () { if (courante) courante.style.transition = ''; }, 300);
  }
  function geste(nom) {
    if (!courante) return;
    if (nom === 'plus_tard') { courante.style.transition = 'transform .32s ease, opacity .32s ease'; courante.style.transform = 'translateY(-140%) rotate(-2deg)'; courante.style.opacity = '0';
      setTimeout(function () { courante.style.transition = ''; courante.style.opacity = ''; index++; if (index >= cartes.length) index = 0; majPile(); indice(null); }, 320); return; }
    ouvrirFeuille(nom === 'droite' ? 'approuver' : 'refuser');
  }
  function ouvrirFeuille(action) {
    if (!courante || !feuille) return;
    var id = courante.getAttribute('data-id'), lecture = courante.getAttribute('data-lecture') === '1';
    feuille.querySelector('[data-sw-titre]').textContent = LIBELLES[action] + ' : ' + courante.getAttribute('data-objectif');
    feuille.querySelector('[data-sw-sous]').textContent = courante.getAttribute('data-resume') || '';
    formulaire.setAttribute('action', '/decisions/' + id + '/' + action);
    var zone = feuille.querySelector('[data-sw-consigne]'); zone.hidden = action !== 'a_modifier'; zone.querySelector('textarea').required = action === 'a_modifier';
    var lu = feuille.querySelector('[data-sw-lu]'); lu.hidden = !(lecture && action === 'approuver'); lu.querySelector('input').checked = false; lu.querySelector('input').required = !lu.hidden;
    var bouton = feuille.querySelector('[data-sw-confirmer]'); bouton.textContent = action === 'approuver' ? 'Oui, approuver' : (action === 'refuser' ? 'Oui, refuser' : 'Envoyer la consigne');
    bouton.className = 'bouton ' + (action === 'approuver' ? 'bouton--laiton' : 'bouton--second');
    feuille.showModal(); poser();
  }
  if (feuille) {
    feuille.querySelector('[data-sw-annuler]').addEventListener('click', function () { feuille.close(); });
    feuille.addEventListener('close', poser);
    formulaire.querySelector('input[name=_csrf]').value = csrf || '';
    formulaire.addEventListener('submit', function () { feuille.querySelector('[data-sw-confirmer]').disabled = true; });
  }

  // pointeur
  pile.addEventListener('pointerdown', function (ev) { if (!courante || ev.target.closest('a, button, summary')) return; depart = { x: ev.clientX, y: ev.clientY }; dx = dy = 0; courante.setPointerCapture && courante.setPointerCapture(ev.pointerId); });
  pile.addEventListener('pointermove', function (ev) {
    if (!depart || !courante) return; dx = ev.clientX - depart.x; dy = ev.clientY - depart.y;
    courante.style.transform = 'translate(' + dx + 'px,' + dy + 'px) rotate(' + (dx / 18) + 'deg)';
    indice(dy < -SEUIL && Math.abs(dx) < SEUIL ? 'plus_tard' : (dx > SEUIL ? 'droite' : (dx < -SEUIL ? 'gauche' : null)));
  });
  function lacher() {
    if (!depart || !courante) { depart = null; return; }
    var nom = dy < -SEUIL && Math.abs(dx) < SEUIL ? 'plus_tard' : (dx > SEUIL ? 'droite' : (dx < -SEUIL ? 'gauche' : null)); depart = null;
    if (nom) geste(nom); else poser();
  }
  pile.addEventListener('pointerup', lacher); pile.addEventListener('pointercancel', lacher);

  // boutons et clavier
  racine.querySelectorAll('[data-sw-geste]').forEach(function (b) { b.addEventListener('click', function () { geste(b.getAttribute('data-sw-geste')); }); });
  racine.querySelectorAll('[data-sw-modifier]').forEach(function (b) { b.addEventListener('click', function () { ouvrirFeuille('a_modifier'); }); });
  document.addEventListener('keydown', function (ev) {
    if (feuille && feuille.open) return;
    if (ev.target.matches('input, textarea, select')) return;
    if (ev.key === 'ArrowRight') { ev.preventDefault(); geste('droite'); }
    else if (ev.key === 'ArrowLeft') { ev.preventDefault(); geste('gauche'); }
    else if (ev.key === 'ArrowUp') { ev.preventDefault(); geste('plus_tard'); }
    else if (ev.key === 'm' || ev.key === 'M') ouvrirFeuille('a_modifier');
  });
  majPile();
})();
