# Jarolift Controller – Home Assistant Integration

HACS-Integration für den [ESP32-Jarolift-Controller](https://github.com/dewenni/ESP32-Jarolift-Controller) von dewenni.

Kommuniziert direkt per **WebSocket** (`ws://<IP>/ws`) mit dem ESP32 – kein MQTT erforderlich.

---

## Installation

1. In HACS → **Eigene Repositories** → URL dieses Repos hinzufügen → Kategorie: `Integration`
2. Integration installieren
3. Home Assistant neu starten
4. **Einstellungen → Integrationen → Hinzufügen → Jarolift Controller**

---

## Einrichtung

Der Setup-Dialog fragt:

| Feld | Beschreibung |
|---|---|
| IP-Adresse | IP des ESP32 (z.B. `192.168.66.43`) |
| Anzahl Kanäle | 1–16 |
| Anzahl Gruppen | 0–6 |
| Kanal-Namen | Individueller Name pro Kanal |
| Gruppen-Namen | Individueller Name pro Gruppe |

---

## Entitäten

Jeder Kanal und jede Gruppe erscheint als **Cover-Entität** in Home Assistant mit:

- ▲ Öffnen (hoch)
- ▼ Schließen (runter)
- ■ Stop

### Schattenstellung

Zusätzlich steht ein Service für die Schattenstellung bereit:

```yaml
service: jarolift.shade
data:
  entity_id: cover.wohnzimmer
```

### Beispiel-Automation

```yaml
automation:
  - alias: "Rollladen bei Sonnenuntergang schließen"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: cover.close_cover
        target:
          entity_id: cover.wohnzimmer
```

---

## Hinweis zum Status

Die Jarolift-Motoren senden **keinen Status-Rückkanal**. Der angezeigte Zustand in HA entspricht dem zuletzt gesendeten Befehl – nicht dem tatsächlichen Motorstatus.

---

## Voraussetzungen

- Home Assistant 2023.x oder neuer
- ESP32-Jarolift-Controller v1.x mit WebUI aktiv
- Python-Paket `websockets>=11.0` (wird automatisch installiert)
