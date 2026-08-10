# Toxi

Ein kleines 2D-Lernspiel für Toxikologie mit zufälligen Microgames im Stil eines ruhigen WarioWare-Mixes: schnelle Szenenwechsel, aber **ohne Zeitlimit**.

## Spielprinzip

- Jede Lernfrage hat **zwei Microgame-Level**, die pro Versuch abwechseln.
- Ein gewonnenes Microgame gibt der konkreten Frage **+1 Lernpunkt**.
- Bei **3/3 Lernpunkten** gilt die Frage als gelernt und wird nicht mehr gezogen.
- Jede richtige Lösung erhöht zusätzlich den **Global Score**.
- Sobald alle Fragen 3/3 erreicht haben, erscheint der Finished-Screen.
- Fortschritt wird lokal gespeichert und bleibt zwischen Starts erhalten.
- Bei der Zufallsauswahl wird zuerst gleichverteilt zwischen den aktuell verfügbaren nächsten Microgame-Typen gewählt und danach eine passende Frage gezogen. Dadurch dominiert kein Microgame nur deshalb, weil es mehr Fragen zugeordnet bekommen hat.

Aktuell enthaltene Microgame-Typen:

1. **Sword Arena** - top-down bewegen und die richtige, herumfliegende Antwort mit dem Schwert treffen.
2. **Labyrinth-Portale** - im Top-down-Labor zum richtigen Antwortportal laufen.
3. **Platform Gates** - kleiner One-Screen-Platformer; die richtige Antworttür erreichen.
4. **Lab Catcher** - die richtige Antwortkapsel mit einem Fangkorb erwischen.
5. **Comet Click** - einen DNA-Kometen auswählen und bestätigen; Maus bleibt optional.
6. **Battle** - retro Monsterkampf-Stil: die drei Antworten sind Attacken. Bei einer richtigen Attacke wird die Frage besiegt; bei einer falschen kontert die Frage und besiegt den Spieler.

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

## Microgame gezielt debuggen

Ein bestimmtes Microgame kann direkt gestartet werden, ohne den Lernfortschritt, Score oder die Versuche zu verändern:

```powershell
python main.py --debug-microgame pokemon_battle
```

Verfügbare Namen:

```text
sword_arena
maze_portals
platform_gates
lab_catcher
comet_click
pokemon_battle
```

Standardmäßig wird dabei bei jedem Durchlauf eine zufällige Frage verwendet. Optional kann zusätzlich eine konkrete Frage-ID festgelegt werden:

```powershell
python main.py --debug-microgame platform_gates --debug-question pseudoallergy
```

Nach dem Ergebnis startet `A` / `ENTER` dasselbe Debug-Microgame erneut. `B` / `ESC` führt zurück ins Hauptmenü.

## Controller-Steuerung

Das komplette Spiel ist ohne Maus und Tastatur spielbar. Toxi nutzt Pygames SDL-Controller-Schicht und zeigt im Hauptmenü den erkannten Controller an.

- **Linker Stick / D-Pad**: bewegen bzw. Auswahl ändern
- **A**: bestätigen / springen / Hauptaktion
- **X**: alternative Hauptaktion, z. B. Schwertschlag oder Sprung
- **B**: zurück zum Menü / beenden
- **START**: im Hauptmenü ebenfalls starten
- **Y**: Lernfortschritt zurücksetzen

Microgame-spezifisch:

- **Sword Arena**: Stick/D-Pad bewegen, A oder X schlagen
- **Labyrinth-Portale**: Stick/D-Pad bewegen und ins richtige Portal laufen
- **Platform Gates**: Stick/D-Pad laufen, A oder X springen
- **Lab Catcher**: Stick/D-Pad links/rechts bewegen
- **Comet Click**: Stick/D-Pad zwischen Kometen wechseln, A bestätigen
- **Battle**: Stick/D-Pad zwischen Attacken wechseln, A bestätigen

Der Controller kann auch nach dem Start des Spiels angeschlossen werden; Toxi sucht automatisch erneut nach einem Gamepad. Bei richtigen bzw. falschen Antworten wird, sofern unterstützt, kurzes Rumble-Feedback ausgelöst.

### Tastatur-/Maus-Fallback

- `WASD` oder Pfeiltasten: bewegen
- `LEERTASTE`: springen / Schwertschlag / bestätigen
- `ENTER` / `LEERTASTE`: bestätigen
- Maus: optional bei Comet Click und Battle
- `ESC`: zurück / beenden
- `R`: Fortschritt zurücksetzen

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
  input.py         # Controller- und Tastatur-Abstraktion
  microgames/      # einzelne 2D-Microgames
  progress.py      # persistenter Lernfortschritt
  ui.py            # Fonts, Panels, Text-Wrapping
```
