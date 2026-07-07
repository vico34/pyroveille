# Projections beta automatiques

La projection de trajectoire automatique est disponible a partir de `0.3.0-beta.2`.

Important : PyroVeille ne calcule pas une prevision officielle de propagation. La source `feuxdeforet.fr` ne fournit pas de front de feu ni de trajectoire temporelle exploitable. La projection est donc une aide visuelle automatique basee sur la meteo locale, principalement le vent.

## Fonctionnement

Pour chaque incendie proche avec coordonnees, PyroVeille interroge automatiquement Open-Meteo autour du point de l'incendie et recupere :

- vitesse du vent a 10 m ;
- direction du vent a 10 m ;
- rafales a 10 m.

La trajectoire utilise la direction sous le vent, soit la direction du vent retournee par la meteo + 180 degres. La vitesse de progression est estimee avec une heuristique interne a partir de la vitesse du vent. Aucun parametre manuel n'est demande.

PyroVeille cree jusqu'a 4 entites carte :

```text
device_tracker.pyroveille_fire_<id>_projection_25
device_tracker.pyroveille_fire_<id>_projection_50
device_tracker.pyroveille_fire_<id>_projection_75
device_tracker.pyroveille_fire_<id>_projection_100
```

La carte automatique `auto-entities` documentee dans la page [Entites](Entites) les affiche automatiquement car elles commencent par `device_tracker.pyroveille_`.

## Limites

- La projection est une heuristique geometrique : point de depart, vent local, vitesse estimee, horizon.
- Elle ne tient pas compte du relief, de la vegetation, des actions des secours ou de l'evolution reelle du feu.
- Le vent meteo est une donnee modele, pas une observation terrain garantie.
- Elle doit etre utilisee comme aide visuelle personnelle, pas comme source officielle d'alerte ou de decision de securite.
