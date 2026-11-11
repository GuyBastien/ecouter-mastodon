"""Écouter Mastodon en (presque) temps réel, sans compte et sans rien installer.

Deux modes :
  python3 ecouter_mastodon.py '#haiti' [durée_en_secondes]
      affiche chaque nouveau message qui contient le hashtag

  python3 ecouter_mastodon.py https://mastodon.social/@pmaugustin/117547783607239257 [durée]
      affiche les nouvelles réponses à ce message, et les nouveaux favoris / boosts

Option : --instance mastodon.online  (serveur à interroger pour un hashtag, par défaut mastodon.social)

Le script demande les nouveautés toutes les 15 secondes (API publique de Mastodon).
"""
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

INTERVALLE = 15  # secondes entre deux demandes
USER_AGENT = "ecouter_mastodon/1.0 (script de démonstration)"


def api(instance, chemin, **params):
    """Appelle l'API publique d'une instance Mastodon et renvoie le JSON."""
    url = f"https://{instance}/api/v1/{chemin}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def texte(contenu_html):
    """Transforme le HTML d'un message en texte simple sur une ligne."""
    t = re.sub(r"<br\s*/?>|</p>", " ", contenu_html)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return re.sub(r"\s+", " ", t).strip()


def auteur(statut, instance):
    acct = statut["account"]["acct"]
    return "@" + (acct if "@" in acct else f"{acct}@{instance}")


def afficher(statut, instance, icone="💬"):
    heure = statut["created_at"][11:16]
    print(f"{icone} [{heure}] {statut['account']['display_name'] or statut['account']['username']} "
          f"({auteur(statut, instance)}) : {texte(statut['content'])[:200]}")


def ecouter_hashtag(tag, duree, instance):
    tag = tag.lstrip("#").lower()
    print(f"🔎 Écoute de #{tag} sur {instance} pendant {duree} s (nouvelle demande toutes les {INTERVALLE} s)")
    derniers = api(instance, f"timelines/tag/{urllib.parse.quote(tag)}", limit=3)
    print("— 3 derniers messages déjà publiés —")
    for s in reversed(derniers):
        afficher(s, instance, "🕘")
    print("— nouveaux messages —")
    depuis = derniers[0]["id"] if derniers else None
    nouveaux = 0
    fin = time.time() + duree
    while time.time() < fin:
        time.sleep(min(INTERVALLE, max(0, fin - time.time())))
        try:
            params = {"limit": 40}
            if depuis:
                params["since_id"] = depuis
            lot = api(instance, f"timelines/tag/{urllib.parse.quote(tag)}", **params)
        except Exception as e:
            print(f"⚠️ Erreur réseau ({type(e).__name__}), on réessaie…")
            continue
        for s in reversed(lot):
            afficher(s, instance)
            nouveaux += 1
        if lot:
            depuis = lot[0]["id"]
    print(f"Résumé : {nouveaux} nouveau(x) message(s) avec #{tag}")


def ecouter_post(url, duree):
    m = re.match(r"https?://([^/]+)/@[^/]+/(\d+)", url)
    if not m:
        sys.exit("❌ Lien de message invalide. Exemple : https://mastodon.social/@pmaugustin/117547783607239257")
    instance, sid = m.groups()
    post = api(instance, f"statuses/{sid}")
    print(f"📌 Message suivi pendant {duree} s :")
    afficher(post, instance, "📝")
    compte = {"fav": post["favourites_count"], "boost": post["reblogs_count"]}
    print(f"   ⭐ {compte['fav']}  🔁 {compte['boost']}  💬 {post['replies_count']}")
    vus = {s["id"] for s in api(instance, f"statuses/{sid}/context")["descendants"]}
    print(f"— {len(vus)} réponse(s) déjà là ; on attend les nouvelles —")
    nouveaux = 0
    fin = time.time() + duree
    while time.time() < fin:
        time.sleep(min(INTERVALLE, max(0, fin - time.time())))
        try:
            reponses = api(instance, f"statuses/{sid}/context")["descendants"]
            post = api(instance, f"statuses/{sid}")
        except Exception as e:
            print(f"⚠️ Erreur réseau ({type(e).__name__}), on réessaie…")
            continue
        for s in reponses:
            if s["id"] not in vus:
                vus.add(s["id"])
                afficher(s, instance, "↩️")
                nouveaux += 1
        for cle, champ, icone, mot in (("fav", "favourites_count", "⭐", "favori"),
                                       ("boost", "reblogs_count", "🔁", "boost")):
            if post[champ] != compte[cle]:
                print(f"{icone} {mot} : {compte[cle]} → {post[champ]}")
                compte[cle] = post[champ]
    print(f"Résumé : {nouveaux} nouvelle(s) réponse(s), ⭐ {compte['fav']}, 🔁 {compte['boost']}")


def main():
    args = sys.argv[1:]
    instance = "mastodon.social"
    if "--instance" in args:
        i = args.index("--instance")
        instance = args[i + 1]
        del args[i:i + 2]
    if not args:
        sys.exit(__doc__)
    cible = args[0]
    duree = int(args[1]) if len(args) > 1 else 120
    try:
        if cible.startswith("http"):
            ecouter_post(cible, duree)
        else:
            ecouter_hashtag(cible, duree, instance)
    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    except urllib.error.HTTPError as e:
        print(f"❌ Mastodon a répondu {e.code} : vérifiez le hashtag ou le lien.")


if __name__ == "__main__":
    main()
