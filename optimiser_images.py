"""
Optimise les images du site RCE pour la mise en ligne.

- Convertit les photos en WebP, redimensionnées et compressées
  (et corrige l'orientation des photos prises au téléphone).
- Renomme les fichiers proprement : minuscules, sans accents, sans espaces.
- Range le résultat dans le dossier img/ (les originaux ne sont pas modifiés).
- Met à jour les chemins des images dans toutes les pages .html
  (une copie des pages d'origine est gardée dans sauvegarde-html/).

Utilisation, depuis le dossier du projet :
    pip install pillow
    python optimiser_images.py
"""

import re
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageOps

RACINE = Path(__file__).resolve().parent
SORTIE = RACINE / "img"
SAUVEGARDE = RACINE / "sauvegarde-html"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Dossier source (comparé sans accents ni majuscules) -> dossier de sortie, largeur max en pixels
DOSSIERS = {
    "photo_projet_termine": ("photos", 1600),
    "photo-projet-termine": ("photos", 1600),
    "photos": ("photos", 1600),
    "coloris": ("coloris", 800),
    "motif-decor": ("motifs", 800),
    "motif_decor": ("motifs", 800),
    "logo": ("logo", 600),
}
QUALITE = 80


def sans_accents(texte):
    texte = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in texte if not unicodedata.combining(c))


def nom_propre(texte):
    """'Projet_2_après (3)' -> 'projet-2-apres-3'"""
    texte = sans_accents(texte).lower()
    texte = re.sub(r"[^a-z0-9]+", "-", texte)
    return texte.strip("-") or "image"


def cle(chemin):
    """Clé de comparaison tolérante : sans accents, minuscules, espaces normalisés."""
    chemin = unquote(chemin).replace("\\", "/").strip().lstrip("./")
    return nom_propre_chemin(chemin)


def nom_propre_chemin(chemin):
    # L'extension est ignorée : un .jpg cité dans la page retrouve aussi un .png sur le disque
    morceaux = chemin.split("/")
    *dossiers, fichier = morceaux
    base = fichier.rpartition(".")[0] or fichier
    return "/".join([nom_propre(d) for d in dossiers] + [nom_propre(base)])


def convertir(source, destination, largeur_max):
    with Image.open(source) as im:
        im = ImageOps.exif_transpose(im)  # remet droites les photos de téléphone
        if im.width > largeur_max:
            hauteur = round(im.height * largeur_max / im.width)
            im = im.resize((largeur_max, hauteur), Image.LANCZOS)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        im.save(destination, "WEBP", quality=QUALITE, method=6)


def main():
    correspondances = {}  # clé de l'ancien chemin -> nouveau chemin
    taille_avant = taille_apres = 0
    utilises = set()

    for dossier in sorted(p for p in RACINE.iterdir() if p.is_dir()):
        reglage = DOSSIERS.get(nom_propre(dossier.name).replace("-", "_")) or DOSSIERS.get(nom_propre(dossier.name))
        if not reglage:
            continue
        sous_dossier, largeur = reglage
        (SORTIE / sous_dossier).mkdir(parents=True, exist_ok=True)

        for image in sorted(dossier.iterdir()):
            if image.suffix.lower() not in EXTENSIONS:
                continue
            base = nom_propre(image.stem)
            nouveau = f"img/{sous_dossier}/{base}.webp"
            n = 2
            while nouveau in utilises:  # deux fichiers qui donneraient le même nom
                nouveau = f"img/{sous_dossier}/{base}-{n}.webp"
                n += 1
            utilises.add(nouveau)

            try:
                convertir(image, RACINE / nouveau, largeur)
            except Exception as erreur:
                print(f"  ! Impossible de convertir {image.name} : {erreur}")
                continue

            taille_avant += image.stat().st_size
            taille_apres += (RACINE / nouveau).stat().st_size
            correspondances[cle(f"{dossier.name}/{image.name}")] = nouveau
            print(f"  {dossier.name}/{image.name}  ->  {nouveau}")

    if not correspondances:
        print("Aucune image trouvée. Lance le script depuis le dossier du projet.")
        return

    print(f"\nPoids des images : {taille_avant / 1e6:.1f} Mo -> {taille_apres / 1e6:.1f} Mo")

    # Mise à jour des pages HTML
    SAUVEGARDE.mkdir(exist_ok=True)
    motif = re.compile(r'((?:src|href)=")([^"#?]+\.(?:jpe?g|png|webp))(")', re.IGNORECASE)
    introuvables = set()

    for page in sorted(RACINE.glob("*.html")):
        texte = page.read_text(encoding="utf-8")

        def remplacer(m):
            chemin = m.group(2)
            if chemin.startswith(("http://", "https://", "/_")):
                return m.group(0)
            nouveau = correspondances.get(cle(chemin))
            if nouveau is None:
                introuvables.add(f"{page.name} : {chemin}")
                return m.group(0)
            return m.group(1) + nouveau + m.group(3)

        nouveau_texte = motif.sub(remplacer, texte)
        if nouveau_texte != texte:
            shutil.copy2(page, SAUVEGARDE / page.name)
            page.write_text(nouveau_texte, encoding="utf-8")
            print(f"Page mise à jour : {page.name}")

    if introuvables:
        print("\nImages citées dans les pages mais introuvables sur le disque :")
        for ligne in sorted(introuvables):
            print("  - " + ligne)
    else:
        print("\nToutes les images des pages ont été trouvées et mises à jour.")


if __name__ == "__main__":
    main()
