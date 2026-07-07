# FAQ

## J'ai `address_not_found`

Essayez une adresse francaise plus precise, par exemple :

```text
10 rue de la Paix, 75002 Paris
```

Si l'adresse reste introuvable, passez le mode de geocodage sur `Adresse puis commune`. PyroVeille essaie alors l'API Adresse officielle puis un secours plus tolerant.

## Je ne vois aucun `device_tracker`

Les entites `device_tracker` sont creees seulement apres une detection dans le rayon configure et uniquement si le signalement a des coordonnees. Activez le geocodage des communes sans coordonnees natives si vous voulez un placement approximatif.

## La carte automatique ne montre rien

La carte automatique demande la carte custom `auto-entities` installee via HACS. Les nouvelles entites PyroVeille commencent par :

```text
device_tracker.pyroveille_
```

Si vous avez installe une ancienne version, supprimez puis recreez l'integration pour obtenir les nouveaux identifiants suggeres.

## Telegram ne recoit rien

Verifiez d'abord que Telegram fonctionne depuis `Outils de developpement > Services`.

Pour une configuration recente avec entite `notify.*`, testez :

```yaml
service: notify.send_message
data:
  entity_id: notify.telegram_bot_chat
  message: Test PyroVeille
```

Dans PyroVeille, saisissez alors l'entite complete, par exemple `notify.telegram_bot_chat`.

Pour une configuration legacy avec service `notify.telegram`, saisissez seulement le suffixe du service :

```text
telegram
```

Les diagnostics PyroVeille indiquent aussi `telegram_notifications.last_error` si la cible configuree n'est pas disponible.

## Les positions sur la carte sont-elles exactes ?

Les coordonnees natives de feuxdeforet.fr sont utilisees quand elles existent. Sinon, le geocodage par commune reste approximatif et doit etre considere comme une aide de surveillance.
