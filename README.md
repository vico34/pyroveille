# PyroVeille

Integration Home Assistant custom compatible HACS pour surveiller les signalements d'incendies publies par [feuxdeforet.fr](https://feuxdeforet.fr/).

## Fonctionnalites

- Recuperation des signalements recents via la route publique `https://feuxdeforet.fr/api/signalements/recent`.
- Selection d'une zone par latitude, longitude et rayon en kilometres.
- Filtre optionnel par departements.
- Filtre optionnel sur les feux en cours uniquement.
- Notification persistante Home Assistant lorsqu'un nouvel incendie entre dans le perimetre.
- Evenement Home Assistant `pyroveille_nearby_fire` pour declencher vos propres automatisations.
- Entites `device_tracker` GPS pour afficher les incendies proches sur la carte Home Assistant.
- Geocodage optionnel des communes lorsque la route publique ne fournit pas de coordonnees.

## Installation HACS

1. Dans HACS, ajoutez ce depot comme depot personnalise.
2. Categorie: `Integration`.
3. Installez `PyroVeille`.
4. Redemarrez Home Assistant.
5. Ajoutez l'integration depuis `Parametres > Appareils et services`.

## Configuration

Champs principaux :

- `Latitude du centre` et `Longitude du centre`: centre de la zone surveillee.
- `Rayon`: perimetre de surveillance en kilometres.
- `Departements a inclure`: optionnel, separes par virgules, exemple `13, 83, 34`.
- `Limiter aux feux en cours`: ignore les signalements qui ne sont plus actifs.
- `Creer une notification persistante`: cree une notification Home Assistant sur nouvel incendie proche.
- `Geocoder les communes sans coordonnees natives`: utilise Nominatim/OpenStreetMap pour placer les signalements sur la carte quand feuxdeforet.fr ne fournit pas de latitude/longitude.

## Entites creees

- `binary_sensor.alerte_incendie_proche`: actif si au moins un incendie est dans le perimetre.
- `sensor.incendies_proches`: nombre d'incendies dans le perimetre.
- `sensor.distance_incendie_le_plus_proche`: distance en km du signalement le plus proche.
- `device_tracker.*`: un marqueur par incendie proche, visible sur la carte Home Assistant.

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

Lorsque les coordonnees ne sont pas publiees dans cette route, le placement carte est approximatif et base sur la commune. Les notifications doivent donc etre considerees comme une aide de surveillance, pas comme une source officielle d'alerte securite.
