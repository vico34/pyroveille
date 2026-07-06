# Changelog

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
