# PyroVeille

PyroVeille est une integration Home Assistant custom compatible HACS qui surveille les signalements d'incendies publies par feuxdeforet.fr.

## Pages

- [Installation](Installation)
- [Configuration](Configuration)
- [Entites](Entites)
- [Projections](Projections)
- [Automatisations](Automatisations)
- [Source des donnees](Source-des-donnees)
- [Ameliorations proposees](Ameliorations)
- [FAQ](FAQ)
- [Changelog](Changelog)

## Resume

L'integration recupere les signalements recents, filtre les incendies autour d'une adresse et d'un rayon choisis, cree une notification Home Assistant ou Telegram, expose des marqueurs `device_tracker` GPS pour les afficher sur la carte, genere une projection automatique de trajectoire basee sur la meteo locale, et peut suivre les avions/helicos live publies par FeuxDeForet.

## Apercu

![Capteurs PyroVeille](images/pyroveille-info.png)

![Carte des incendies PyroVeille](images/pyroveille-map-card.png)

![Carte des projections PyroVeille](images/pyroveille-projection-map-card.png)
