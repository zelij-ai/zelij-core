"""Outillage de l'éditeur : signer le manifeste d'un module avec la clé privée Ed25519, ou générer la paire de clés.
La clé privée vit sur le poste de l'éditeur (variable ZELIJ_CLE_PRIVEE, hexadécimal) et nulle part ailleurs ; seule la clé
publique entre dans les installations (ZELIJ_CLE_PUBLIQUE).

  python scripts/signer_module.py cles                      → affiche une nouvelle paire (privée, publique)
  python scripts/signer_module.py signer chemin/pack.json   → calcule l'empreinte de chaque fichier du dossier, écrit `fichiers` et la signature
  python scripts/signer_module.py verifier chemin/pack.json → vérifie la signature (ZELIJ_CLE_PUBLIQUE) et les empreintes des fichiers"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import modules  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("cles", "signer", "verifier"):
        print(__doc__)
        return 2
    if argv[0] == "cles":
        priv, pub = modules.generer_cles()
        print("ZELIJ_CLE_PRIVEE=" + priv + "   # à garder chez l'éditeur, jamais dans un dépôt ni une installation")
        print("ZELIJ_CLE_PUBLIQUE=" + pub)
        return 0
    chemin = Path(argv[1])
    m = modules.charger_manifeste(chemin)
    if argv[0] == "signer":
        priv = os.environ.get("ZELIJ_CLE_PRIVEE", "").strip()
        if not priv:
            print("ZELIJ_CLE_PRIVEE absente de l'environnement")
            return 1
        m.fichiers = modules.empreintes_dossier(chemin.parent)
        m.signature = modules.signer(m, priv)
        d = json.loads(chemin.read_text(encoding="utf-8"))
        d["fichiers"], d["signature"] = m.fichiers, m.signature
        chemin.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{chemin} signé ({m.nom} {m.version}, {len(m.fichiers)} fichier(s) couvert(s))")
        return 0
    ok = modules.verifier(m)
    ecarts = modules.verifier_fichiers(m, chemin.parent)
    print(f"{chemin} : {'signature valide' if ok else 'signature absente ou invalide'}" + (f" ; fichiers : {'; '.join(ecarts)}" if ecarts else " ; fichiers conformes"))
    return 0 if ok and not ecarts else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
