# Changelog

## 0.4.0-beta.3

- Ajout d'un polygone `satellite_zone.geojson` pour representer une zone satellite estimee difforme.
- Ajout de `area_km2` sur les zones satellite estimees.
- Ajout de la carte custom `pyroveille-map-card` basee sur OpenStreetMap/Leaflet.

## 0.4.0-beta.2

- Ajout des entites `device_tracker.pyroveille_fire_*_satellite_zone`.
- Affichage possible de la zone satellite estimee comme cercle GPS via `location_accuracy`.
- Ajout de la liste `satellite_zone_entities` dans les attributs de diagnostic de mise a jour.

## 0.4.0-beta.1

- Ajout beta des zones satellite estimees via NASA FIRMS.
- Ajout des options `Activer les zones satellite FIRMS`, `NASA FIRMS MAP_KEY`, `Source satellite FIRMS` et `Rayon de recherche FIRMS`.
- Ajout des entites `device_tracker.pyroveille_hotspot_*` pour afficher les hotspots satellite sur la carte.
- Ajout de l'attribut `satellite_zone` sur les marqueurs d'incendie.

## 0.3.2

- Correction de l'envoi Telegram avec les entites `notify.*` modernes via `notify.send_message`.
- Conservation de la compatibilite avec les anciens services `notify.telegram`.
- Ajout de diagnostics Telegram pour afficher la cible configuree et la derniere erreur.

## 0.3.1

- Ajout de l'option `Activer les projections automatiques`.
- Remplacement du pictogramme fleche des marqueurs de projection par un libelle temporel comme `+1h`.
- Ajout de l'attribut `projection_label` sur les entites de projection.

## 0.3.0

- Passage en stable des projections automatiques basees sur la meteo locale.
- Ajout des captures d'ecran dans le README et le wiki.
- Conservation d'un fonctionnement sans parametre manuel pour les projections.

## 0.3.0-beta.2

- Remplacement des projections manuelles par des projections automatiques sans saisie utilisateur.
- Recuperation automatique de la meteo locale via Open-Meteo pour chaque incendie proche.
- Utilisation du vent local pour determiner la direction sous le vent et une vitesse de progression estimee.
- Suppression des services manuels de projection de la beta.

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
