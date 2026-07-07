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
- `Notifier via Telegram`: envoie aussi l'alerte via Telegram si le service `notify` configure est disponible.
- `Service Telegram notify`: nom du service Telegram, par defaut `telegram` pour appeler `notify.telegram`. Si votre service s'appelle `notify.telegram_maison`, saisissez `telegram_maison`.
- `Geocoder les communes sans coordonnees natives`: place approximativement les signalements sur la carte quand la source ne fournit pas de latitude/longitude.

## Configuration Telegram

PyroVeille n'installe pas Telegram lui-meme. Il reutilise un service `notify` deja configure dans Home Assistant.

1. Configurez d'abord Telegram dans Home Assistant avec votre bot Telegram et votre `chat_id`.
2. Redemarrez Home Assistant si votre configuration Telegram le demande.
3. Ouvrez `Outils de developpement > Services`.
4. Cherchez les services commencant par `notify.`.
5. Reperez le service Telegram disponible, par exemple `notify.telegram` ou `notify.telegram_maison`.
6. Dans les options PyroVeille, activez `Notifier via Telegram`.
7. Dans `Service Telegram notify`, saisissez seulement la partie apres `notify.` :

```text
telegram
```

ou, pour `notify.telegram_maison` :

```text
telegram_maison
```

Si le service Telegram n'est pas disponible, PyroVeille ignore l'envoi Telegram et continue les notifications persistantes Home Assistant.

## Projections beta

Les projections ne se configurent pas dans le formulaire principal. Elles se definissent avec les services Home Assistant :

- `pyroveille.set_fire_projection`
- `pyroveille.clear_fire_projection`
- `pyroveille.clear_all_projections`

Voir [Projections](Projections) pour les exemples complets.
