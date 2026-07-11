# Source des donnees

PyroVeille utilise les routes publiques employees par le site feuxdeforet.fr :

`https://feuxdeforet.fr/api/signalements/recent`

`https://feuxdeforet.fr/fdf/cartographie/geojson?scope=web`

La route `signalements/recent` expose notamment :

- `id`
- `title`
- `commune`
- `dept`
- `url`
- `dateIso`
- `enCours`
- `thumbnail`

La route cartographique expose les points GeoJSON visibles sur la carte FeuxDeForet, avec notamment `statut`, `etat`, `url` et les coordonnees. PyroVeille l'utilise pour recuperer les feux signales en jaune (`signale`, `probable`, `douteux`, `en_attente`) et les expose avec `fire_status: reported`.

Les coordonnees de la route cartographique sont utilisees en priorite. Sinon, le geocodage optionnel place le signalement au niveau de la commune. Cette position est donc approximative. L'adresse configuree par l'utilisateur est aussi geocodee pour calculer le rayon de surveillance.

Pour le suivi des moyens aeriens, PyroVeille utilise le flux public de la carte FeuxDeForet. Depuis `0.4.0-beta.10`, un fallback ADS-B via `api.adsb.lol` complete ce flux pour les Canadair/Pelican, Dash/Milan et helicos Dragon visibles publiquement autour de la zone configuree. Les donnees ADS-B peuvent etre incompletes ou absentes selon la couverture et l'equipement visible.

PyroVeille est une aide de surveillance et ne remplace pas les consignes officielles des autorites.
