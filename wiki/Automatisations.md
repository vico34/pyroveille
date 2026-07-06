# Automatisations

PyroVeille emet l'evenement `pyroveille_nearby_fire` lorsqu'un nouvel incendie entre dans le perimetre configure.

## Notification mobile

```yaml
alias: Alerte incendie proche
mode: queued
trigger:
  - platform: event
    event_type: pyroveille_nearby_fire
action:
  - service: notify.mobile_app_votre_telephone
    data:
      title: "Alerte incendie proche"
      message: >
        {{ trigger.event.data.title }} a {{ trigger.event.data.distance_km | round(1) }} km.
      data:
        url: "{{ trigger.event.data.url }}"
```

## Telegram

PyroVeille peut envoyer directement une notification Telegram si l'integration Telegram de Home Assistant expose un service `notify`.

### Cote Home Assistant

Configurez Telegram dans Home Assistant avant d'activer l'option PyroVeille. Une fois Telegram configure, verifiez le nom du service dans `Outils de developpement > Services`. Le service attendu ressemble a :

```text
notify.telegram
```

ou :

```text
notify.telegram_maison
```

Vous pouvez tester le service depuis les outils de developpement avec :

```yaml
service: notify.telegram
data:
  title: Test PyroVeille
  message: Telegram est pret pour PyroVeille.
```

### Cote PyroVeille

Dans les options PyroVeille :

- activez `Notifier via Telegram` ;
- laissez `Service Telegram notify` a `telegram` si votre service est `notify.telegram` ;
- saisissez seulement le suffixe du service pour un autre nom, par exemple `telegram_maison` pour `notify.telegram_maison`.

Si le service n'est pas disponible, PyroVeille conserve les notifications persistantes et ignore l'envoi Telegram sans bloquer la mise a jour.
