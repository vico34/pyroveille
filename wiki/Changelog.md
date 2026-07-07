# Changelog

## 0.3.0-beta.1

- Ajout beta des projections utilisateur de trajectoire incendie.
- Ajout des services `pyroveille.set_fire_projection`, `pyroveille.clear_fire_projection` et `pyroveille.clear_all_projections`.
- Ajout de marqueurs carte `device_tracker.pyroveille_fire_*_projection_*` pour visualiser la progression estimee.
- Persistance des projections dans le stockage Home Assistant.
- Documentation de la limite importante : projection utilisateur, pas prevision officielle.

## 0.2.4

- Ajout d'identifiants suggeres `device_tracker.pyroveille_*` pour les entites carte.
- Ajout d'un exemple de carte automatique avec `auto-entities`.
- Ajout des marqueurs couleur par statut du feu.
- Ajout du capteur `Derniere mise a jour PyroVeille`.
- Ajout de diagnostics enrichis : derniere erreur, centre configure, rayon et alertes proches.
- Ajout d'un seuil optionnel de distance pour les notifications.
- Ajout d'une option pour inclure ou retirer le lien feuxdeforet.fr dans les notifications.
- Ajout du mode de geocodage `Adresse stricte` ou `Adresse puis commune`.

## 0.2.3

- Ajout du geocodage via l'API Adresse officielle francaise.
- Ajout d'un secours Nominatim plus tolerant.
- Message `address_not_found` plus explicite.

## 0.2.2

- Mise a jour du logo et de l'icone.
- Ajout des notifications Telegram via un service `notify` existant.
- Ajout de la documentation Telegram et carte.

## 0.2.1

- Configuration par adresse au lieu de latitude/longitude.
- Geocodage automatique de l'adresse de surveillance.
