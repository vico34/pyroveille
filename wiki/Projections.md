# Projections beta

La projection de trajectoire est disponible a partir de `0.3.0-beta.1`.

Important : PyroVeille ne calcule pas une prevision officielle de propagation. La source `feuxdeforet.fr` ne fournit pas de front de feu ni de trajectoire temporelle exploitable. La projection est donc une information utilisateur : vous saisissez la direction et la vitesse estimees, puis PyroVeille affiche des points de progression sur la carte.

## Definir une projection

Dans Home Assistant, ouvrez `Outils de developpement > Services`, puis appelez :

```yaml
service: pyroveille.set_fire_projection
data:
  fire_id: "12345"
  bearing: 90
  speed_kmh: 1.2
  horizon_hours: 4
  uncertainty_km: 1
```

Champs :

- `fire_id`: identifiant de l'incendie, visible dans les attributs du `device_tracker` PyroVeille.
- `bearing`: direction en degres. `0` nord, `90` est, `180` sud, `270` ouest.
- `speed_kmh`: vitesse estimee en kilometres par heure.
- `horizon_hours`: nombre d'heures a projeter.
- `uncertainty_km`: incertitude approximative en kilometres.

PyroVeille cree jusqu'a 4 entites carte :

```text
device_tracker.pyroveille_fire_<id>_projection_25
device_tracker.pyroveille_fire_<id>_projection_50
device_tracker.pyroveille_fire_<id>_projection_75
device_tracker.pyroveille_fire_<id>_projection_100
```

La carte automatique `auto-entities` documentee dans la page [Entites](Entites) les affiche automatiquement car elles commencent par `device_tracker.pyroveille_`.

## Effacer une projection

```yaml
service: pyroveille.clear_fire_projection
data:
  fire_id: "12345"
```

Pour tout effacer :

```yaml
service: pyroveille.clear_all_projections
```

## Limites

- La projection est purement geometrique : point de depart, direction, vitesse, horizon.
- Elle ne tient pas compte du vent, du relief, de la vegetation, des actions des secours ou de l'evolution reelle du feu.
- Elle doit etre utilisee comme aide visuelle personnelle, pas comme source officielle d'alerte ou de decision de securite.
