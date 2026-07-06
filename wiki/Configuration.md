# Configuration

PyroVeille se configure depuis l'interface Home Assistant.

## Zone surveillee

- `Adresse du centre`: adresse utilisee comme centre de surveillance.
- `Rayon`: rayon en kilometres.

L'adresse est geocodee au moment de l'enregistrement. PyroVeille conserve les coordonnees calculees en interne pour filtrer les signalements dans le rayon choisi.

## Filtres

- `Departements a inclure`: optionnel, valeurs separees par des virgules, par exemple `13, 83, 34`.
- `Limiter aux feux en cours`: ignore les signalements non actifs.

## Notifications et geocodage

- `Creer une notification persistante`: affiche une notification Home Assistant pour chaque nouvel incendie proche.
- `Geocoder les communes sans coordonnees natives`: place approximativement les signalements sur la carte quand la source ne fournit pas de latitude/longitude.
