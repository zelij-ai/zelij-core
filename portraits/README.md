# Portraits

Une photo par personne, dans ce dossier :

| Fichier | Qui | Où elle apparaît |
|---|---|---|
| `fondateur.webp` (ou `.png`, `.jpg`) | Vous | En-tête du bureau, bulle « Vous décidez » de l'aquarium et de la vitrine publique |
| `<identifiant>.webp` (ou `.png`, `.jpg`), par exemple `chef-de-cabinet.webp` | Un agent | Bulles et cartes de l'aquarium, vitrine publique |

Format : image **carrée**, 256 × 256 px suffisent (512 au plus), `webp` de préférence. Le bureau la découpe en rond. Un agent peut aussi garder sa photo dans son dossier (`agents/<identifiant>/portrait.webp`) ; ce dossier-ci est regardé ensuite.

Sans photo : les agents reçoivent un monogramme (leurs initiales), le fondateur la silhouette `fondateur.svg` de ce dossier. Remplacez-la par votre photo, ne la supprimez pas.

Avec Docker, le dossier est monté en lecture seule dans le conteneur (`./portraits:/srv/app/portraits:ro`, voir `docker-compose.yml`) : déposez la photo, rechargez la page, c'est tout.

Les photos ne sont jamais envoyées ailleurs ; la vitrine publique les affiche à qui a le lien.
