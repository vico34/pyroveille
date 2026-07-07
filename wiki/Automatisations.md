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

PyroVeille peut envoyer directement une notification Telegram si l'integration Telegram de Home Assistant expose une entite `notify.*` ou un service legacy `notify.telegram`.

### Cote Home Assistant

Configurez Telegram dans Home Assistant avant d'activer l'option PyroVeille. Une fois Telegram configure, verifiez la cible disponible. Les versions recentes de Home Assistant exposent souvent une entite `notify.*` a utiliser avec `notify.send_message`, par exemple :

```text
notify.telegram_bot_chat
```

Les configurations legacy peuvent exposer un service :

```text
notify.telegram
```

Vous pouvez tester une entite moderne depuis les outils de developpement avec :

```yaml
service: notify.send_message
data:
  entity_id: notify.telegram_bot_chat
  message: Telegram est pret pour PyroVeille.
```

Pour un service legacy, utilisez `service: notify.telegram` avec `message`.

### Cote PyroVeille

Dans les options PyroVeille :

- activez `Notifier via Telegram` ;
- saisissez l'entite complete, par exemple `notify.telegram_bot_chat`, pour le mode moderne ;
- ou laissez `telegram` si votre service legacy est `notify.telegram` ;
- ou saisissez seulement le suffixe du service legacy, par exemple `telegram_maison` pour `notify.telegram_maison`.

Si la cible n'est pas disponible, PyroVeille conserve les notifications persistantes, note l'erreur dans les diagnostics et ignore l'envoi Telegram sans bloquer la mise a jour.
