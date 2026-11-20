# écouter-mastodon

Un petit script Python qui **suit Mastodon presque en temps réel** depuis le terminal : les nouveaux messages d'un hashtag, ou les nouvelles réponses, favoris et boosts d'un message.

- Aucun compte Mastodon nécessaire
- Rien à installer : seulement Python 3 (bibliothèque standard)
- Utilise l'API publique officielle de Mastodon

## Utilisation

```sh
# Suivre un hashtag pendant 120 secondes
python3 ecouter_mastodon.py '#haiti' 120

# Suivre un message (réponses, favoris, boosts) pendant 5 minutes
python3 ecouter_mastodon.py https://mastodon.social/@pmaugustin/117547783607239257 300

# Suivre un hashtag sur une autre instance
python3 ecouter_mastodon.py '#tryton' 120 --instance mastodon.online
```

> Mettez le hashtag entre guillemets (`'#haiti'`), sinon le terminal prend `#` pour un commentaire.

La durée est en secondes (120 par défaut). `Ctrl+C` arrête le script.

## Exemple

```
🔎 Écoute de #news sur mastodon.social pendant 50 s (nouvelle demande toutes les 15 s)
— 3 derniers messages déjà publiés —
🕘 [03:06] Citelink (@citelink@mastodon.social) : Delegates gather in Turkey for Cop31…
— nouveaux messages —
💬 [03:09] Hermes-vector.buzz (@hermes_vector@mastodon.social) : Nvidia board hires former prosecutor…
💬 [02:34] Українська правда (@ukrpravda@rss.anyfeed.cc) : У частині Латвії…
Résumé : 2 nouveau(x) message(s) avec #news
```

```
📌 Message suivi pendant 20 s :
📝 [16:27] Pierre Michel Augustin (@pmaugustin@mastodon.social) : @tryton @cedrickrier Mwen kreye yon kont sou #Weblate…
   ⭐ 1  🔁 0  💬 2
— 5 réponse(s) déjà là ; on attend les nouvelles —
Résumé : 0 nouvelle(s) réponse(s), ⭐ 1, 🔁 0
```

Quand quelque chose change, le script l'affiche, par exemple `↩️` pour une nouvelle réponse ou `⭐ favori : 1 → 2`.

## Comment ça marche

Toutes les 15 secondes, le script interroge l'API publique de Mastodon :

| Mode | Appel API |
|---|---|
| Hashtag | `GET /api/v1/timelines/tag/<hashtag>?since_id=<dernier>` |
| Message | `GET /api/v1/statuses/<id>` et `GET /api/v1/statuses/<id>/context` |

Il ne garde que ce qui est nouveau depuis la dernière demande, puis l'affiche.

## Mastodon, un système réparti

Mastodon n'est pas un seul site : ce sont des milliers de serveurs (instances) qui échangent les messages avec le protocole **ActivityPub**. C'est ce qu'on appelle le **Fediverse**.

On le voit dans l'exemple ci-dessus : le message de `@ukrpravda@rss.anyfeed.cc` a été écrit à **02:34** mais n'est arrivé sur mastodon.social qu'à **03:09**. Chaque serveur reçoit les messages des autres avec un certain délai : c'est la *cohérence à terme* (eventual consistency) d'un système réparti.

## À faire

- Mode temps réel avec l'API de streaming (nécessite un jeton de compte)
- Enregistrer les messages dans un fichier (CSV / JSON)

## Licence

GPL-3.0 — voir [LICENSE](LICENSE).

## Auteur

Bastien — [@Guy_Bastien@mastodon.social](https://mastodon.social/@Guy_Bastien) · [GitHub](https://github.com/GuyBastien) · [Portfolio](https://guivenschery.me)

## Publier un message

`publier_mastodon.py` publie un message (et une image si on veut) sur votre compte :

```sh
python3 publier_mastodon.py message.txt
python3 publier_mastodon.py message.txt --image capture.png --alt "Description de l'image"
```

Il faut un jeton d'accès : sur Mastodon, **Préférences > Développement > Nouvelle application**, cochez seulement `write:statuses` et `write:media`, puis copiez « Votre jeton d'accès ». Le script le demande au moment de publier (il ne s'affiche pas et n'est pas enregistré). Ne mettez jamais ce jeton dans un fichier du dépôt.

Le script affiche le lien du message publié. On peut ensuite suivre les réponses :

```sh
python3 ecouter_mastodon.py https://mastodon.social/@moi/123456789 600
```
