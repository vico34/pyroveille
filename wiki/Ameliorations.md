# Ameliorations proposees

Cette page liste les pistes utiles pour faire evoluer PyroVeille.

## Priorite haute

- Ajouter des tests unitaires sur le filtrage par rayon, le geocodage et la creation des entites carte.
- Ajouter une action de service Home Assistant pour forcer un rafraichissement immediat.

## Carte et affichage

- Ajouter une carte Lovelace dediee PyroVeille si le besoin depasse la carte `map` native.
- Ajouter des captures d'ecran de la configuration, des entites et de la carte.

## Notifications

- Ajouter un format de message personnalisable pour Telegram et mobile.
- Ajouter une option pour inclure la miniature dans les notifications.
- Ajouter une protection anti-spam configurable pour ne pas renvoyer trop souvent la meme alerte.

## Donnees et fiabilite

- Ajouter un cache persistant du geocodage pour reduire les appels a Nominatim.
- Exposer plus clairement la source de la position : coordonnees natives ou geocodage par commune.

## HACS et maintenance

- Suivre les retours de la PR HACS et adapter rapidement si les mainteneurs demandent des changements.
