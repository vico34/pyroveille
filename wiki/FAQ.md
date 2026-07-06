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

Verifiez que Home Assistant expose bien un service `notify.telegram` ou equivalent dans `Outils de developpement > Services`.

Dans PyroVeille, saisissez seulement le suffixe du service :

```text
telegram
```

pour `notify.telegram`.

## Les positions sur la carte sont-elles exactes ?

Les coordonnees natives de feuxdeforet.fr sont utilisees quand elles existent. Sinon, le geocodage par commune reste approximatif et doit etre considere comme une aide de surveillance.
