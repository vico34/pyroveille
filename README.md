# PyroVeille

Integration Home Assistant custom compatible HACS pour surveiller les signalements d'incendies publies par [feuxdeforet.fr](https://feuxdeforet.fr/).

## Fonctionnalites

- Recuperation des signalements recents via la route publique `https://feuxdeforet.fr/api/signalements/recent`.
- Selection d'une zone par adresse et rayon en kilometres.
- Filtre optionnel par departements.
- Filtre optionnel sur les feux en cours uniquement.
- Notification persistante Home Assistant lorsqu'un nouvel incendie entre dans le perimetre.
- Notification Telegram optionnelle via un service `notify.telegram` existant dans Home Assistant.
- Evenement Home Assistant `pyroveille_nearby_fire` pour declencher vos propres automatisations.
- Entites `device_tracker` GPS pour afficher les incendies proches sur la carte Home Assistant.
- Projection beta de trajectoire utilisateur avec vitesse, direction et points visuels sur la carte.
- Geocodage optionnel des communes lorsque la route publique ne fournit pas de coordonnees.

## Installation HACS

1. Dans HACS, ajoutez ce depot comme depot personnalise : `https://github.com/vico34/pyroveille`.
2. Categorie: `Integration`.
3. Installez `PyroVeille`.
4. Redemarrez Home Assistant.
5. Ajoutez l'integration depuis `Parametres > Appareils et services`.

## Configuration

Champs principaux :

- `Adresse du centre`: adresse utilisee comme centre de la zone surveillee.
- `Rayon`: perimetre de surveillance en kilometres.
- `Departements a inclure`: optionnel, separes par virgules, exemple `13, 83, 34`.
- `Limiter aux feux en cours`: ignore les signalements qui ne sont plus actifs.
- `Creer une notification persistante`: cree une notification Home Assistant sur nouvel incendie proche.
- `Notifier seulement sous cette distance`: seuil optionnel en kilometres. `0` desactive le seuil.
- `Inclure le lien feuxdeforet.fr`: ajoute ou retire le lien source dans les notifications.
- `Notifier via Telegram`: envoie aussi l'alerte via Telegram si le service `notify` configure est disponible.
- `Service Telegram notify`: nom du service Telegram, par defaut `telegram` pour appeler `notify.telegram`.
- `Mode de geocodage`: `Adresse puis commune` utilise l'API Adresse officielle puis Nominatim en secours. `Adresse stricte` limite le geocodage a l'API Adresse officielle.
- `Geocoder les communes sans coordonnees natives`: utilise Nominatim/OpenStreetMap pour placer les signalements sur la carte quand feuxdeforet.fr ne fournit pas de latitude/longitude.

## Entites creees

- `binary_sensor.alerte_incendie_proche`: actif si au moins un incendie est dans le perimetre.
- `sensor.incendies_proches`: nombre d'incendies dans le perimetre.
- `sensor.distance_incendie_le_plus_proche`: distance en km du signalement le plus proche.
- `sensor.derniere_mise_a_jour_pyroveille`: date de la derniere recuperation reussie.
- `device_tracker.*`: un marqueur GPS par incendie proche, visible sur la carte Home Assistant.
- `device_tracker.pyroveille_fire_*_projection_*`: marqueurs beta de projection de trajectoire, si une projection est definie.

## Exemple de carte

Apres une premiere alerte, ajoutez les entites `device_tracker` creees par PyroVeille dans une carte Home Assistant. La carte native `map` utilise OpenStreetMap :

```yaml
type: map
title: Incendies PyroVeille
default_zoom: 9
hours_to_show: 24
entities:
  - entity: device_tracker.nom_de_l_incendie_pyroveille
```

Les noms exacts des entites sont visibles dans `Parametres > Appareils et services > Entites`, en filtrant sur `PyroVeille`. Les marqueurs PyroVeille sont rouges pour les feux actifs et gris pour les feux inactifs.

Pour afficher automatiquement toutes les entites `device_tracker.pyroveille_*`, installez la carte custom `auto-entities` via HACS :

```yaml
type: custom:auto-entities
card:
  type: map
  title: Incendies PyroVeille
  default_zoom: 9
  hours_to_show: 24
filter:
  include:
    - entity_id: device_tracker.pyroveille_*
  exclude:
    - attributes:
        fire_status: inactive
show_empty: false
```

## Projection beta de trajectoire

La version `0.3.0-beta.1` permet de definir manuellement une trajectoire estimee pour un incendie. PyroVeille ne predit pas le feu depuis la source : la direction et la vitesse sont saisies par l'utilisateur, puis l'integration affiche 4 points de progression sur la carte native Home Assistant.

Exemple depuis `Outils de developpement > Services` :

```yaml
service: pyroveille.set_fire_projection
data:
  fire_id: "12345"
  bearing: 90
  speed_kmh: 1.2
  horizon_hours: 4
  uncertainty_km: 1
```

- `bearing`: direction en degres, `0` nord, `90` est, `180` sud, `270` ouest.
- `speed_kmh`: vitesse estimee en km/h.
- `horizon_hours`: horizon affiche sur la carte.
- `uncertainty_km`: incertitude approximative, exposee comme precision GPS du marqueur.

Pour supprimer une projection :

```yaml
service: pyroveille.clear_fire_projection
data:
  fire_id: "12345"
```

## Automatisation mobile

L'integration cree deja une notification persistante si l'option est active. Pour envoyer aussi une notification mobile, utilisez l'evenement :

```yaml
alias: Alerte incendie proche
mode: queued
trigger:
  - platform: event
    event_type: pyroveille_nearby_fire
action:
  - service: notify.mobile_app_votre_telephone
    data:
      title: "Alerte incendie proche"
      message: >
        {{ trigger.event.data.title }} a {{ trigger.event.data.distance_km | round(1) }} km.
      data:
        url: "{{ trigger.event.data.url }}"
```

## Notes sur la source

Feux de Foret expose sur son site public une carte "Feux en cours" et une route JSON publique utilisee par le frontend. Au 6 juillet 2026, la route `https://feuxdeforet.fr/api/signalements/recent` renvoie notamment `id`, `title`, `commune`, `dept`, `url`, `dateIso`, `enCours` et `thumbnail`. Si des coordonnees sont ajoutees par la source, l'integration les utilisera directement.

L'adresse de surveillance et les communes sans coordonnees natives sont geocodees via Nominatim/OpenStreetMap. Lorsque les coordonnees ne sont pas publiees dans cette route, le placement carte est approximatif et base sur la commune. Les notifications doivent donc etre considerees comme une aide de surveillance, pas comme une source officielle d'alerte securite.
