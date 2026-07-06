# Entites

PyroVeille cree les entites suivantes.

## Capteurs

- `binary_sensor.alerte_incendie_proche`: actif si au moins un incendie est dans la zone.
- `sensor.incendies_proches`: nombre d'incendies dans le perimetre.
- `sensor.distance_incendie_le_plus_proche`: distance du signalement le plus proche.

## Carte

Des entites `device_tracker` GPS sont creees pour les incendies proches disposant de coordonnees. Elles exposent `latitude`, `longitude` et `source_type = gps`, ce qui les rend visibles dans la carte native Home Assistant.

Si la source ne fournit pas de coordonnees, PyroVeille peut geocoder la commune pour obtenir une position approximative.

## Exemple de carte Lovelace

Apres une premiere detection, Home Assistant cree une entite `device_tracker` par incendie proche. Ajoutez ces entites dans une carte `map` :

```yaml
type: map
title: Incendies proches
default_zoom: 9
hours_to_show: 24
entities:
  - entity: device_tracker.nom_de_l_incendie_pyroveille
```

Les noms exacts sont visibles dans `Parametres > Appareils et services > Entites`, en filtrant sur `PyroVeille`. Remplacez l'exemple par une ou plusieurs entites `device_tracker` generees par l'integration.
