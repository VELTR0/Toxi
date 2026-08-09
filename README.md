# Toxi

Ein kleines 2D-Lernspiel für Toxikologie mit zufälligen Microgames im Stil eines ruhigen WarioWare-Mixes: schnelle Szenenwechsel, aber **ohne Zeitlimit**.

## Spielprinzip

- Jede Lernfrage hat **zwei Microgame-Level**, die pro Versuch abwechseln.
- Ein gewonnenes Microgame gibt der konkreten Frage **+1 Lernpunkt**.
- Bei **3/3 Lernpunkten** gilt die Frage als gelernt und wird nicht mehr gezogen.
- Jede richtige Lösung erhöht zusätzlich den **Global Score**.
- Sobald alle Fragen 3/3 erreicht haben, erscheint der Finished-Screen.
- Fortschritt wird lokal gespeichert und bleibt zwischen Starts erhalten.

Aktuell enthaltene Microgame-Typen:

1. **Sword Arena** - top-down bewegen und die richtige, herumfliegende Antwort mit dem Schwert treffen.
2. **Labyrinth-Portale** - im Top-down-Labor zum richtigen Antwortportal laufen.
3. **Platform Gates** - kleiner One-Screen-Platformer; die richtige Antworttür erreichen.
4. **Lab Catcher** - die richtige Antwortkapsel mit einem Fangkorb erwischen.
5. **Comet Click** - den richtigen DNA-Kometen anklicken.

Die Fragen sind aus den im Projekt bereitgestellten Toxikologie-Notizen abgeleitet. Im Ergebnisbildschirm wird die zugehörige PDF-Seite angezeigt.

## Installation unter Windows

Python 3.11+ empfohlen.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Alternativ in `cmd.exe`:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

## Steuerung

- `WASD` oder Pfeiltasten: bewegen
- `LEERTASTE`: springen / Schwertschlag (abhängig vom Microgame)
- Maus: Comet-Click
- `ESC`: zum Menü bzw. beenden
- `R` im Menü: gespeicherten Lernfortschritt zurücksetzen

## Fortschritt

Unter Windows wird der Spielstand hier gespeichert:

```text
%APPDATA%\Toxi\progress.json
```

## Neue Frage hinzufügen

In `toxi/data.py` einen weiteren Eintrag ergänzen:

```python
{
    "id": "eindeutige_id",
    "page": 1,
    "question": "Frage?",
    "answers": ["Richtig", "Falsch A", "Falsch B"],
    "correct": 0,
    "explanation": "Kurze Lern-Erklärung.",
    "variants": ["sword_arena", "platform_gates"],
}
```

Um später mehr als zwei Level pro Frage zu erlauben, einfach weitere Variantennamen in `variants` ergänzen. Der Spielkern kann bereits mit beliebig vielen Varianten umgehen; die aktuelle Validierung fordert absichtlich genau zwei.

## Projektstruktur

```text
main.py
requirements.txt
toxi/
  data.py          # Fragen + zwei Levelzuordnungen je Frage
  game.py          # Szenenwechsel, Score, Lernlogik
  microgames.py    # alle Microgame-Klassen
  progress.py      # persistenter Lernfortschritt
  ui.py            # Fonts, Panels, Text-Wrapping
```
