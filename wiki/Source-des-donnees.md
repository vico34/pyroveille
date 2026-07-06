# Source des donnees

PyroVeille utilise la route publique employee par le site feuxdeforet.fr :

`https://feuxdeforet.fr/api/signalements/recent`

Au 6 juillet 2026, cette route expose notamment :

- `id`
- `title`
- `commune`
- `dept`
- `url`
- `dateIso`
- `enCours`
- `thumbnail`

Les coordonnees sont utilisees directement si elles sont presentes. Sinon, le geocodage optionnel place le signalement au niveau de la commune. Cette position est donc approximative. L'adresse configuree par l'utilisateur est aussi geocodee pour calculer le rayon de surveillance.

PyroVeille est une aide de surveillance et ne remplace pas les consignes officielles des autorites.
