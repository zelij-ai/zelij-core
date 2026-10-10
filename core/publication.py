"""Publication : une page écrite par l'agent Croissance devient une proposition sur le site du fondateur, jamais une mise en
ligne directe. Deux canaux : une demande de fusion sur le dépôt GitHub du site (jeton restreint à ce dépôt) ou un brouillon
WordPress (compte auteur, mot de passe d'application). Le fondateur fusionne ou publie lui-même : le dernier geste est à lui."""
from __future__ import annotations

import base64
import html
import json
import os
import re
from datetime import date

import httpx

from core import db

_TIMEOUT = httpx.Timeout(40.0)
_API = "https://api.github.com"
ETATS = {"brouillon": "Brouillon", "proposee": "Proposée au site", "en_ligne": "En ligne", "echec": "Échec"}


def configuration() -> dict | None:
    """Le canal vient de l'environnement : dépôt GitHub (SITE_DEPOT + GITHUB_TOKEN) ou WordPress (WP_URL + WP_USER + WP_APP_PASSWORD)."""
    depot, jeton = os.environ.get("SITE_DEPOT", "").strip(), os.environ.get("GITHUB_TOKEN", "").strip()
    if depot and jeton and "/" in depot:
        prefixe = "/" + os.environ.get("SITE_PREFIXE", "/").strip().strip("/")
        return {"canal": "pr", "depot": depot, "jeton": jeton, "prefixe": prefixe if prefixe != "/" else "", "gabarit": os.environ.get("SITE_GABARIT", "_gabarit/page.html"),
                "domaine": os.environ.get("SITE_DOMAINE", "").strip().rstrip("/")}
    url, user, mdp = os.environ.get("WP_URL", "").strip().rstrip("/"), os.environ.get("WP_USER", "").strip(), os.environ.get("WP_APP_PASSWORD", "").strip()
    if url and user and mdp:
        return {"canal": "wordpress", "url": url, "user": user, "mdp": mdp}
    return None


def slug_sur(valeur: str) -> str:
    import unicodedata

    sans_accents = unicodedata.normalize("NFKD", valeur or "").encode("ascii", "ignore").decode()
    v = re.sub(r"[^a-z0-9]+", "-", sans_accents.lower()).strip("-")
    return v[:80] or "page"


def _esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def rendre_corps(page: dict, jour: date | None = None) -> str:
    """Intro, sections, questions fréquentes, sources datées. Texte échappé : aucun HTML brut ne passe."""
    jour = jour or date.today()
    parties = []
    intro = str(page.get("intro") or "").strip()
    if intro:
        parties.append('<p class="intro">' + "</p><p class=\"intro\">".join(_esc(p.strip()) for p in intro.split("\n") if p.strip()) + "</p>")
    for s in page.get("sections") or []:
        if not isinstance(s, dict):
            continue
        texte = str(s.get("texte") or s.get("text") or "")
        paras = "".join(f"<p>{_esc(p.strip())}</p>" for p in texte.split("\n") if p.strip())
        parties.append(f"<section><h2>{_esc(s.get('h2') or s.get('titre') or '')}</h2>{paras}</section>")
    faq = [f for f in (page.get("faq") or []) if isinstance(f, dict) and f.get("q") and f.get("a")]
    if faq:
        parties.append("<section><h2>Questions fréquentes</h2>" + "".join(f"<h3>{_esc(f['q'])}</h3><p>{_esc(f['a'])}</p>" for f in faq) + "</section>")
    # Une source est une adresse https : tout autre protocole (javascript:, data:…) est écarté, il finirait en lien sur le site public.
    sources = [s for s in (page.get("sources") or []) if isinstance(s, dict) and str(s.get("url") or "").strip().lower().startswith("https://")]
    if sources:
        items = "".join(f'<li><a href="{_esc(s["url"])}" rel="noopener">{_esc(s.get("title") or s.get("titre") or s["url"])}</a></li>' for s in sources)
        parties.append(f"<section><h2>Sources</h2><ul>{items}</ul></section>")
    parties.append(f"<p><small>Faits vérifiés le {jour.strftime('%d/%m/%Y')}.</small></p>")
    return "\n".join(parties)


def rendre_page(gabarit: str | None, page: dict, *, url: str, jour: date | None = None) -> str:
    """Avec un gabarit du site (`{{titre}}`, `{{description}}`, `{{h1}}`, `{{corps}}`, `{{url}}`, `{{date}}`) ; sinon une page autonome sobre."""
    jour = jour or date.today()
    champs = {"titre": _esc(page.get("title")), "description": _esc(page.get("meta_description")), "h1": _esc(page.get("h1") or page.get("title")),
              "corps": rendre_corps(page, jour), "url": _esc(url), "date": jour.isoformat()}
    if gabarit and "{{corps}}" in gabarit:
        out = gabarit
        for k, v in champs.items():
            out = out.replace("{{" + k + "}}", v)
        return out
    return ("<!doctype html>\n<html lang=\"fr\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{champs['titre']}</title>\n<meta name=\"description\" content=\"{champs['description']}\">\n<link rel=\"canonical\" href=\"{champs['url']}\">\n"
            "</head>\n<body>\n<main>\n" f"<h1>{champs['h1']}</h1>\n{champs['corps']}\n</main>\n</body>\n</html>\n")


# ---------------------------------------------------------------- registre des publications

def enregistrer_brouillon(c: db.Connexion, org_id: str, page: dict, *, par: str) -> str:
    from core.gouvernance import journaliser

    titre = str(page.get("title") or page.get("h1") or "Page sans titre")[:200]
    pid = db.nouvel_id()
    c.executer("INSERT INTO publications (id, org_id, slug, titre, canal, page, etat, cree_le) VALUES (?,?,?,?,?,?,?,?)",
               (pid, org_id, slug_sur(page.get("slug") or titre), titre, (configuration() or {}).get("canal", ""), json.dumps(page, ensure_ascii=False)[:60000],
                "brouillon", db.maintenant()))
    journaliser(c, org_id, par, "publication.brouillon", pid, titre)
    return pid


def lire(c: db.Connexion, org_id: str, pub_id: str) -> dict | None:
    r = c.une("SELECT * FROM publications WHERE id = ? AND org_id = ?", (pub_id, org_id))
    if r:
        try:
            r["page_dict"] = json.loads(r["page"] or "{}")
        except ValueError:
            r["page_dict"] = {}
        r["etat_libelle"] = ETATS.get(r["etat"], r["etat"])
    return r


def liste(c: db.Connexion, org_id: str, limite: int = 30) -> list[dict]:
    rows = c.lignes("SELECT * FROM publications WHERE org_id = ? ORDER BY cree_le DESC LIMIT ?", (org_id, limite))
    for r in rows:
        r["etat_libelle"] = ETATS.get(r["etat"], r["etat"])
    return rows


# ---------------------------------------------------------------- canaux

def _gh(jeton: str) -> dict:
    return {"Authorization": f"Bearer {jeton}", "Accept": "application/vnd.github+json", "User-Agent": "zelij-core"}


def publier_par_pr(conf: dict, pub: dict, *, client: httpx.Client | None = None) -> dict:
    """Branche `agents/<slug>`, fichier `<prefixe>/<slug>/index.html`, demande de fusion. Rien n'est fusionné."""
    propre = client is None
    client = client or httpx.Client(timeout=_TIMEOUT)
    h = _gh(conf["jeton"])
    depot, slug = conf["depot"], pub["slug"]
    try:
        r = client.get(f"{_API}/repos/{depot}", headers=h)
        if r.status_code != 200:
            return {"ok": False, "detail": f"dépôt inaccessible ({r.status_code}) : jeton restreint à ce dépôt ?"}
        principale = r.json().get("default_branch") or "main"
        r = client.get(f"{_API}/repos/{depot}/git/ref/heads/{principale}", headers=h)
        if r.status_code != 200:
            return {"ok": False, "detail": f"branche {principale} introuvable ({r.status_code})"}
        sha = r.json()["object"]["sha"]
        gabarit = None
        g = client.get(f"{_API}/repos/{depot}/contents/{conf['gabarit']}", headers=h, params={"ref": principale})
        if g.status_code == 200 and g.json().get("content"):
            gabarit = base64.b64decode(g.json()["content"]).decode("utf-8", errors="replace")
        chemin = f"{conf['prefixe'].strip('/')}/{slug}/index.html".lstrip("/")
        url = f"{conf['domaine']}/{chemin.removesuffix('index.html')}" if conf.get("domaine") else "/" + chemin.removesuffix("index.html")
        contenu = rendre_page(gabarit, pub["page_dict"], url=url)
        branche = f"agents/{slug}-{pub['id'][:6]}"
        r = client.post(f"{_API}/repos/{depot}/git/refs", headers=h, json={"ref": f"refs/heads/{branche}", "sha": sha})
        if r.status_code not in (200, 201):
            return {"ok": False, "detail": f"création de branche refusée ({r.status_code})"}
        r = client.put(f"{_API}/repos/{depot}/contents/{chemin}", headers=h,
                       json={"message": f"Page proposée par l'agent Croissance : {pub['titre'][:80]}", "branch": branche,
                             "content": base64.b64encode(contenu.encode("utf-8")).decode()})
        if r.status_code not in (200, 201):
            return {"ok": False, "detail": f"écriture du fichier refusée ({r.status_code})"}
        corps = (f"Page proposée par l'agent Croissance, à relire avant fusion. Chemin : `{chemin}`.\n\n"
                 f"{pub['page_dict'].get('meta_description', '')}\n\nSources citées : {len(pub['page_dict'].get('sources') or [])}. "
                 "Rien n'est en ligne tant que cette demande n'est pas fusionnée.")
        r = client.post(f"{_API}/repos/{depot}/pulls", headers=h, json={"title": f"Page : {pub['titre'][:90]}", "head": branche, "base": principale, "body": corps})
        if r.status_code not in (200, 201):
            return {"ok": False, "detail": f"demande de fusion refusée ({r.status_code})"}
        return {"ok": True, "url": r.json().get("html_url", ""), "detail": f"demande de fusion n° {r.json().get('number')} sur {depot}"}
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return {"ok": False, "detail": f"GitHub injoignable : {str(exc)[:160]}"}
    finally:
        if propre:
            client.close()


def publier_wordpress(conf: dict, pub: dict, *, client: httpx.Client | None = None) -> dict:
    propre = client is None
    client = client or httpx.Client(timeout=_TIMEOUT)
    page = pub["page_dict"]
    jeton = base64.b64encode(f"{conf['user']}:{conf['mdp']}".encode()).decode()
    charge = {"title": pub["titre"], "slug": pub["slug"], "status": "draft", "content": rendre_corps(page), "excerpt": str(page.get("meta_description") or "")[:300],
              "comment_status": "closed"}
    try:
        r = client.post(f"{conf['url']}/wp-json/wp/v2/posts", headers={"Authorization": f"Basic {jeton}", "Accept": "application/json"}, json=charge)
        if r.status_code not in (200, 201):
            return {"ok": False, "detail": f"WordPress a refusé ({r.status_code})"}
        return {"ok": True, "url": r.json().get("link", ""), "detail": f"brouillon WordPress n° {r.json().get('id')}"}
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "detail": f"WordPress injoignable : {str(exc)[:160]}"}
    finally:
        if propre:
            client.close()


def publier(c: db.Connexion, org_id: str, pub_id: str, *, par: str, client: httpx.Client | None = None) -> dict:
    """Exécute la décision du fondateur : la page part vers le site, comme proposition. L'état et le détail sont enregistrés."""
    from core.gouvernance import journaliser

    pub = lire(c, org_id, pub_id)
    if pub is None:
        return {"ok": False, "detail": "publication introuvable"}
    conf = configuration()
    if conf is None:
        res = {"ok": False, "detail": "aucun canal de publication configuré (SITE_DEPOT + GITHUB_TOKEN, ou WP_URL + WP_USER + WP_APP_PASSWORD)"}
    elif conf["canal"] == "pr":
        res = publier_par_pr(conf, pub, client=client)
    else:
        res = publier_wordpress(conf, pub, client=client)
    etat = "proposee" if res.get("ok") else "echec"
    c.executer("UPDATE publications SET etat = ?, canal = ?, reference = ?, detail = ?, publie_le = ? WHERE id = ? AND org_id = ?",
               (etat, (conf or {}).get("canal", ""), res.get("url", ""), res.get("detail", "")[:400], db.maintenant() if res.get("ok") else None, pub_id, org_id))
    journaliser(c, org_id, par, f"publication.{etat}", pub_id, res.get("detail", "")[:160])
    return res
