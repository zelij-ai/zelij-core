"""Le bureau : une page. Décisions en attente (approuver, refuser, demander des changements avec consigne obligatoire),
une demande au Chef de cabinet, le journal, le coût du mois face au plafond, les agents, les modules installés."""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core import VERSION, agents, db, demo, gouvernance, modules, passerelle, poche
from core.bureau import connexion as cx
from core.executeur import Executeur
from core.schema import migrer

logger = logging.getLogger("zelij-core")
RACINE = Path(__file__).resolve().parent
CHEF = os.environ.get("AGENT_CHEF_DE_CABINET", "chef-de-cabinet")

migrer()   # schéma prêt dès l'import : serveur et tests partent d'une base à jour


def _origine() -> str:
    return os.environ.get("APP_ORIGIN", "http://localhost:8000").rstrip("/")


async def _controle_csrf(request: Request) -> None:
    """Tout POST d'un utilisateur connecté porte le jeton de sa session (champ `_csrf` ou en-tête X-CSRF-Token) : un formulaire
    forgé depuis un autre site ne le connaît pas. Seconde barrière après le cookie SameSite=Strict et le contrôle d'origine."""
    if request.method != "POST" or request.url.path in ("/connexion", "/demo/entrer") or request.url.path.startswith(("/connexion/", "/poche/")):
        return                      # demander un lien, le confirmer, entrer dans la démonstration ou décider par lien signé : sans session
    cookie = request.cookies.get(cx.COOKIE)
    uid = cx.lire_session(cookie)
    if not uid:
        return                      # sans session, la route redirige vers la connexion
    jeton = request.headers.get("x-csrf-token")
    if not jeton:
        form = await request.form()
        jeton = str(form.get("_csrf") or "")
    if not cx.csrf_valide(uid, jeton, cx.numero_session(cookie)):
        raise HTTPException(status_code=403, detail="jeton de formulaire absent ou invalide")


app = FastAPI(title="Zelij Core", docs_url=None, redoc_url=None, openapi_url=None, dependencies=[Depends(_controle_csrf)])
app.mount("/static", StaticFiles(directory=str(RACINE / "static")), name="static")
app.state.executeur = Executeur()
templates = Jinja2Templates(directory=str(RACINE / "templates"))
templates.env.globals.update(VERSION=VERSION, ETATS=gouvernance.ETATS)

# Politique de sécurité du contenu : tout vient du bureau lui-même ; aucun script en ligne, aucun cadre, aucun envoi ailleurs.
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; "
       "form-action 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'")
EN_TETES_SECURITE = {"Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
                     "Referrer-Policy": "strict-origin-when-cross-origin", "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
                     "Cross-Origin-Opener-Policy": "same-origin", "Cross-Origin-Resource-Policy": "same-origin"}


CORPS_MAX = 2 * 1024 * 1024      # aucune requête du bureau n'approche cette taille (le plus gros envoi est un manifeste de 64 Ko)
_PUBLIC_EN_CACHE = ("/static/", "/portraits/", "/agents/")


class _CorpsTropGros(Exception):
    pass


class LimiteCorps:
    """Refuse une requête dont le corps dépasse CORPS_MAX, avant qu'il ne soit lu en mémoire ou écrit sur le disque : la taille
    annoncée d'abord, puis le compte réel des octets reçus (une taille annoncée peut mentir ou manquer)."""

    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.application(scope, receive, send)
        annonce = dict(scope.get("headers") or []).get(b"content-length", b"")
        etat = {"recu": 0, "commence": False}

        async def refuser():
            corps = "requête trop volumineuse".encode()
            en_tetes = [(b"content-type", b"text/plain; charset=utf-8"), (b"content-length", str(len(corps)).encode()), (b"connection", b"close"),
                        (b"x-content-type-options", b"nosniff"), (b"cache-control", b"no-store")]
            await send({"type": "http.response.start", "status": 413, "headers": en_tetes})
            await send({"type": "http.response.body", "body": corps})

        if annonce.isdigit() and int(annonce) > CORPS_MAX:
            return await refuser()

        async def recevoir():
            message = await receive()
            if message["type"] == "http.request":
                etat["recu"] += len(message.get("body") or b"")
                if etat["recu"] > CORPS_MAX:
                    raise _CorpsTropGros()
            return message

        async def envoyer(message):
            if message["type"] == "http.response.start":
                etat["commence"] = True
            await send(message)

        try:
            await self.application(scope, recevoir, envoyer)
        except _CorpsTropGros:
            if not etat["commence"]:
                await refuser()


app.add_middleware(LimiteCorps)


@app.middleware("http")
async def _en_tetes_securite(request: Request, call_next):
    reponse = await call_next(request)
    for k, v in EN_TETES_SECURITE.items():
        reponse.headers.setdefault(k, v)
    if not request.url.path.startswith(_PUBLIC_EN_CACHE):
        # Rien de ce que sert le bureau ne doit rester dans un cache : ni page privée, ni export, ni lien de connexion.
        reponse.headers.setdefault("Cache-Control", "no-store")
    if _origine().startswith("https"):
        reponse.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.url.path.startswith("/vitrine/"):
        # la page publique peut être encadrée par le site de l'entreprise, rien d'autre
        reponse.headers["Content-Security-Policy"] = CSP.replace("frame-ancestors 'none'", "frame-ancestors 'self' " + _origine())
        reponse.headers["X-Frame-Options"] = "SAMEORIGIN"
    return reponse

MESSAGES = {
    "lien": "Si l'adresse est valide, un lien de connexion vient d'être envoyé. Il vaut vingt minutes.",
    "lien_invalide": "Ce lien n'est plus valable. Demandez-en un nouveau.", "trop": "Trop de demandes. Réessayez dans un quart d'heure.",
    "email": "Adresse e-mail invalide.", "deconnecte": "Vous êtes déconnecté.",
    "approuvee": "Décision approuvée : l'agent peut agir.", "refusee": "Décision refusée.",
    "a_modifier": "Consigne transmise à l'agent demandeur.", "consigne": "Dis ce que tu veux changer : la consigne est transmise à l'agent demandeur.",
    "deja": "Cette décision est déjà prise.", "demande": "Demande traitée : voir la réponse ci-dessous.",
    "plafond": "Plafond mensuel atteint : aucun agent n'est appelé tant qu'il n'est pas relevé.",
    "vide": "Écrivez votre demande avant d'envoyer.",
    "smtp_absent": "L'envoi d'e-mails n'est pas configuré sur ce bureau (SMTP_HOST) : aucun lien ne peut partir.",
    "reserve": "Cette action est réservée au fondateur.",
}


def _rediriger(url: str, message: str | None = None) -> RedirectResponse:
    if message:
        url += ("&" if "?" in url else "?") + "m=" + message
    return RedirectResponse(url, status_code=303)


def _utilisateur(request: Request, c: db.Connexion) -> dict | None:
    cookie = request.cookies.get(cx.COOKIE)
    uid = cx.lire_session(cookie)
    if not uid:
        return None
    u = c.une("SELECT u.*, o.nom AS organisation FROM utilisateurs u JOIN organisations o ON o.id = u.org_id WHERE u.id = ?", (uid,))
    if u is None or int(u.get("session_n") or 0) != cx.numero_session(cookie):
        return None                 # session révoquée par une déconnexion : le cookie, même copié, ne vaut plus rien
    return u


def _origine_sure(request: Request) -> bool:
    src = request.headers.get("origin") or request.headers.get("referer") or ""
    if not src:
        return True
    hote = urlsplit(src).netloc.lower()
    return hote == (request.headers.get("host") or "").lower() or hote == urlsplit(_origine()).netloc.lower()


def _garde(request: Request, c: db.Connexion, *, fondateur: bool = False) -> tuple[dict | None, Response | None]:
    """`fondateur=True` : ce qui engage l'entreprise (décider, installer un module, ouvrir une mise en ligne, ouvrir la page
    publique) revient au fondateur. Un membre lit et demande ; il ne décide pas."""
    u = _utilisateur(request, c)
    if not u:
        return None, _rediriger("/connexion")
    if request.method == "POST" and not _origine_sure(request):
        return None, Response("origine refusée", status_code=403)
    if fondateur and u.get("role") != "fondateur":
        gouvernance.journaliser(c, u["org_id"], u["email"], "acces.refuse", request.url.path[:80], "action réservée au fondateur")
        c.commit()
        return None, _rediriger("/bureau", "reserve")
    return u, None


def _page(request: Request, nom: str, **ctx) -> HTMLResponse:
    ctx.update(request=request, message=MESSAGES.get(request.query_params.get("m", ""), ""))
    if demo.actif():
        ctx.update(demo=True, demo_bandeau=demo.BANDEAU, demo_suggestions=demo.SUGGESTIONS, demo_guide=demo.GUIDE_INSTALLATION)
    if ctx.get("u"):
        ctx["csrf"] = cx.jeton_csrf(ctx["u"]["id"], int(ctx["u"].get("session_n") or 0))
    return templates.TemplateResponse(request, nom, ctx)


@app.get("/healthz")
def healthz() -> JSONResponse:
    with db.connexion() as c:
        c.une("SELECT 1 AS un")
    return JSONResponse({"ok": True, "service": "zelij-core", "version": VERSION})


@app.get("/")
def accueil(request: Request):
    with db.connexion() as c:
        u = _utilisateur(request, c)
    return _rediriger("/bureau" if u else "/connexion")


@app.get("/connexion", response_class=HTMLResponse)
def connexion(request: Request):
    return _page(request, "connexion.html")


@app.post("/connexion")
def connexion_envoyer(request: Request, taches: BackgroundTasks, email: str = Form("")):
    if demo.actif():
        return _rediriger("/connexion")       # la démonstration n'envoie aucun e-mail : on y entre par son bouton
    e = cx.email_valide(email)
    if not e:
        return _rediriger("/connexion", "email")
    if cx.production() and not os.environ.get("SMTP_HOST", ""):
        return _rediriger("/connexion", "smtp_absent")      # rien n'est journalisé, aucun jeton n'est créé
    if not cx.demande_autorisee(e, ip=(request.client.host if request.client else "")):
        return _rediriger("/connexion", "trop")
    with db.connexion() as c:
        # Une installation = une organisation : une adresse inconnue ne reçoit rien dès que le bureau a son fondateur.
        # La réponse est la même dans les deux cas, pour ne rien apprendre à qui sonde le formulaire.
        brut = cx.creer_jeton(c, e) if cx.inscription_possible(c, e) else None
    if brut:
        sujet, corps = cx.email_connexion(f"{_origine()}/connexion/{brut}")
        # L'envoi part après la réponse : le temps de réponse est le même pour une adresse connue et pour une inconnue.
        taches.add_task(cx.envoyer_mail, e, sujet, corps)
    return _rediriger("/connexion", "lien")


@app.get("/connexion/{jeton}", response_class=HTMLResponse)
def connexion_confirmer(request: Request, jeton: str):
    """Ouvrir le lien ne connecte pas : il affiche un bouton. Un antivirus de messagerie ou un aperçu de lien qui visite
    l'adresse ne consomme donc pas le lien et n'ouvre aucune session ; seul le clic de la personne le fait."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,80}", jeton or ""):
        return _rediriger("/connexion", "lien_invalide")
    return _page(request, "connexion.html", jeton=jeton)


@app.post("/connexion/{jeton}")
def connexion_jeton(jeton: str):
    with db.connexion() as c:
        u = cx.consommer_jeton(c, jeton)
        if u:
            gouvernance.journaliser(c, u["org_id"], u["email"], "connexion")
    if not u:
        return _rediriger("/connexion", "lien_invalide")
    r = _rediriger("/bureau")
    r.set_cookie(cx.COOKIE, cx.signer_session(u["id"], n=int(u.get("session_n") or 0)), max_age=cx.DUREE_SESSION, httponly=True, samesite="strict",
                 secure=_origine().startswith("https"), path="/")
    return r


@app.post("/demo/entrer")
def demo_entrer():
    """Entrée dans la démonstration, sans e-mail : la route n'existe que si CORE_DEMO=1, et ce mode refuse de démarrer sur
    une installation réelle (voir core/demo.py)."""
    if not demo.actif():
        return Response("introuvable", status_code=404)
    uid = demo.preparer()
    with db.connexion() as c:
        u = c.une("SELECT * FROM utilisateurs WHERE id = ?", (uid,))
        gouvernance.journaliser(c, u["org_id"], u["email"], "connexion", "", "entrée dans la démonstration")
    r = _rediriger("/bureau")
    r.set_cookie(cx.COOKIE, cx.signer_session(u["id"], n=int(u.get("session_n") or 0)), max_age=cx.DUREE_SESSION, httponly=True, samesite="strict",
                 secure=_origine().startswith("https"), path="/")
    return r


@app.post("/deconnexion")
def deconnexion(request: Request):
    """Efface le cookie et révoque la session côté serveur : une copie du cookie cesse de valoir sur tous les appareils."""
    with db.connexion() as c:
        u = _utilisateur(request, c)
        if u:
            cx.revoquer_sessions(c, u["id"])
            gouvernance.journaliser(c, u["org_id"], u["email"], "deconnexion")
    r = _rediriger("/connexion", "deconnecte")
    r.delete_cookie(cx.COOKIE, path="/")
    return r


def _executions(c: db.Connexion, org_id: str, limite: int = 12) -> list[dict]:
    rows = c.lignes("SELECT * FROM executions WHERE org_id = ? ORDER BY cree_le DESC LIMIT ?", (org_id, limite))
    for r in rows:
        try:
            r["sortie_dict"] = json.loads(r["sortie"] or "{}")
        except ValueError:
            r["sortie_dict"] = {}
        r["cout_eur"] = round(float(r["cout_usd"] or 0) * passerelle.taux_usd_eur(), 4)
    return rows


@app.get("/bureau", response_class=HTMLResponse)
def bureau(request: Request):
    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        mois = db.mois_courant()
        atteint, depense, plafond = passerelle.plafond_atteint(c, u["org_id"], mois)
        fiches = agents.charger()
        return _page(request, "bureau.html", u=u, en_attente=gouvernance.en_attente(c, u["org_id"]), recentes=gouvernance.recentes(c, u["org_id"], 10),
                     journal=c.lignes("SELECT * FROM journal WHERE org_id = ? ORDER BY cree_le DESC LIMIT 40", (u["org_id"],)),
                     executions=_executions(c, u["org_id"]), fiches=list(fiches.values()), chef=fiches.get(CHEF),
                     mois=mois, depense=depense, plafond=plafond, plafond_atteint=atteint, modules=modules.installes(c, u["org_id"]),
                     tarifs_le=passerelle.TARIFS_RELEVES_LE, modele=_modele_affiche(fiches))


def _modele_affiche(fiches: dict) -> dict:
    """Ce que le compteur du bureau dit du modèle : le fournisseur, et si un tarif manque (le coût est alors compté au plus cher)."""
    try:
        d = passerelle.description()
    except RuntimeError as exc:
        return {"fournisseur": "?", "libelle": str(exc)[:80], "local": False, "sans_tarif": [], "erreur": True}
    d["sans_tarif"] = sorted({f.modele for f in fiches.values() if not passerelle.tarif_connu(f.modele)})
    return d


INSTRUCTION_DEMANDE = (
    "Demande du fondateur :\n«{demande}»\n\n"
    "Agents de ce bureau (identifiant : fonction) : {equipe}.\n"
    "Si la demande engage l'entreprise (argent, exposition publique, suppression, irréversible) ou mérite un arbitrage, prépare un "
    "paquet de décision complet ; indique dans `agent_cible` l'identifiant de l'agent qui exécutera le plan une fois approuvé (toi-même "
    "si c'est ton métier) et dans `tache` la consigne précise qu'il recevra. Sinon, réponds directement et dis ce que tu as fait ou ce "
    "que tu proposes de faire.\n"
    "Modules disponibles chez l'éditeur (ce que ce bureau ne contient pas) :\n{catalogue}\n"
    "Si la demande relève d'un de ces modules (déploiement cloud, prospection, SEO et GEO, veille des prix, surveillance, usine logicielle, "
    "hébergement), ouvre un paquet « construire soi-même ou installer le module » avec deux options réelles au moins : "
    "« Installer le module <nom> » (le fondateur l'achète chez l'éditeur, prix affiché là-bas ; mets `tache` à `catalogue:<identifiant>` "
    "et `agent_cible` à ton identifiant) et « Construire soi-même avec le Bâtisseur » (estime honnêtement le temps en jours, rappelle ses bornes : "
    "un seul dépôt, 300 lignes par demande de fusion, pas de backend, pas de nouveau service ; mets `agent_cible` à `batisseur` et `tache` à la consigne de construction). "
    "Recommande selon le temps du fondateur et la complexité, sans inventer de prix.\n"
    'Réponds en JSON strict : {{"decision_requise": true|false, "reponse": "ce que tu dis au fondateur", '
    '"objectif": "…", "proposition": "…", "pourquoi_maintenant": "…", "options": ["…", "…"], "recommandation": "…", '
    '"risques": ["…"], "reversibilite": "reversible|partielle|irreversible", "plan": ["…"], "retour_arriere": ["…"], "impact_eur": 0, '
    '"agent_cible": "identifiant ou vide", "tache": "consigne d\'exécution ou vide", '
    '"page": "seulement si tu as rédigé une page ou un article : {{title, meta_description, h1, intro, sections: [{{h2, texte}}], faq: [{{q, a}}], sources: [{{title, url}}]}}, sinon null"}}'
)
INSTRUCTION_EXECUTION = (
    "Décision approuvée par le fondateur le {jour}.\nObjectif : {objectif}\nProposition retenue : {proposition}\nPlan : {plan}\n"
    "{consigne}Ta tâche : {tache}\n\n"
    "Exécute ce qui est en ton pouvoir avec tes outils, sans dépasser le plan approuvé ; ce que tu ne peux pas faire toi-même, "
    "décris-le précisément (quoi, où, par qui). Réponds en JSON strict : "
    '{{"fait": ["…"], "reste_a_faire": ["…"], "faits_sources": [{{"fait": "…", "source_url": "…", "date": "AAAA-MM-JJ"}}], "reponse": "compte rendu au fondateur"}}'
)


def _equipe(fiches: dict) -> str:
    return ", ".join(f"{f.id} : {f.fonction}" for f in fiches.values())


@app.post("/demande")
def demande(request: Request, texte: str = Form(""), agent: str = Form("")):
    """Le fondateur parle à un agent (le Chef de cabinet par défaut). Si la demande engage, un paquet s'ouvre ; sinon une réponse."""
    texte = (texte or "").strip()[:4000]
    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        if not texte:
            return _rediriger("/bureau", "vide")
        fiches = agents.charger()
        fiche = fiches.get(agent or CHEF) or fiches.get(CHEF)
        if fiche is None:
            return Response("fiche du Chef de cabinet absente", status_code=500)
        gouvernance.journaliser(c, u["org_id"], u["email"], "demande", fiche.id, texte)
        from core import catalogue as _catalogue

        # Le contexte ne porte que le nom de l'organisation : l'adresse du fondateur n'a rien à faire devant un modèle.
        res = app.state.executeur.executer(c, u["org_id"], fiche, tache="demande-fondateur",
                                           instruction=INSTRUCTION_DEMANDE.format(demande=texte, equipe=_equipe(fiches), catalogue=_catalogue.pour_agent()),
                                           contexte={"organisation": u["organisation"]})
        if res["statut"] == "refusee" and "plafond" in res.get("detail", ""):
            return _rediriger("/bureau", "plafond")
        sortie = res.get("sortie") or {}
        page = sortie.get("page") if isinstance(sortie.get("page"), dict) else None
        if res["statut"] == "terminee" and page and (page.get("title") or page.get("h1")):
            # Une page rédigée est une exposition publique : brouillon enregistré, décision ouverte, publication sur approbation seulement.
            from core import publication

            pid = publication.enregistrer_brouillon(c, u["org_id"], page, par=fiche.signature)
            titre = str(page.get("title") or page.get("h1"))[:160]
            paquet = gouvernance.Paquet(demandeur=fiche.signature, objectif=f"Publier « {titre} » sur le site",
                                        proposition=str(page.get("meta_description") or sortie.get("reponse") or titre)[:1500],
                                        pourquoi_maintenant=str(sortie.get("pourquoi_maintenant") or "La page est prête ; elle n'est en ligne qu'après votre fusion ou votre publication.")[:600],
                                        options=["Proposer la page au site", "Garder en brouillon"], recommandation="Proposer la page au site",
                                        risques=["Exposition publique : relire les faits et les sources avant de fusionner"], reversibilite="reversible",
                                        plan=["Proposition sur le site (demande de fusion ou brouillon)", "Relecture et fusion par le fondateur"],
                                        retour_arriere=["Fermer la demande ou supprimer le brouillon"], portee="publication", execution_id=res["execution_id"],
                                        agent_cible=fiche.id, tache=f"publier:{pid}", provenance=res.get("provenance") or {})
            did = _ouvrir(c, u["org_id"], paquet)
            c.executer("UPDATE publications SET decision_id = ? WHERE id = ?", (did, pid))
            return _rediriger("/bureau", "demande")
        if res["statut"] == "terminee" and sortie.get("decision_requise"):
            paquet = gouvernance.depuis_sortie_agent(fiche.signature, sortie, execution_id=res["execution_id"], portee="demande-fondateur",
                                                     provenance=res.get("provenance") or {})
            if paquet.agent_cible not in fiches:
                paquet.agent_cible = fiche.id if paquet.tache else ""     # un agent inconnu ne peut pas être désigné
            if paquet.tache.strip().lower().startswith("publier:"):
                # « publier:<id> » est une tâche que seul le bureau écrit, sur la décision de publication qu'il ouvre lui-même.
                # Écrite par un agent, elle ferait partir un autre contenu que celui que la décision annonce : elle est retirée.
                gouvernance.journaliser(c, u["org_id"], fiche.signature, "decision.tache_retiree", res["execution_id"], "tâche de publication écrite par un agent")
                paquet.tache, paquet.agent_cible = "", ""
            manques = paquet.valider()
            if not manques:
                _ouvrir(c, u["org_id"], paquet)
            else:
                gouvernance.journaliser(c, u["org_id"], fiche.signature, "decision.incomplete", res["execution_id"], ", ".join(manques))
    return _rediriger("/bureau", "demande")


@app.get("/poche/{jeton}", response_class=HTMLResponse)
def poche_page(request: Request, jeton: str):
    """Le lien reçu par e-mail ouvre une page de confirmation : rien n'est décidé par le GET (un logiciel qui suit les liens ne
    décide rien). Le paquet est rappelé en entier ; le geste est le bouton."""
    with db.connexion() as c:
        v = poche.lire_lien(c, jeton)
        if v is None:
            return _page(request, "poche.html", etat="invalide")
        return _page(request, "poche.html", etat="confirmer", d=v["decision"], action=v["jeton"]["action"], jeton=jeton,
                     email=cx.masquer(v["jeton"]["email"]))


@app.post("/poche/{jeton}", response_class=HTMLResponse)
def poche_decider(request: Request, jeton: str):
    """Le geste : le jeton est consommé, la décision tranchée par la gouvernance et journalisée « (lien e-mail) »."""
    if not _origine_sure(request):
        return Response("origine refusée", status_code=403)
    with db.connexion() as c:
        try:
            d = poche.decider_par_lien(c, jeton, ip=request.client.host if request.client else "")
        except ValueError as exc:
            return _page(request, "poche.html", etat=str(exc) if str(exc) in ("trop", "reserve") else "invalide")
        return _page(request, "poche.html", etat="fait", d=d)


@app.post("/decisions/{decision_id}/{action}")
def decider(request: Request, decision_id: str, action: str, consigne: str = Form("")):
    with db.connexion() as c:
        u, refus = _garde(request, c, fondateur=True)
        if refus:
            return refus
        try:
            d = gouvernance.decider(c, u["org_id"], decision_id, action, par=u["email"], consigne=consigne)
        except LookupError:
            return Response("introuvable", status_code=404)
        except ValueError as exc:
            texte = str(exc)
            if "consigne" in texte:
                return _rediriger("/bureau", "consigne")
            if "déjà" in texte:
                return _rediriger("/bureau", "deja")
            return Response(texte, status_code=400)
        if d["etat"] == "approuvee" and d.get("agent_cible") and d.get("tache"):
            _executer_apres_approbation(c, u, d)
    if d["etat"] == "approuvee" and str(d.get("tache") or "").startswith("catalogue:"):
        from core import catalogue as _catalogue

        pack = d["tache"].split(":", 1)[1].strip()
        return _rediriger("/catalogue" + (f"?pack={pack}" if _catalogue.est_pack(pack) else ""), "catalogue_module")
    return _rediriger("/bureau", d["etat"])


def _ouvrir(c: db.Connexion, org_id: str, paquet) -> str:
    """Ouvre la décision et prévient le fondateur là où il est (e-mail avec liens signés, Telegram) : « Dans la poche », 0.9.0.
    Une notification qui échoue n'empêche jamais la décision d'exister : elle attend dans le bureau."""
    did = gouvernance.ouvrir(c, org_id, paquet)
    try:
        poche.prevenir(c, org_id, did)
    except Exception:  # noqa: BLE001
        logger.exception("Dans la poche : notification impossible pour la décision %s", did)
    return did


def _executer_apres_approbation(c: db.Connexion, u: dict, d: dict) -> None:
    """Une décision approuvée qui désigne un agent et une tâche se met en route aussitôt, dans les limites du plan approuvé."""
    if d["tache"].startswith("catalogue:"):
        # « Installer le module » : rien ne s'achète ici ; le bureau note la décision et conduit le fondateur au catalogue, lien d'achat prêt.
        from core import catalogue as _catalogue

        pack = d["tache"].split(":", 1)[1].strip()
        gouvernance.journaliser(c, u["org_id"], "bureau", "catalogue.module", d["id"], f"décision d'installer le module {pack} : achat chez l'éditeur" if _catalogue.est_pack(pack) else f"module inconnu {pack[:40]}")
        return
    if d["tache"].startswith("publier:"):
        from core import publication

        pid = d["tache"].split(":", 1)[1].strip()
        pub = publication.lire(c, u["org_id"], pid)
        if d.get("portee") != "publication" or pub is None or pub.get("decision_id") != d["id"]:
            # La page qui part est celle que cette décision présentait, et aucune autre.
            gouvernance.journaliser(c, u["org_id"], "bureau", "publication.refusee", d["id"], "la tâche désigne une page qui n'est pas celle de cette décision")
            return
        res = publication.publier(c, u["org_id"], pid, par=u["email"])
        gouvernance.journaliser(c, u["org_id"], "bureau", "publication.apres_approbation", d["id"], res.get("detail", "")[:160])
        return
    fiche = agents.charger().get(d["agent_cible"])
    if fiche is None:
        gouvernance.journaliser(c, u["org_id"], "bureau", "execution.impossible", d["id"], f"agent {d['agent_cible']} inconnu")
        return
    consigne = f"Consigne du fondateur : {d['consigne']}\n" if d.get("consigne") else ""
    instruction = INSTRUCTION_EXECUTION.format(jour=db.maintenant()[:10], objectif=d["objectif"], proposition=d["proposition"],
                                               plan=" → ".join(d.get("plan") or []) or "—", consigne=consigne, tache=d["tache"])
    res = app.state.executeur.executer(c, u["org_id"], fiche, tache=f"decision-{d['id'][:8]}", instruction=instruction,
                                       contexte={"organisation": u["organisation"], "decision_id": d["id"], "portee": d.get("portee") or ""})
    c.executer("UPDATE decisions SET execution_apres = ? WHERE id = ? AND org_id = ?", (res["execution_id"], d["id"], u["org_id"]))
    gouvernance.journaliser(c, u["org_id"], fiche.signature, "execution.apres_approbation", d["id"], f"{res['statut']} · {res['detail'] or 'plan en cours'}")


# ------------------------------------------------------------------ lot 3 : finances

MESSAGES.update({
    "charge": "Charge déclarée.", "vente": "Vente enregistrée avec sa preuve.", "vente_doublon": "Cette référence existe déjà : rien n'a été ajouté.",
    "saisie": "Saisie refusée : vérifiez la date, le montant et les champs obligatoires.", "stripe_absent": "Clé Stripe absente : rien n'a été importé.",
    "contact": "Fiche créée.", "contact_refus": "Fiche refusée : base légale, rôle ou adresse manquants, ou contact déjà présent.",
    "echange": "Échange ajouté.", "oppose": "Ce contact s'est opposé : aucun message sortant.", "droit": "Droit enregistré.", "oubli": "Fiches échues oubliées.",
})


def _mois_valide(v: str | None) -> str:
    v = (v or "").strip()[:7]
    import re as _re

    return v if _re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", v) else db.mois_courant()      # ce siècle : une année 0000 ou 9999 n'a pas de calendrier


@app.get("/finances", response_class=HTMLResponse)
def finances(request: Request, mois: str = ""):
    from core import compta

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        j = compta.journal(c, u["org_id"], _mois_valide(mois))
        return _page(request, "finances.html", u=u, j=j, categories=compta.CATEGORIES, periodicites=compta.PERIODICITES,
                     stripe_pret=bool(os.environ.get("STRIPE_SECRET_KEY")))


@app.get("/finances/export")
def finances_export(request: Request, mois: str = ""):
    from core import compta

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        j = compta.journal(c, u["org_id"], _mois_valide(mois))
        gouvernance.journaliser(c, u["org_id"], u["email"], "finances.export", j["mois"])
    return Response(compta.export_csv(j), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename=journal-{j['mois']}.csv"})


@app.post("/finances/charges")
async def finances_charge(request: Request):
    from core import compta

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        f = await request.form()
        try:
            charge = compta.valider_charge(date_=str(f.get("date") or ""), libelle=str(f.get("libelle") or ""), montant_eur=str(f.get("montant_eur") or ""),
                                           categorie=str(f.get("categorie") or ""), periodicite=str(f.get("periodicite") or ""),
                                           jusqu_a=str(f.get("jusqu_a") or ""), piece=str(f.get("piece") or ""))
        except ValueError:
            return _rediriger("/finances", "saisie")
        compta.ajouter_charge(c, u["org_id"], charge, par=u["email"])
    return _rediriger(f"/finances?mois={charge['date'][:7]}", "charge")


@app.post("/finances/ventes")
async def finances_vente(request: Request):
    from core import compta

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        f = await request.form()
        try:
            v = compta.valider_charge(date_=str(f.get("date") or ""), libelle=str(f.get("libelle") or ""), montant_eur=str(f.get("montant_eur") or ""),
                                      categorie="autre", periodicite="unique")
            reference = str(f.get("reference") or "").strip()
            if not reference:
                raise ValueError("preuve manquante")
        except ValueError:
            return _rediriger("/finances", "saisie")
        ok = compta.ajouter_vente(c, u["org_id"], source="manuel", reference=reference, date_=v["date"], libelle=v["libelle"], montant_eur=v["montant_eur"],
                                  client=str(f.get("client") or ""), par=u["email"])
    return _rediriger(f"/finances?mois={v['date'][:7]}", "vente" if ok else "vente_doublon")


@app.post("/finances/stripe")
def finances_stripe(request: Request):
    from core import compta

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        res = compta.importer_stripe(c, u["org_id"], par=u["email"])
        gouvernance.journaliser(c, u["org_id"], u["email"], "finances.import_stripe", "", f"{res['importees']} vente(s) sur {res['lues']} lue(s)" + (f" · {res['erreur']}" if res["erreur"] else ""))
    if res["erreur"] and "absente" in res["erreur"]:
        return _rediriger("/finances", "stripe_absent")
    return _rediriger("/finances", "vente" if res["importees"] else "vente_doublon")


# ------------------------------------------------------------------ lot 3 : contacts

@app.get("/contacts", response_class=HTMLResponse)
def contacts(request: Request, filtre: str = "actifs", fiche: str = ""):
    from core import crm

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        filtre = filtre if filtre in ("actifs", "a_traiter", "oublies", "tous") else "actifs"
        tous = crm.liste(c, u["org_id"])
        detail = next((x for x in tous if x["id"] == fiche), None) if fiche else None
        return _page(request, "contacts.html", u=u, contacts=crm.liste(c, u["org_id"], filtre=filtre), filtre=filtre, fiche=detail,
                     echanges=crm.echanges(c, u["org_id"], fiche) if detail else [], droits=crm.droits(c, u["org_id"], fiche) if detail else [],
                     roles=crm.ROLES, bases=crm.BASES_LEGALES, a_oublier=[x for x in tous if x["a_oublier"]])


@app.post("/contacts")
async def contact_creer(request: Request):
    from core import crm

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        f = await request.form()
        try:
            cid = crm.creer_contact(c, u["org_id"], email=str(f.get("email") or ""), nom=str(f.get("nom") or ""), entreprise=str(f.get("entreprise") or ""),
                                    role=str(f.get("role") or ""), base_legale=str(f.get("base_legale") or ""), source=str(f.get("source") or ""),
                                    conservation_mois=str(f.get("conservation_mois") or ""), par=u["email"])
        except ValueError:
            return _rediriger("/contacts", "contact_refus")
    return _rediriger(f"/contacts?fiche={cid}", "contact")


@app.post("/contacts/{cid}/echanges")
def contact_echange(request: Request, cid: str, sens: str = Form("note"), canal: str = Form(""), resume: str = Form("")):
    from core import crm

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        try:
            crm.ajouter_echange(c, u["org_id"], cid, sens=sens, canal=canal, resume=resume, par=u["email"])
        except LookupError:
            return Response("introuvable", status_code=404)
        except PermissionError:
            return _rediriger(f"/contacts?fiche={cid}", "oppose")
        except ValueError:
            return _rediriger(f"/contacts?fiche={cid}", "saisie")
    return _rediriger(f"/contacts?fiche={cid}", "echange")


@app.post("/contacts/{cid}/droits")
def contact_droit(request: Request, cid: str, type: str = Form(""), detail: str = Form("")):
    from core import crm

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        try:
            crm.exercer_droit(c, u["org_id"], cid, type_=type, par=u["email"], detail=detail)
        except LookupError:
            return Response("introuvable", status_code=404)
        except ValueError:
            return Response("droit inconnu", status_code=400)
    return _rediriger(f"/contacts?fiche={cid}", "droit")


@app.post("/contacts/oublier")
def contacts_oublier(request: Request):
    from core import crm

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        for ct in crm.liste(c, u["org_id"], filtre="a_traiter"):
            if ct["a_oublier"]:
                crm.oublier(c, u["org_id"], ct["id"], par=u["email"], motif="durée de conservation échue")
    return _rediriger("/contacts?filtre=oublies", "oubli")


# ------------------------------------------------------------------ lot 4 : aquarium, vitrine publique, catalogue, modules, publications

MESSAGES.update({
    "vitrine": "Page publique créée : le lien est prêt à partager.", "vitrine_fermee": "Lien public coupé.",
    "module": "Module vérifié et installé.", "module_refus": "Module refusé : signature absente ou invalide, ou interface incompatible.",
    "manifeste": "Manifeste illisible.",
    "catalogue_module": "Décision approuvée : le module s'achète chez l'éditeur, son lien est prêt ci-dessous ; une fois le colis reçu, installez-le ici.",
})


@app.get("/aquarium", response_class=HTMLResponse)
def aquarium_page(request: Request):
    from core import aquarium, catalogue

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        fiches = agents.charger()
        return _page(request, "aquarium.html", u=u, etat=aquarium.etat(c, u["org_id"], fiches), jeton=aquarium.jeton_public(c, u["org_id"]),
                     postes=catalogue.POSTES_LIBRES, origine=_origine())


@app.get("/api/aquarium")
def aquarium_api(request: Request):
    from core import aquarium

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return JSONResponse({"erreur": "connexion requise"}, status_code=401)
        return JSONResponse(aquarium.etat(c, u["org_id"], agents.charger()))


@app.post("/vitrine/ouvrir")
def vitrine_ouvrir(request: Request):
    from core import aquarium

    with db.connexion() as c:
        u, refus = _garde(request, c, fondateur=True)
        if refus:
            return refus
        aquarium.ouvrir_vitrine(c, u["org_id"], par=u["email"])
    return _rediriger("/aquarium", "vitrine")


@app.post("/vitrine/fermer")
def vitrine_fermer(request: Request):
    from core import aquarium

    with db.connexion() as c:
        u, refus = _garde(request, c, fondateur=True)
        if refus:
            return refus
        aquarium.fermer_vitrine(c, u["org_id"], par=u["email"])
    return _rediriger("/aquarium", "vitrine_fermee")


@app.get("/vitrine/{jeton}", response_class=HTMLResponse)
def vitrine(request: Request, jeton: str):
    """Page publique : pas de connexion, rien d'interne, le badge de l'éditeur."""
    from core import aquarium

    with db.connexion() as c:
        org = aquarium.organisation_par_jeton(c, jeton)
        if org is None:
            return Response("page introuvable", status_code=404)
        etat = aquarium.etat(c, org["id"], agents.charger(), public=True)
    return templates.TemplateResponse(request, "vitrine.html", {"request": request, "organisation": org["nom"], "etat": etat, "jeton": jeton,
                                                                "demo": demo.actif(), "demo_bandeau": demo.BANDEAU})


@app.get("/api/vitrine/{jeton}")
def vitrine_api(jeton: str):
    from core import aquarium

    with db.connexion() as c:
        org = aquarium.organisation_par_jeton(c, jeton)
        if org is None:
            return JSONResponse({"erreur": "introuvable"}, status_code=404)
        return JSONResponse(aquarium.etat(c, org["id"], agents.charger(), public=True))


@app.get("/catalogue", response_class=HTMLResponse)
def catalogue_page(request: Request, pack: str = ""):
    from core import INTERFACE_MODULES, catalogue

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        instance = u["org_id"][:12]
        return _page(request, "catalogue.html", u=u, packs=catalogue.PACKS, liens={p["id"]: catalogue.lien_achat(p["id"], instance) for p in catalogue.PACKS},
                     modules=modules.installes(c, u["org_id"]), interface=INTERFACE_MODULES, cle_presente=bool(modules.cle_publique_editeur()), instance=instance,
                     cible=pack if catalogue.est_pack(pack) else "")


@app.post("/modules/installer")
async def module_installer(request: Request):
    import tempfile
    from pathlib import Path as _Path

    with db.connexion() as c:
        u, refus = _garde(request, c, fondateur=True)
        if refus:
            return refus
        form = await request.form()
        fichier = form.get("manifeste")
        contenu = await fichier.read() if fichier is not None and hasattr(fichier, "read") else b""
        if not contenu or len(contenu) > 64 * 1024:
            return _rediriger("/catalogue", "manifeste")
        with tempfile.TemporaryDirectory() as d:
            chemin = _Path(d) / "pack.json"
            chemin.write_bytes(contenu)
            try:
                m = modules.charger_manifeste(chemin)
            except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
                return _rediriger("/catalogue", "manifeste")
        res = modules.installer(c, u["org_id"], m, par=u["email"])
    return _rediriger("/catalogue", "module" if res.get("installe") else "module_refus")


@app.get("/publications", response_class=HTMLResponse)
def publications_page(request: Request):
    from core import publication

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        return _page(request, "publications.html", u=u, publications=publication.liste(c, u["org_id"]), canal=(publication.configuration() or {}).get("canal"))


PORTRAITS = RACINE.parents[1] / "portraits"      # dossier des photos (fondateur.webp, <agent>.webp) ; monté en lecture seule avec Docker
_FORMATS_PORTRAIT = (("webp", "image/webp"), ("png", "image/png"), ("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("svg", "image/svg+xml"))


def _fichier_portrait(nom: str) -> tuple[Path, str] | None:
    """Le premier fichier trouvé pour un nom : la photo (webp, png, jpg) avant la silhouette (svg)."""
    for ext, media in _FORMATS_PORTRAIT:
        chemin = PORTRAITS / f"{nom}.{ext}"
        if chemin.is_file():
            return chemin, media
    return None


def _reponse_portrait(chemin: Path, media: str) -> FileResponse:
    return FileResponse(str(chemin), media_type=media, headers={"Cache-Control": "public, max-age=300"})


@app.get("/portraits/{nom}")
def portrait_dossier(nom: str):
    """Une photo du dossier portraits/ : `fondateur` (silhouette fournie, à remplacer par votre photo) ou un identifiant d'agent."""
    if not re.fullmatch(r"[a-z0-9-]{1,60}", nom or ""):
        return Response("introuvable", status_code=404)
    trouve = _fichier_portrait(nom)
    if trouve is None:
        return Response("introuvable", status_code=404)
    return _reponse_portrait(*trouve)


@app.get("/agents/{agent_id}/portrait")
def portrait(agent_id: str):
    """Portrait d'un agent : d'abord VOTRE photo dans portraits/<id>.*, puis celle livrée avec la fiche (agents/<id>/portrait.*,
    les quatre agents de l'édition arrivent avec un portrait de personnage fictif) ; sinon 404 et le bassin dessine un monogramme."""
    if not re.fullmatch(r"[a-z0-9-]{1,60}", agent_id or ""):
        return Response("introuvable", status_code=404)
    trouve = _fichier_portrait(agent_id)
    if trouve is not None:
        return _reponse_portrait(*trouve)
    for ext, media in _FORMATS_PORTRAIT[:4]:
        chemin = agents.DOSSIER_AGENTS / agent_id / f"portrait.{ext}"
        if chemin.exists():
            return _reponse_portrait(chemin, media)
    return Response("introuvable", status_code=404)


# ------------------------------------------------------------------ lot 5 : software factory

MESSAGES.update({
    "sonde": "Relevé du domaine fait.", "sauvegarde": "Sauvegarde du bureau faite.", "sauvegarde_echec": "Sauvegarde impossible : voir le détail sur la page.",
    "mise_en_ligne": "Décision ouverte : la mise en ligne partira dès votre approbation.", "cible_absente": "Cible ou dépôt non configurés : rien à mettre en ligne.",
})


def _contexte_batir(c, u: dict, sonde=None) -> dict:
    from core import cibles, depot, sauvegarde
    from core.cibles import ovh

    module = cibles.charger()
    conf = module.configuration()
    versions = module.versions() if conf else {"ok": False, "versions": [], "courante": None, "detail": "cible non configurée"}
    return {"u": u, "depot": depot.configuration() is not None, "cible_nom": cibles.CIBLES[cibles.cible_active()]["nom"], "cible_ok": conf is not None,
            "versions": versions, "sauvegardes": sauvegarde.liste(), "sonde": sonde, "panier": ovh.preparer_panier(os.environ.get("SITE_DOMAINE", "").replace("https://", "").strip("/") or None),
            "pret": conf is not None and depot.configuration() is not None}


@app.get("/batir", response_class=HTMLResponse)
def batir(request: Request):
    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        return _page(request, "batir.html", **_contexte_batir(c, u))


@app.post("/batir/sonde", response_class=HTMLResponse)
def batir_sonde(request: Request):
    from core.cibles import sonde as module_sonde

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        releve = module_sonde.sonder(os.environ.get("SITE_DOMAINE", ""))
        gouvernance.journaliser(c, u["org_id"], u["email"], "sonde", releve.get("domaine", ""), "; ".join(releve.get("constats") or ["tout répond"])[:300])
        return _page(request, "batir.html", **_contexte_batir(c, u, sonde=releve))


@app.post("/batir/sauvegarde")
def batir_sauvegarde(request: Request):
    from core import sauvegarde

    with db.connexion() as c:
        u, refus = _garde(request, c)
        if refus:
            return refus
        res = sauvegarde.sauvegarder()
        gouvernance.journaliser(c, u["org_id"], u["email"], "sauvegarde", res.get("fichier", ""), res.get("detail", "")[:200])
    return _rediriger("/batir", "sauvegarde" if res.get("ok") else "sauvegarde_echec")


@app.post("/batir/deployer")
def batir_deployer(request: Request):
    """Une mise en ligne engage : elle passe par un paquet de décision ; approuvée, le Bâtisseur l'exécute avec deployer_site."""
    from core import cibles, depot

    with db.connexion() as c:
        u, refus = _garde(request, c, fondateur=True)
        if refus:
            return refus
        if cibles.charger().configuration() is None or depot.configuration() is None:
            return _rediriger("/batir", "cible_absente")
        fiche = agents.charger().get("batisseur")
        if fiche is None:
            return Response("fiche du Bâtisseur absente", status_code=500)
        paquet = gouvernance.Paquet(demandeur=fiche.signature, objectif="Mettre en ligne la branche principale du site",
                                    proposition=f"Déployer la version fusionnée du dépôt sur {cibles.CIBLES[cibles.cible_active()]['nom']} : bascule atomique, test de fumée, retour arrière automatique.",
                                    pourquoi_maintenant="Demande du fondateur depuis la page Software factory.", options=["Mettre en ligne maintenant", "Attendre"],
                                    recommandation="Mettre en ligne maintenant", risques=["Exposition publique de ce qui est fusionné sur la branche principale"],
                                    reversibilite="reversible", plan=["Archive de la branche principale", "Envoi et dépliage dans une nouvelle version", "Bascule", "Test de fumée", "Ménage des anciennes versions"],
                                    retour_arriere=["Retour automatique à la version précédente si la fumée échoue", "Bascule manuelle vers une version gardée"],
                                    portee="mise-en-ligne", agent_cible="batisseur", tache="Mets en ligne la branche principale avec l'outil deployer_site, puis relève le domaine avec sonder_domaine et rends compte.")
        _ouvrir(c, u["org_id"], paquet)
    return _rediriger("/bureau", "mise_en_ligne")


from core import sauvegarde as _sauvegarde  # noqa: E402

_sauvegarde.demarrer_fil()
# « Dans la poche » (0.9.0) : ce qui suit une approbation est le même, qu'elle vienne du bureau, d'un lien ou de Telegram.
poche.configurer(apres_approbation=_executer_apres_approbation, envoyer_mail=cx.envoyer_mail)
poche.demarrer_fil()

if demo.actif():
    demo.demarrer(app)      # refuse de démarrer en production, sur PostgreSQL, ou sur une base qui porte une organisation réelle
