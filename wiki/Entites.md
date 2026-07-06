# Entites

PyroVeille cree les entites suivantes.

## Capteurs

- `binary_sensor.alerte_incendie_proche`: actif si au moins un incendie est dans la zone.
- `sensor.incendies_proches`: nombre d'incendies dans le perimetre.
- `sensor.distance_incendie_le_plus_proche`: distance du signalement le plus proche.

## Carte

Des entites `device_tracker` GPS sont creees pour les incendies proches disposant de coordonnees. Elles exposent `latitude`, `longitude` et `source_type = gps`, ce qui les rend visibles dans la carte native Home Assistant.

Si la source ne fournit pas de coordonnees, PyroVeille peut geocoder la commune pour obtenir une position approximative.
