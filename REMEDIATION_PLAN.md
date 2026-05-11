# Captua – Remediation Plan

Analysiert: `capture.py`, `tools.py`, `items.py`, `canvas.py`, `overlay.py`, `settings.py`, `history.py`, `main.py`  
Stand: 2026-05-09 — aktualisiert 2026-05-11 (R-01–R-12, R-14, R-17 erledigt; R-13, R-15, R-16 offen)

---

## Befunde nach Kategorie

| ID | Kategorie | Befund & Maßnahme | Priorität | Aufwand |
|----|-----------|-------------------|-----------|---------|
| ~~R-01~~ | ~~Korrektheit~~ | ~~**`History.clear()` fehlt.**~~ ✅ Erledigt: `History.clear()` ist implementiert. | ~~P0~~ | ~~S~~ |
| ~~R-02~~ | ~~Sicherheit~~ | ~~**Orphaned Temp-Dateien mit Screenshot-Inhalt.**~~ ✅ Erledigt: Beide Tools verwenden `QBuffer`/`BytesIO` statt `/tmp`-Dateien. | ~~P0~~ | ~~S~~ |
| ~~R-03~~ | ~~Codequalität~~ | ~~**Doppelte Imports in Funktionsrümpfen.**~~ ✅ Erledigt: `QCursor`/`QApplication` auf Modulebene verschoben. | ~~P0~~ | ~~S~~ |
| ~~R-04~~ | ~~Performance~~ | ~~**Disk-Roundtrip in Blur- und Magnifier-Pipeline.**~~ ✅ Erledigt: Beide Tools verwenden `QBuffer`/`BytesIO` für In-Memory-Verarbeitung. | ~~P1~~ | ~~M~~ |
| ~~R-05~~ | ~~Performance~~ | ~~**`_MagnifierPosWatcher` 30-ms-Poll.**~~ ✅ Erledigt (bereits korrekt): Render-Update per 80-ms-Debounce-Timer; Poll vergleicht nur `QPointF`-Objekte. | ~~P1~~ | ~~M~~ |
| ~~R-06~~ | ~~Performance~~ | ~~**O(n) `boundingRect()`**~~ ✅ Erledigt (bereits korrekt): `PenItem`/`MarkerItem` nutzen `_raw_bbox`, inkrementell in `add_point()` aktualisiert. | ~~P1~~ | ~~S~~ |
| ~~R-07~~ | ~~Performance~~ | ~~**`ShapeItem._build_path()` bei jedem Repaint.**~~ ✅ Erledigt (bereits korrekt): `_cached_path` vorhanden; `paint()` baut nur neu wenn `None`; `setRect()` invalidiert Cache. | ~~P1~~ | ~~S~~ |
| ~~R-08~~ | ~~Performance~~ | ~~**`CanvasView.drawBackground()` iteriert alle Scene-Items.**~~ ✅ Erledigt (bereits korrekt): `drawBackground()` liest `scene._content_rect` (gecachtes Feld). | ~~P1~~ | ~~S~~ |
| ~~R-09~~ | ~~UX/Persistenz~~ | ~~**Toolbar-Änderungen werden bei Fensterschluss verworfen.**~~ ✅ Erledigt: `OverlayWindow.closeEvent()` persistiert alle `_props`-Felder via `save_settings()`. | ~~P1~~ | ~~S~~ |
| ~~R-10~~ | ~~Sicherheit~~ | ~~**`save_settings()` ist nicht atomisch.**~~ ✅ Erledigt: `settings.py` schreibt in `.settings.tmp` und verwendet `Path.replace()` (atomisches Rename). | ~~P1~~ | ~~S~~ |
| ~~R-11~~ | ~~Kodequalität~~ | ~~**Broad `except Exception: return None`**~~ ✅ Erledigt: Beide Tools verwenden spezifische Exception-Typen und `logging.exception()`. | ~~P1~~ | ~~S~~ |
| ~~R-12~~ | ~~Kodequalität~~ | ~~**`CropTool` greift auf privates Attribut zu.**~~ ✅ Erledigt (bereits korrekt): `CropOverlayItem` hat öffentliches Property `crop_rect`; `CropTool` nutzt es. | ~~P2~~ | ~~S~~ |
| R-13 | Architektur | **Keine Plattformabstraktion.** `grim`, `slurp`, `hyprctl` und `wl-copy` sind direkt in `capture.py` hart verdrahtet. Das Modul ist ohne Stub nicht testbar; eine künftige X11- oder KDE-Unterstützung erfordert Umschreiben. → Ein `CaptureBackend`-Protocol (oder ABC) mit den Methoden `capture_region()`, `capture_screen()`, `capture_window()`, `copy_to_clipboard()` definieren; `GrimBackend` als erste Implementierung. `main.py` wählt das Backend; Stubs ermöglichen Unit-Tests. | P2 | L |
| ~~R-14~~ | ~~Architektur~~ | ~~**`QGraphicsView.FullViewportUpdate`**~~ ✅ Erledigt: Auf `SmartViewportUpdate` umgestellt. | ~~P2~~ | ~~M~~ |
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
