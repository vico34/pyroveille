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
