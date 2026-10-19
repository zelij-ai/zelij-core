// Aquarium Zelij Core — même scène que l'aquarium de zelij.ai : nuit chaude, couloirs par métier, agents en anneaux, cartes
// de dialogue à filet, liens entre acteurs, horloge et ligne de temps rejouable. Canvas 2D, aucune bibliothèque. Tout ce qui
// s'affiche vient des événements réels des 24 dernières heures. Sous « moins de mouvement » : scène fixe, replay manuel.
(function () {
  var canvas = document.getElementById('aquarium'); if (!canvas) return;
  var source = canvas.getAttribute('data-source'), ctx = canvas.getContext('2d');
  var reduit = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dpr = Math.min(2, window.devicePixelRatio || 1), etat = null, noeuds = {}, couloirs = [], cartes = [], liens = [], portraits = {};
  var mode = 'direct', curseur = 0, vitesse = 60, enPause = false, dernierTick = null, indexEvt = 0, derniereSouris = { x: -1, y: -1 };
  var ui = { pause: document.getElementById('aq-pause'), direct: document.getElementById('aq-direct'), slider: document.getElementById('aq-temps'),
             vitesse: document.getElementById('aq-vitesse'), horloge: document.getElementById('aq-horloge'), sous: document.getElementById('aq-sous') };
  var ENCRE = '#0e0b08', OR = '#e0a21c';

  // ---------- disposition
  var tv = document.body.classList.contains('tv'), decalTv = tv ? 70 : 0;   // mode salle d'attente : la grande horloge prend le haut, la scène descend
  function taille() {
    var w = canvas.clientWidth, h = tv ? Math.max(360, window.innerHeight - (document.querySelector('.mesures') ? document.querySelector('.mesures').offsetHeight : 90)) : Math.max(480, Math.min(720, Math.round(w * 0.56)));
    canvas.width = w * dpr; canvas.height = h * dpr; canvas.style.height = h + 'px'; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    disposer();
  }
  function disposer() {
    if (!etat) return;
    var w = canvas.clientWidth, h = canvas.clientHeight, n = etat.couloirs.length, large = w / n;
    couloirs = etat.couloirs.map(function (k, i) { return { id: k.id, nom: k.nom, couleur: k.couleur, x0: i * large, x1: (i + 1) * large, cx: (i + 0.5) * large }; });
    var parCouloir = {};
    etat.agents.forEach(function (a) { (parCouloir[a.couloir] = parCouloir[a.couloir] || []).push(a); });
    etat.postes_libres.forEach(function (p) { (parCouloir.libres = parCouloir.libres || []).push({ id: p.id, nom: p.nom, prenom: '?', fonction: p.resume, couloir: 'libres', couleur: '#8a8378', libre: true }); });
    var anciens = noeuds; noeuds = {};
    couloirs.forEach(function (k) {
      var liste = parCouloir[k.id] || [], top = 200 + decalTv, bas = h - 90, pas = liste.length > 1 ? (bas - top) / (liste.length - 1) : 0;
      liste.forEach(function (a, i) {
        var ancien = anciens[a.id];
        noeuds[a.id] = { id: a.id, nom: a.nom, prenom: a.prenom, fonction: a.fonction, couleur: a.couleur, libre: !!a.libre, actif: !!a.actif, en_cours: !!a.en_cours,
          activite: a.activite || 0, cout: a.cout_eur || 0, x0: k.cx + (i % 2 ? 46 : -46) * (liste.length > 1 ? 1 : 0), y0: liste.length > 1 ? top + pas * i : (top + bas) / 2,
          x: ancien ? ancien.x : k.cx, y: ancien ? ancien.y : (liste.length > 1 ? top + pas * i : (top + bas) / 2), phase: Math.random() * 6.28, r: a.libre ? 22 : 26 };
      });
    });
    var f = etat.fondateur;
    noeuds.fondateur = { id: 'fondateur', nom: f.nom, prenom: f.nom, fonction: f.fonction, couleur: f.couleur, fondateur: true, x0: w / 2, y0: 140 + decalTv, x: w / 2, y: 140 + decalTv, phase: 0, r: 30, actif: true };
  }
  function charger() {
    fetch(source, { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (d) {
      var premier = !etat; etat = d; disposer();
      if (premier) { curseur = Date.parse(d.maintenant); if (ui.slider) { ui.slider.min = Date.parse(d.depuis); ui.slider.max = Date.parse(d.maintenant); ui.slider.value = curseur; }
        indexEvt = d.evenements.length; d.evenements.slice(-4).forEach(function (e) { jouer(e, true); }); }
      if (!('fondateur' in portraits)) { var imgF = new Image(); portraits.fondateur = null; imgF.onload = function () { portraits.fondateur = imgF; }; imgF.onerror = function () { portraits.fondateur = null; }; imgF.src = '/portraits/fondateur'; }
      d.agents.forEach(function (a) { if (!(a.id in portraits)) { var img = new Image(); portraits[a.id] = null; img.onload = function () { portraits[a.id] = img; }; img.onerror = function () { portraits[a.id] = null; }; img.src = '/agents/' + a.id + '/portrait'; } });
      if (reduit) dessiner(0);
    }).catch(function () {});
  }

  // ---------- événements → cartes et liens
  function jouer(e, discret) {
    var acteur = noeuds[e.acteur] || noeuds['chef-de-cabinet']; if (!acteur) return;
    var cible = e.cible ? noeuds[e.cible] : null, teinte = e.type === 'decision_ceo' ? OR : (e.type === 'execution' || e.type === 'outil') ? '#37b385' : (e.type === 'decision' ? '#f1d48a' : '#8ea6f0');
    cartes.push({ acteur: acteur, cible: cible, texte: e.texte, t0: performance.now(), duree: discret ? 5000 : 7000, teinte: teinte, type: e.type, heure: e.t.slice(11, 16) });
    if (cartes.length > 4) cartes.shift();
    if (cible) { liens.push({ a: acteur, b: cible, t0: performance.now(), duree: 3200, teinte: teinte }); if (liens.length > 6) liens.shift(); }
    acteur.pulse = performance.now();
  }
  function avancer(dt) {
    if (!etat || enPause) return;
    if (mode === 'direct') { curseur = Date.now(); return; }
    curseur += dt * vitesse;
    var fin = Date.parse(etat.maintenant);
    if (curseur >= fin) { curseur = fin; enPause = true; if (ui.pause) ui.pause.textContent = '▶ Rejouer'; }
    while (indexEvt < etat.evenements.length && Date.parse(etat.evenements[indexEvt].t) <= curseur) { jouer(etat.evenements[indexEvt], false); indexEvt++; }
    if (ui.slider) ui.slider.value = curseur;
  }
  function allerA(ms) {
    curseur = ms; cartes = []; liens = []; indexEvt = 0;
    while (indexEvt < etat.evenements.length && Date.parse(etat.evenements[indexEvt].t) <= curseur) indexEvt++;
    etat.evenements.slice(Math.max(0, indexEvt - 3), indexEvt).forEach(function (e) { jouer(e, true); });
  }

  // ---------- dessin
  function fond(w, h, t) {
    var g = ctx.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#1a1510'); g.addColorStop(0.5, '#0f0c09'); g.addColorStop(1, '#0a0806'); ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    for (var i = 0; i < 6; i++) { ctx.save(); ctx.globalAlpha = 0.045 + (reduit ? 0 : 0.015 * Math.sin(t / 2200 + i * 1.7)); ctx.fillStyle = '#e0a21c';
      var x0 = (i + 0.4) * w / 6; ctx.beginPath(); ctx.moveTo(x0 - 30, 0); ctx.lineTo(x0 + 40, 0); ctx.lineTo(x0 + 120, h); ctx.lineTo(x0 - 60, h); ctx.closePath(); ctx.fill(); ctx.restore(); }
    for (var k = 0; k < 3; k++) { ctx.save(); ctx.globalAlpha = 0.08; ctx.strokeStyle = '#e0a21c'; ctx.lineWidth = 1; ctx.beginPath();
      for (var x = 0; x <= w; x += 12) { var y = h - 60 - k * 18 + Math.sin(x / 90 + t / (1800 + 300 * k) * (reduit ? 0 : 1) + k) * 7; x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
      ctx.stroke(); ctx.restore(); }
  }
  function entetes(h) {
    couloirs.forEach(function (k) {
      ctx.save(); ctx.font = '600 11px ui-monospace, Consolas, monospace'; ctx.textAlign = 'center'; ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.letterSpacing = '0.22em';
      ctx.fillText(k.nom, k.cx, 96 + decalTv); ctx.strokeStyle = k.couleur; ctx.globalAlpha = 0.8; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(k.cx - 16, 104 + decalTv); ctx.lineTo(k.cx + 16, 104 + decalTv); ctx.stroke();
      ctx.globalAlpha = 0.06; ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(k.x1, 84); ctx.lineTo(k.x1, h - 30); ctx.stroke(); ctx.restore();
    });
  }
  function noeud(n, t) {
    var nage = (reduit || n.fondateur) ? 0 : Math.sin(t / 1700 + n.phase) * 4;
    if (!reduit && !n.fondateur) { n.x += (n.x0 - n.x) * 0.02 + Math.cos(t / 2600 + n.phase) * 0.15; n.y += (n.y0 - n.y) * 0.02; }
    var x = n.x, y = n.y + nage, r = n.r;
    if (n.pulse && t - n.pulse < 1800) { var p = (t - n.pulse) / 1800; ctx.save(); ctx.globalAlpha = (1 - p) * 0.6; ctx.strokeStyle = n.couleur; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, r + 6 + p * 26, 0, 6.283); ctx.stroke(); ctx.restore(); }
    ctx.save();
    if (n.libre) { ctx.setLineDash([4, 4]); ctx.strokeStyle = 'rgba(255,255,255,.5)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(255,255,255,.08)'; ctx.fill(); ctx.fillStyle = 'rgba(255,255,255,.8)'; ctx.font = '700 16px ui-sans-serif, system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('?', x, y + 1); }
    else {
      ctx.shadowColor = n.couleur; ctx.shadowBlur = n.actif || n.fondateur ? 18 : 6; ctx.strokeStyle = n.couleur; ctx.lineWidth = n.fondateur ? 3 : 2.5;
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.stroke(); ctx.shadowBlur = 0;
      visage(n, x, y, r - 3);
      if (n.en_cours && !reduit) { ctx.save(); ctx.strokeStyle = n.couleur; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, r + 5, t / 300, t / 300 + 1.2); ctx.stroke(); ctx.restore(); }
    }
    ctx.restore();
    // étiquette en pastille sombre : code dans la couleur du couloir, prénom en blanc
    var code = n.fondateur ? 'FONDATEUR' : (n.libre ? 'libre' : n.id), prenom = n.fondateur ? 'humain' : (n.libre ? n.nom : n.prenom);
    ctx.save(); ctx.font = '600 10px ui-monospace, Consolas, monospace'; var wc = ctx.measureText(code).width; ctx.font = '700 13px ui-sans-serif, system-ui'; var wp = ctx.measureText(prenom).width;
    var pw = wc + wp + 26, px = x - pw / 2, py = y + r + 8;
    ctx.fillStyle = 'rgba(8,10,12,.72)'; ctx.beginPath(); ctx.roundRect(px, py, pw, 22, 11); ctx.fill();
    ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.font = '600 10px ui-monospace, Consolas, monospace'; ctx.fillStyle = n.fondateur ? OR : n.couleur; ctx.fillText(code, px + 9, py + 12);
    ctx.font = '700 13px ui-sans-serif, system-ui'; ctx.fillStyle = '#fff'; ctx.fillText(prenom, px + 9 + wc + 8, py + 12); ctx.restore();
    if (Math.hypot(derniereSouris.x - x, derniereSouris.y - y) < r + 6) infobulle(n, x, y);
  }
  function infobulle(n, x, y) {
    var lignes = n.libre ? ['Poste libre : ' + n.nom, 'cliquez pour voir la fiche'] : n.fondateur ? ['Vous décidez', etat.decisions_en_attente + ' décision(s) en attente'] : [n.nom + ' · ' + n.fonction, n.activite + ' action(s) sur 24 h · ' + n.cout.toFixed(3) + ' €'];
    ctx.save(); ctx.font = '12px ui-sans-serif, system-ui'; var w = Math.max.apply(null, lignes.map(function (l) { return ctx.measureText(l).width; })) + 22, h = 16 * lignes.length + 14;
    var bx = Math.min(Math.max(8, x - w / 2), canvas.clientWidth - w - 8), by = y - n.r - h - 12;
    ctx.fillStyle = 'rgba(10,8,6,.92)'; ctx.strokeStyle = 'rgba(224,162,28,.55)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.roundRect(bx, by, w, h, 8); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'; lignes.forEach(function (l, i) { ctx.fillStyle = i ? 'rgba(255,255,255,.7)' : '#fff'; ctx.fillText(l, bx + 11, by + 20 + 16 * i); });
    ctx.restore();
  }
  function lien(l, t) {
    var p = (t - l.t0) / l.duree; if (p >= 1) return false;
    var a = l.a, b = l.b, mx = (a.x + b.x) / 2, my = Math.min(a.y, b.y) - 60;
    ctx.save(); ctx.globalAlpha = 0.85 * (1 - p); ctx.strokeStyle = l.teinte; ctx.lineWidth = 1.5; ctx.shadowColor = l.teinte; ctx.shadowBlur = 8;
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.quadraticCurveTo(mx, my, b.x, b.y); ctx.stroke();
    var q = Math.min(1, p * 1.6), px = (1 - q) * (1 - q) * a.x + 2 * (1 - q) * q * mx + q * q * b.x, py = (1 - q) * (1 - q) * a.y + 2 * (1 - q) * q * my + q * q * b.y;
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(px, py, 3, 0, 6.283); ctx.fill(); ctx.restore(); return true;
  }
  // Portrait rond (photo si elle existe, sinon monogramme sur fond sombre), réutilisé par les cartes et les nœuds.
  function visage(n, x, y, r) {
    ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.clip();
    var img = portraits[n.id];
    if (img) ctx.drawImage(img, x - r, y - r, 2 * r, 2 * r);
    else { var g = ctx.createLinearGradient(x - r, y - r, x + r, y + r); g.addColorStop(0, '#2b241c'); g.addColorStop(1, '#15110d'); ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
      var parts = (n.nom || '').split(' '); ctx.fillStyle = n.fondateur ? OR : 'rgba(255,255,255,.92)'; ctx.font = '700 ' + Math.round(r * 0.78) + 'px ui-sans-serif, system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(n.fondateur ? 'VOUS' : ((parts[0] || '')[0] || '') + ((parts[1] || '')[0] || ''), x, y + 1); }
    ctx.restore();
  }
  // Carte de dialogue, comme sur l'aquarium de zelij.ai : verre sombre, filet teinté, portrait, nom, « acteur → cible », texte lisible.
  function carte(c, t, rang) {
    var p = (t - c.t0) / c.duree; if (p >= 1) return false;
    var alpha = p < 0.08 ? p / 0.08 : (p > 0.85 ? (1 - p) / 0.15 : 1), w = canvas.clientWidth, a = c.acteur;
    ctx.save(); ctx.globalAlpha = alpha; ctx.font = '500 16px ui-sans-serif, system-ui';
    var cwMax = Math.min(460, w - 24), lignes = couper(c.texte, cwMax - 36), lw = 0;
    lignes.forEach(function (l) { lw = Math.max(lw, ctx.measureText(l).width); });
    var cw = Math.max(280, Math.min(cwMax, lw + 36)), ch = 64 + 24 * lignes.length;
    var cx = a.x > w / 2 ? a.x - cw - 64 : a.x + 64, cy = a.y - ch / 2 - 10 - rang * 14;
    cx = Math.min(Math.max(10, cx), w - cw - 10); cy = Math.min(Math.max(112, cy), canvas.clientHeight - ch - 72);
    // filet entre l'agent et la carte
    var ax = cx > a.x ? cx : cx + cw, ay = cy + ch / 2;
    ctx.strokeStyle = c.teinte; ctx.globalAlpha = alpha * 0.75; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.quadraticCurveTo((a.x + ax) / 2, a.y - 24, ax, ay); ctx.stroke();
    // halo concentrique autour de l'acteur pendant la carte
    ctx.globalAlpha = alpha * 0.35; ctx.lineWidth = 1; for (var k = 1; k <= 3; k++) { ctx.beginPath(); ctx.arc(a.x, a.y, a.r + 10 * k + (reduit ? 0 : Math.sin(t / 500 + k) * 2), 0, 6.283); ctx.stroke(); }
    // la carte
    ctx.globalAlpha = alpha; ctx.fillStyle = 'rgba(7,12,14,.93)'; ctx.strokeStyle = c.teinte; ctx.lineWidth = 1.5; ctx.shadowColor = c.teinte; ctx.shadowBlur = 22;
    ctx.beginPath(); ctx.roundRect(cx, cy, cw, ch, 14); ctx.fill(); ctx.shadowBlur = 0; ctx.stroke();
    ctx.save(); ctx.shadowColor = a.couleur; ctx.shadowBlur = 10; ctx.strokeStyle = a.couleur; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx + 30, cy + 28, 17, 0, 6.283); ctx.stroke(); ctx.restore();
    visage(a, cx + 30, cy + 28, 15);
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
    ctx.font = '700 16px ui-sans-serif, system-ui'; ctx.fillStyle = '#fff'; ctx.fillText(a.nom, cx + 58, cy + 24);
    ctx.font = '600 12px ui-monospace, Consolas, monospace'; ctx.fillStyle = c.teinte;
    var cibleNom = c.cible ? (c.cible.fondateur ? 'FONDATEUR' : c.cible.prenom) : '';
    ctx.fillText((a.fondateur ? 'FONDATEUR' : a.id) + (cibleNom ? '  →  ' + cibleNom : '') + '    ' + c.heure, cx + 58, cy + 42);
    ctx.font = '500 16px ui-sans-serif, system-ui'; ctx.fillStyle = 'rgba(255,255,255,.95)'; lignes.forEach(function (l, i) { ctx.fillText(l, cx + 18, cy + 76 + 24 * i); });
    ctx.restore(); return true;
  }
  function couper(texte, max) { var mots = texte.split(' '), lignes = [], cur = ''; mots.forEach(function (m) { var e = (cur + ' ' + m).trim(); if (ctx.measureText(e).width > max && cur) { lignes.push(cur); cur = m; } else cur = e; }); if (cur) lignes.push(cur);
    if (lignes.length > 2) { lignes = lignes.slice(0, 2); lignes[1] = lignes[1].replace(/.{2}$/, '') + '…'; } return lignes; }
  // Anneaux dorés qui montent du fond : l'ambiance de l'aquarium de la maison.
  var anneaux = []; for (var i = 0; i < 14; i++) anneaux.push({ x: Math.random(), y: Math.random(), r: 3 + Math.random() * 9, v: 0.00008 + Math.random() * 0.00012, a: 0.15 + Math.random() * 0.3 });
  function ambiance(w, h, t) {
    anneaux.forEach(function (b) { if (!reduit) { b.y -= b.v * 16; if (b.y < -0.05) { b.y = 1.05; b.x = Math.random(); } }
      ctx.save(); ctx.globalAlpha = b.a; ctx.strokeStyle = OR; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(b.x * w + Math.sin(t / 1500 + b.r) * 6, b.y * h, b.r, 0, 6.283); ctx.stroke(); ctx.restore(); });
  }
  function horloge() {
    var d = new Date(curseur), hh = function (n) { return (n < 10 ? '0' : '') + n; };
    if (ui.horloge) ui.horloge.textContent = hh(d.getHours()) + ':' + hh(d.getMinutes()) + ':' + hh(d.getSeconds());
    if (ui.sous) ui.sous.textContent = (mode === 'direct' ? 'DIRECT' : 'REPLAY · ' + d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }).toUpperCase()) + (etat ? ' · ' + etat.executions + ' ACTIONS · ' + etat.cout_jour_eur.toFixed(2) + ' €' : '');
  }
  function dessiner(t) {
    var w = canvas.clientWidth, h = canvas.clientHeight;
    fond(w, h, t); ambiance(w, h, t); if (!etat) return; entetes(h);
    liens = liens.filter(function (l) { return lien(l, t); });
    Object.keys(noeuds).forEach(function (k) { noeud(noeuds[k], t); });
    var vivantes = []; cartes.forEach(function (c, i) { if (carte(c, t, i)) vivantes.push(c); }); cartes = vivantes;
    ctx.save(); ctx.font = '11px ui-sans-serif, system-ui'; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    [['#8ea6f0', 'échange'], ['#37b385', 'exécution'], ['#e0a21c', 'décision · fondateur']].forEach(function (lg, i) { var x = 16 + i * 120; ctx.strokeStyle = lg[0]; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, h - 16); ctx.lineTo(x + 22, h - 16); ctx.stroke(); ctx.fillStyle = 'rgba(255,255,255,.7)'; ctx.fillText(lg[1], x + 28, h - 12); });
    ctx.textAlign = 'right'; ctx.fillStyle = 'rgba(255,255,255,.45)'; ctx.fillText((canvas.getAttribute('data-mention') || 'chaque carte est une action réelle') + ' · by zelij.ai', w - 14, h - 12); ctx.restore();
    horloge();
  }
  function boucle(t) { if (dernierTick !== null) avancer(t - dernierTick); dernierTick = t; dessiner(t); if (!reduit) requestAnimationFrame(boucle); }

  // ---------- commandes
  if (ui.pause) ui.pause.addEventListener('click', function () { if (mode === 'direct') { mode = 'replay'; allerA(Date.parse(etat.depuis)); enPause = false; ui.pause.textContent = '❚❚ Pause'; }
    else { enPause = !enPause; ui.pause.textContent = enPause ? '▶ Lecture' : '❚❚ Pause'; } ui.pause.setAttribute('aria-pressed', String(!enPause)); if (reduit) dessiner(performance.now()); });
  if (ui.direct) ui.direct.addEventListener('click', function () { mode = 'direct'; enPause = false; curseur = Date.now(); cartes = []; liens = []; indexEvt = etat ? etat.evenements.length : 0; if (etat) etat.evenements.slice(-3).forEach(function (e) { jouer(e, true); }); if (ui.pause) ui.pause.textContent = '▶ Rejouer les 24 h'; if (reduit) dessiner(performance.now()); });
  if (ui.slider) ui.slider.addEventListener('input', function () { if (!etat) return; mode = 'replay'; enPause = true; if (ui.pause) ui.pause.textContent = '▶ Lecture'; allerA(parseInt(ui.slider.value, 10)); if (reduit) dessiner(performance.now()); });
  if (ui.vitesse) ui.vitesse.addEventListener('change', function () { vitesse = parseInt(ui.vitesse.value, 10) || 60; });
  canvas.addEventListener('mousemove', function (ev) { var r = canvas.getBoundingClientRect(); derniereSouris = { x: ev.clientX - r.left, y: ev.clientY - r.top }; if (reduit) dessiner(performance.now()); });
  canvas.addEventListener('mouseleave', function () { derniereSouris = { x: -1, y: -1 }; });
  canvas.addEventListener('click', function (ev) {
    var r = canvas.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top;
    Object.keys(noeuds).forEach(function (k) { var n = noeuds[k]; if (n.libre && Math.hypot(n.x - x, n.y - y) < n.r + 8) { var fiche = document.getElementById('poste-' + n.id); if (fiche) { fiche.scrollIntoView({ behavior: reduit ? 'auto' : 'smooth', block: 'center' }); fiche.classList.add('poste--vise'); setTimeout(function () { fiche.classList.remove('poste--vise'); }, 1800); } } });
  });
  window.addEventListener('resize', taille);
  taille(); charger(); setInterval(function () { if (mode === 'direct') charger(); }, 60000);
  if (tv) {
    // Mode salle d'attente (0.9.2) : plein écran au premier clic, curseur et bandeau effacés après quatre secondes sans mouvement,
    // page rechargée toutes les six heures pour suivre les mises à jour. Toujours en direct.
    var repos = null;
    function reveiller() { document.body.classList.remove('tv--repos'); clearTimeout(repos); repos = setTimeout(function () { document.body.classList.add('tv--repos'); }, 4000); }
    document.addEventListener('mousemove', reveiller); document.addEventListener('keydown', reveiller); reveiller();
    var pe = document.querySelector('[data-tv-plein-ecran]');
    if (pe) pe.addEventListener('click', function () { var el = document.documentElement; if (el.requestFullscreen) el.requestFullscreen().catch(function () {}); });
    window.addEventListener('resize', taille);
    setTimeout(function () { window.location.reload(); }, 6 * 3600 * 1000);
  }
  if (!reduit) requestAnimationFrame(boucle); else setTimeout(function () { dessiner(0); }, 400);
})();
