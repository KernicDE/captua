# Captua – Remediation Plan

Analysiert: `capture.py`, `tools.py`, `items.py`, `canvas.py`, `overlay.py`, `settings.py`, `history.py`, `main.py`  
Stand: 2026-05-09 — aktualisiert 2026-05-11 (erledigte Punkte markiert)

---

## Befunde nach Kategorie

| ID | Kategorie | Befund & Maßnahme | Priorität | Aufwand |
|----|-----------|-------------------|-----------|---------|
| ~~R-01~~ | ~~Korrektheit~~ | ~~**`History.clear()` fehlt.**~~ ✅ Erledigt: `History.clear()` ist implementiert. | ~~P0~~ | ~~S~~ |
| ~~R-02~~ | ~~Sicherheit~~ | ~~**Orphaned Temp-Dateien mit Screenshot-Inhalt.**~~ ✅ Erledigt: Beide Tools verwenden `QBuffer`/`BytesIO` statt `/tmp`-Dateien. | ~~P0~~ | ~~S~~ |
| R-03 | Codequalität | **Doppelte Imports in Funktionsrümpfen.** `copy_pixmap_to_clipboard()` importiert `tempfile` und `pathlib.Path` erneut innerhalb der Funktion, obwohl `tempfile` bereits auf Modulebene importiert ist. `capture_window()` importiert `json` innerhalb des Funktionsrumpfes. → Alle Imports an den Modulanfang verschieben. (Teilweise erledigt: `json` wurde verschoben; `QCursor`/`QApplication` sind noch lokal in `capture_screen_pixels()` importiert.) | P0 | S |
| ~~R-04~~ | ~~Performance~~ | ~~**Disk-Roundtrip in Blur- und Magnifier-Pipeline.**~~ ✅ Erledigt: Beide Tools verwenden `QBuffer`/`BytesIO` für In-Memory-Verarbeitung. | ~~P1~~ | ~~M~~ |
| R-05 | Performance | **`_MagnifierPosWatcher` 30-ms-Poll mit `scene.render()`.** Bei jeder Positionsänderung des Magnifier-Items rendert der Watcher die gesamte Quellregion aus der Szene, skaliert das Ergebnis und aktualisiert das Pixmap. Für eine 4K-Quellregion: unkontrollierter CPU-Burst bei Drag. → Bewegungsrate mit einem Debounce-Timer (≥ 100 ms nach letztem Move-Event) begrenzen; alternativ `QGraphicsItem.ItemSendsGeometryChanges` Flag setzen und `itemChange(ItemPositionHasChanged)` verwenden, da das in PySide6 ≥ 6.5 für Position funktioniert. | P1 | M |
| R-06 | Performance | **O(n) `boundingRect()` in `PenItem` und `MarkerItem`.** Beide iterieren bei jedem Aufruf über alle gespeicherten Punkte (`min(xs)`, `max(xs)`) um die Bounding Box zu berechnen. Bei langen Strichen (hunderte Punkte) wird dies bei jedem Repaint ausgeführt. → Bounding Box inkrementell in `add_point()` aktualisieren und als Attribut cachen; `boundingRect()` gibt den Cache zurück. | P1 | S |
| R-07 | Performance | **`ShapeItem._build_path()` bei jedem Repaint neu berechnet.** `paint()` ruft `self._build_path()` auf, der alle Bezier- und Polygon-Koordinaten für den aktuellen `_rect` neu konstruiert. → `_build_path()` nur in `setRect()`, `set_line_width()` und `__init__` aufrufen; den resultierenden `QPainterPath` als `_cached_path` speichern. `paint()` verwendet nur den Cache. | P1 | S |
| R-08 | Performance | **`CanvasView.drawBackground()` iteriert alle Scene-Items bei jedem Frame.** Die Methode berechnet `content_rect` durch `item.mapRectToScene(item.boundingRect())` für jedes Item. Bei vielen Annotationen: O(n) pro Repaint-Zyklus. → `content_rect` als Attribut der `CanvasScene` vorhalten; bei `addItem()`/`removeItem()` und `_expand_scene_if_needed()` aktualisieren. `drawBackground()` liest nur das Attribut. | P1 | S |
| ~~R-09~~ | ~~UX/Persistenz~~ | ~~**Toolbar-Änderungen werden bei Fensterschluss verworfen.**~~ ✅ Erledigt: `OverlayWindow.closeEvent()` persistiert alle `_props`-Felder via `save_settings()`. | ~~P1~~ | ~~S~~ |
| ~~R-10~~ | ~~Sicherheit~~ | ~~**`save_settings()` ist nicht atomisch.**~~ ✅ Erledigt: `settings.py` schreibt in `.settings.tmp` und verwendet `Path.replace()` (atomisches Rename). | ~~P1~~ | ~~S~~ |
| ~~R-11~~ | ~~Kodequalität~~ | ~~**Broad `except Exception: return None`**~~ ✅ Erledigt: Beide Tools verwenden spezifische Exception-Typen und `logging.exception()`. | ~~P1~~ | ~~S~~ |
| R-12 | Kodequalität | **`CropTool` greift auf `self._active_item._crop` zu (privates Attribut).** Das verletzt Kapselung; jede Umbenennung des Attributs in `CropOverlayItem` bricht `CropTool`. → `CropOverlayItem` ein öffentliches Property `crop_rect` spendieren. | P2 | S |
| R-13 | Architektur | **Keine Plattformabstraktion.** `grim`, `slurp`, `hyprctl` und `wl-copy` sind direkt in `capture.py` hart verdrahtet. Das Modul ist ohne Stub nicht testbar; eine künftige X11- oder KDE-Unterstützung erfordert Umschreiben. → Ein `CaptureBackend`-Protocol (oder ABC) mit den Methoden `capture_region()`, `capture_screen()`, `capture_window()`, `copy_to_clipboard()` definieren; `GrimBackend` als erste Implementierung. `main.py` wählt das Backend; Stubs ermöglichen Unit-Tests. | P2 | L |
| R-14 | Architektur | **`QGraphicsView.FullViewportUpdate` deaktiviert Dirty-Region-Tracking.** Jede Szenenänderung triggert einen vollständigen Viewport-Repaint, auch bei kleinen Annotationsänderungen. → Auf `MinimalViewportUpdate` oder `SmartViewportUpdate` wechseln; vorher sicherstellen, dass `prepareGeometryChange()` in allen Items konsistent aufgerufen wird (bereits größtenteils der Fall). | P2 | M |
| R-15 | Kodequalität | **Fehlende Typ-Annotationen auf Basisklassen und Callback-Signaturen.** `Command.do()`/`undo()`, `Tool.activate()`/`deactivate()`, `CanvasScene._expand_scene_if_needed()`, `_MagnifierPosWatcher._check()` sowie die `parent`-Parameter vieler `QGraphicsItem`-Subklassen sind unannotiert. → Mypy im `strict`-Modus aktivieren (erst nach R-01–R-03); fehlende Annotationen ergänzen; `QGraphicsItem`-`parent`-Parameter auf `QGraphicsItem | None` typisieren. | P2 | M |
| R-16 | UX | **`EmojiItem` setzt `QFont("Noto Color Emoji", size)` ohne Fallback.** Ist das Font-Paket nicht installiert, rendert Qt mit dem System-Fallback, was Emoji-Rendering kaputt macht (monochrom oder fehlend). → Prüfen ob der Font verfügbar ist (`QFontDatabase.families()`) und ggf. auf `"Segoe UI Emoji"` (Windows) oder `""` (Qt-Systemfallback) zurückfallen; oder Font im App-Bundle mitliefern. | P2 | S |
| ~~R-17~~ | ~~Sicherheit~~ | ~~**Kein Zeitlimit für Subprozesse.**~~ ✅ Erledigt: `capture.py` verwendet `_TIMEOUT`-Konstante in allen `subprocess.run()`-Aufrufen. | ~~P2~~ | ~~S~~ |

---

## Zu integrierende Tools

| Tool | Zweck | Befehl |
|------|-------|--------|
| **Ruff** | Linting + Autoformat (ersetzt Flake8, isort, pyupgrade) | `ruff check captua/ --fix` |
| **Mypy** | Statische Typrüfung | `mypy captua/ --strict` |
| **Bandit** | Security-Scan (Subprocess-Misuse, Tempfile-Risiken) | `bandit -r captua/` |
| **pytest** | Test-Framework (derzeit keine Tests vorhanden) | `pytest tests/` |
| **pytest-qt** | Qt-Widget-Tests ohne Display | `pip install pytest-qt` |
| **pre-commit** | Hooks für Ruff + Mypy vor jedem Commit | `.pre-commit-config.yaml` |

---

## Kritischer Pfad (empfohlene Reihenfolge)

1. **R-01** → R-02 → R-03 (Bugs/Crashes, kein Aufwand)
2. **R-09** → R-10 (Datenverlust und Korruption)
3. **R-04** → R-06 → R-07 (Performance, größter Impact für 4K)
4. **R-11** → R-17 (Observability und Robustheit)
5. **R-05** → R-08 → R-14 (UI-Responsiveness)
6. **R-13** → R-15 (Architektur/Testbarkeit, langfristig)
