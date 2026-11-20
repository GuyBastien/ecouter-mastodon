"""Publier un message sur Mastodon depuis le terminal, sans rien installer.

  python3 publier_mastodon.py message.txt
  python3 publier_mastodon.py message.txt --image capture.png --alt "Description de l'image"
  python3 publier_mastodon.py "Bonjour Mastodon !"

Options :
  --instance mastodon.social   serveur de votre compte (par défaut mastodon.social)
  --image fichier.png          joindre une image (png, jpg, gif, webp)
  --alt "texte"                description de l'image pour les personnes aveugles
  --oui                        publier sans demander de confirmation

Le jeton d'accès est lu dans la variable MASTODON_TOKEN, sinon le script le demande
(il ne s'affiche pas pendant la saisie et n'est jamais enregistré).
Créer un jeton : Préférences > Développement > Nouvelle application,
avec seulement les droits write:statuses et write:media.

Ensuite, suivez les réponses avec :
  python3 ecouter_mastodon.py <lien du message> 600
"""
import getpass
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

USER_AGENT = "publier_mastodon/1.0"
LIMITE = 500  # caractères par défaut sur mastodon.social


def requete(instance, chemin, jeton, donnees, type_contenu, entetes=None):
    req = urllib.request.Request(
        f"https://{instance}/api/{chemin}",
        data=donnees,
        method="POST",
        headers={
            "Authorization": f"Bearer {jeton}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": type_contenu,
            **(entetes or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", "")
        except ValueError:
            msg = ""
        if e.code == 401:
            msg = "jeton refusé (vérifiez-le, ou ses droits write:statuses / write:media)"
        sys.exit(f"❌ Erreur {e.code} : {msg}")


def envoyer_image(instance, jeton, chemin, alt):
    """Envoie une image et renvoie son identifiant."""
    limite = "----publier" + uuid.uuid4().hex
    type_mime = mimetypes.guess_type(chemin)[0] or "application/octet-stream"
    with open(chemin, "rb") as f:
        contenu = f.read()
    parties = []
    if alt:
        parties.append(
            f'--{limite}\r\nContent-Disposition: form-data; name="description"\r\n\r\n{alt}\r\n'.encode()
        )
    parties.append(
        f'--{limite}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{os.path.basename(chemin)}"\r\nContent-Type: {type_mime}\r\n\r\n'.encode()
        + contenu
        + b"\r\n"
    )
    parties.append(f"--{limite}--\r\n".encode())
    media = requete(instance, "v2/media", jeton, b"".join(parties), f"multipart/form-data; boundary={limite}")
    return media["id"]


def main(args):
    instance, image, alt, oui = "mastodon.social", None, None, False
    reste = []
    i = 0
    while i < len(args):
        if args[i] == "--instance":
            instance, i = args[i + 1], i + 2
        elif args[i] == "--image":
            image, i = args[i + 1], i + 2
        elif args[i] == "--alt":
            alt, i = args[i + 1], i + 2
        elif args[i] == "--oui":
            oui, i = True, i + 1
        else:
            reste.append(args[i])
            i += 1
    if len(reste) != 1:
        sys.exit(__doc__)

    source = reste[0]
    message = open(source, encoding="utf-8").read().strip() if os.path.isfile(source) else source
    if not message:
        sys.exit("❌ Message vide")
    if len(message) > LIMITE:
        print(f"⚠️  {len(message)} caractères : mastodon.social en accepte {LIMITE} (les liens comptent pour 23).")
    if image and not os.path.isfile(image):
        sys.exit(f"❌ Image introuvable : {image}")

    print(f"— Message ({len(message)} caractères) sur {instance} —\n{message}\n")
    if image:
        print(f"🖼️  Image : {image}" + (f" (alt : {alt})" if alt else " (sans description)"))
    if not oui and input("Publier ? [o/N] ").strip().lower() not in ("o", "oui", "y", "yes", "w", "wi"):
        sys.exit("Annulé.")

    jeton = os.environ.get("MASTODON_TOKEN") or getpass.getpass("Jeton Mastodon (invisible) : ").strip()
    if not jeton:
        sys.exit("❌ Aucun jeton")

    champs = {"status": message, "visibility": "public"}
    if image:
        champs["media_ids"] = [envoyer_image(instance, jeton, image, alt)]
    statut = requete(
        instance,
        "v1/statuses",
        jeton,
        json.dumps(champs).encode(),
        "application/json",
        # Évite un double message si la commande est relancée par erreur
        {"Idempotency-Key": uuid.uuid4().hex},
    )
    print(f"✅ Publié : {statut['url']}")
    print(f"   Suivre les réponses : python3 ecouter_mastodon.py {statut['url']} 600")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("\nAnnulé.")
