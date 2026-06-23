# Kinoheld – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Bindet das aktuelle Kinoprogramm über die [Kinoheld](https://www.kinoheld.de) GraphQL-API in Home Assistant ein.

## Features

- **Programm-Sensor** – Anzahl der aktuell laufenden Filme als State, komplette Filmliste als Attribut
- **Nächste-Vorstellung-Sensor** – Titel + Details des nächst­möglichen Films
- Konfiguration über die UI (Config Flow)
- Intervall anpassbar (Standard: 60 min)
- Mehrere Kinos gleichzeitig möglich

## Installation via HACS

1. HACS → **Integrationen** → drei Punkte → *Benutzerdefiniertes Repository hinzufügen*
2. URL: `https://github.com/DHansel91/kinoheld-ha`, Kategorie: **Integration**
3. Integration installieren und HA neu starten

## Manuelle Installation

```
custom_components/kinoheld/  →  <config>/custom_components/kinoheld/
```
HA neu starten.

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Kinoheld**
2. Suchbegriff eingeben (z. B. `Weiden`)
3. Kino aus der Ergebnisliste wählen
4. Fertig – zwei Sensoren werden angelegt

## Sensoren

| Entität | State | Wichtige Attribute |
|---|---|---|
| `sensor.kinoheld_<kino>_programm` | Anzahl Filme | `movies` (Liste), `movie_count` |
| `sensor.kinoheld_<kino>_naechste_vorstellung` | Filmtitel | `next_show`, `duration`, `genres`, `poster_url` |

### Beispiel-Attribut `movies`

```yaml
- title: "Deadpool & Wolverine"
  duration: 127
  genres: ["Action", "Komödie"]
  next_show: "2025-07-01T19:30:00"
  show_count: 4
  url: "https://www.kinoheld.de/..."
  poster_url: "https://..."
  shows:
    - beginning: "2025-07-01T19:30:00"
      language: "de"
      technology: "2D"
```

## Lovelace-Beispiel

```yaml
type: markdown
content: >
  ## 🎬 {{ state_attr('sensor.kinoheld_cineplex_weiden_programm', 'cinema_name') }}
  {% for film in state_attr('sensor.kinoheld_cineplex_weiden_programm', 'movies') %}
  **{{ film.title }}** ({{ film.duration }} min) – {{ film.genres | join(', ') }}
  Nächste Vorstellung: {{ film.next_show }}
  {% endfor %}
```

## Lizenz

MIT
