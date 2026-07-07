# Configuration

PyroVeille se configure depuis l'interface Home Assistant.

## Zone surveillee

- `Adresse du centre`: adresse utilisee comme centre de surveillance.
- `Mode de geocodage de l'adresse`: `Adresse puis commune` autorise un secours approximatif par commune ; `Adresse stricte` utilise uniquement l'API Adresse officielle.
- `Rayon`: rayon en kilometres.

L'adresse est geocodee au moment de l'enregistrement. PyroVeille conserve les coordonnees calculees en interne pour filtrer les signalements dans le rayon choisi.

## Filtres

- `Departements a inclure`: optionnel, valeurs separees par des virgules, par exemple `13, 83, 34`.
- `Limiter aux feux en cours`: ignore les signalements non actifs.

## Notifications et geocodage

- `Creer une notification persistante`: affiche une notification Home Assistant pour chaque nouvel incendie proche.
- `Notifier seulement sous cette distance`: seuil optionnel en kilometres. `0` signifie que toutes les alertes dans le rayon configuré peuvent notifier.
- `Inclure le lien feuxdeforet.fr dans les notifications`: ajoute le lien source dans les messages.
- `Notifier via Telegram`: envoie aussi l'alerte via Telegram si la cible `notify` configuree est disponible.
- `Service ou entite Telegram notify`: service legacy, par exemple `telegram` pour `notify.telegram`, ou entite moderne, par exemple `notify.telegram_bot_chat`.
- `Geocoder les communes sans coordonnees natives`: place approximativement les signalements sur la carte quand la source ne fournit pas de latitude/longitude.
- `Activer les projections automatiques`: cree les points de projection sur la carte et recupere la meteo locale. Desactivez cette option pour garder uniquement les alertes et marqueurs d'incendie.
- `Activer les zones satellite FIRMS`: active la recuperation beta de hotspots satellite NASA FIRMS autour des incendies.
- `NASA FIRMS MAP_KEY`: cle gratuite necessaire pour appeler les services FIRMS.
- `Source satellite FIRMS`: source de donnees satellite, par defaut `VIIRS S-NPP NRT`.
- `Rayon de recherche FIRMS`: rayon autour de chaque incendie utilise pour chercher les hotspots.

## Configuration Telegram

PyroVeille n'installe pas Telegram lui-meme. Il reutilise une cible `notify` deja configuree dans Home Assistant.

1. Configurez d'abord Telegram dans Home Assistant avec votre bot Telegram et votre `chat_id`.
2. Redemarrez Home Assistant si votre configuration Telegram le demande.
3. Ouvrez `Outils de developpement > Services` et testez `notify.send_message`, ou cherchez un ancien service commencant par `notify.`.
4. Reperez la cible Telegram disponible, par exemple `notify.telegram_bot_chat`, `notify.telegram` ou `notify.telegram_maison`.
6. Dans les options PyroVeille, activez `Notifier via Telegram`.
7. Dans `Service ou entite Telegram notify`, saisissez l'entite complete si vous utilisez `notify.send_message` :

```text
notify.telegram_bot_chat
```

ou saisissez seulement la partie apres `notify.` si vous utilisez un service legacy :

```text
telegram
```

ou, pour `notify.telegram_maison` :

```text
telegram_maison
```

Si la cible Telegram n'est pas disponible, PyroVeille ignore l'envoi Telegram, note l'erreur dans les diagnostics et continue les notifications persistantes Home Assistant.

## Projections automatiques

Depuis `0.3.1`, les projections peuvent etre activees ou desactivees dans les options de l'integration. Quand elles sont activees, PyroVeille recupere automatiquement la meteo locale Open-Meteo pour chaque incendie proche, puis cree des points de projection sur la carte si le vent local est disponible. Quand elles sont desactivees, PyroVeille ne recupere pas la meteo locale et ne cree pas de points de projection.

Voir [Projections](Projections) pour le fonctionnement et les limites.

## Zones satellite FIRMS beta

Depuis `0.4.0-beta.1`, PyroVeille peut recuperer des hotspots satellite NASA FIRMS autour des incendies proches. Depuis `0.4.0-beta.2`, PyroVeille cree aussi une entite de zone satellite estimee affichable sur la carte native Home Assistant. Depuis `0.4.0-beta.3`, PyroVeille expose un polygone GeoJSON et une carte custom pour afficher une zone difforme transparente. Cette fonction est desactivee par defaut et demande une `MAP_KEY` FIRMS.

### Generer la cle NASA FIRMS

1. Ouvrez la page officielle NASA FIRMS : [demander une MAP_KEY FIRMS](https://firms.modaps.eosdis.nasa.gov/api/map_key/).
2. Renseignez votre adresse email dans le formulaire `Get MAP_KEY`.
3. Validez la demande.
4. Copiez la cle recue par email.
5. Dans les options PyroVeille, collez cette valeur dans `NASA FIRMS MAP_KEY`.
6. Activez `Activer les zones satellite FIRMS`.
7. Gardez `VIIRS S-NPP NRT` pour un premier test et `25 km` comme rayon de recherche.

La page NASA permet aussi de verifier le nombre de transactions restantes. La limite indiquee par NASA est de 5000 transactions par intervalle de 10 minutes, ce qui est largement suffisant pour un usage Home Assistant normal.

Les hotspots sont exposes comme des entites `device_tracker.pyroveille_hotspot_*`. PyroVeille cree aussi une entite `device_tracker.pyroveille_fire_*_satellite_zone` par incendie quand des hotspots sont disponibles. Cette entite utilise `location_accuracy` comme rayon estime en metres, ce qui permet a la carte native Home Assistant d'afficher un cercle GPS. Le marqueur de l'incendie expose aussi un attribut `satellite_zone` avec le nombre de hotspots, un centre estime, une bbox, un rayon estime, une surface estimee et un `geojson`.

### Carte custom PyroVeille

Pour afficher une seule zone difforme transparente, ajoutez cette ressource Lovelace :

```text
/pyroveille_static/pyroveille-map-card.js
```

Type : `Module JavaScript`.

Exemple de carte :

```yaml
type: custom:pyroveille-map-card
title: Incendies PyroVeille
height: 520px
show_satellite_zones: true
show_hotspots: true
show_projections: true
```

La carte lit automatiquement les entites `device_tracker.pyroveille_*` et dessine les polygones `satellite_zone.geojson` quand ils sont disponibles.

Cette information reste une estimation satellite, pas un perimetre officiel du feu.
