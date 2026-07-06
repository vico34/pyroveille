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
- `Notifier via Telegram`: envoie aussi l'alerte via Telegram si le service `notify` configure est disponible.
- `Service Telegram notify`: nom du service Telegram, par defaut `telegram` pour appeler `notify.telegram`. Si votre service s'appelle `notify.telegram_maison`, saisissez `telegram_maison`.
- `Geocoder les communes sans coordonnees natives`: place approximativement les signalements sur la carte quand la source ne fournit pas de latitude/longitude.
