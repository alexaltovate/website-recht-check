---
name: website-recht-check
description: Prüft deutsche Websites auf rechtliche Pflichten und Abmahnrisiken — Impressum/Anbieterkennzeichnung (§ 5 DDG, inkl. Erreichbarkeit in 2 Klicks und Aktualität), Datenschutzerklärung (Art. 13 DSGVO), Cookie-Banner/Consent (§ 25 TDDDG), Barrierefreiheit (BFSG) und KI-Transparenz (EU AI Act, Art. 50). Use when checking a German website or its source code for legal compliance, when asked about Impressum, Datenschutz, DSGVO, Cookie-Banner, BFSG/Barrierefreiheit or AI-Act labeling, or "ist meine Website rechtssicher". Works on a live URL or on a code repository (e.g. Lovable export, React/Next project).
---

# Website-Recht-Check (Deutschland)

Prüft, ob eine Website die deutschen Pflichten erfüllt, die in der Praxis am
häufigsten fehlen oder veraltet sind. Liefert einen priorisierten Report mit
konkreten Fixes — keine Rechtsberatung.

## Wann dieser Skill greift

Nutzer will wissen, ob eine Website (eigene oder fremde) rechtssicher ist:
Impressum, Datenschutz, Cookies, Barrierefreiheit, KI-Kennzeichnung. Egal ob als
Live-URL oder als Quellcode-Projekt.

## Ablauf

1. **Ziel klären.** Frage nach einer URL **oder** einem Pfad zum Quellcode, falls
   nicht genannt. URL → Laufzeit-Check. Pfad → Code-Check. Bei eigener Website mit
   Tracking lohnt zusätzlich der Deep-Modus.

2. **Engine ausführen.** Aus dem Skill-Verzeichnis:

   ```bash
   # Einmalig:
   pip install -r scripts/requirements.txt
   # Optional für den Deep-Modus (echtes Laden, beweist Tracking vor Einwilligung):
   pip install playwright && playwright install chromium

   # Live-Check:
   python scripts/check.py https://example.de --json /tmp/wrc.json
   # Live-Check mit Laufzeit-Beweis + echtem WCAG-Audit (axe-core):
   python scripts/check.py https://example.de --deep --json /tmp/wrc.json
   # Code-Check:
   python scripts/check.py /pfad/zum/projekt --json /tmp/wrc.json
   ```

   Die Engine schreibt einen Markdown-Report und (mit `--json`) strukturierte
   Befunde. Exit-Code 1 = mindestens ein FAIL (für CI nutzbar).

3. **Befunde interpretieren — NICHT roh ausgeben.** Lies das JSON. Die Engine
   liefert deterministische Maschinen-Befunde (FAIL/WARN/PASS/MANUAL/INFO). Deine
   Aufgabe ist die juristische Einordnung und Priorisierung anhand der Dateien in
   `references/`. Lies die jeweils betroffene Referenz, bevor du bewertest:
   - `references/impressum-ddg.md`
   - `references/datenschutz-dsgvo.md`
   - `references/cookies-tdddg.md`
   - `references/bfsg-barrierefreiheit.md`
   - `references/ai-act-art50.md`

4. **MANUAL-Punkte selbst entscheiden.** Die Engine kann manches nicht beurteilen
   — du schon, anhand des Kontexts:
   - **BFSG-Betroffenheit:** B2C mit Vertragsabschluss/Shop/Buchung? Kleinst­unternehmen
     (< 10 MA **und** ≤ 2 Mio. € Umsatz)? Produkte vs. nur Dienstleistung? Siehe Referenz.
     Im `--deep`-Modus läuft zusätzlich ein echter WCAG-Audit via **axe-core** (dieselbe
     Engine wie Lighthouses Accessibility-Score) — Kontraste, ARIA, Labels. Für einen
     vollständigen Lighthouse-Report (inkl. Performance/SEO) steht, falls verfügbar, das
     `chrome-devtools`-MCP-Tool `lighthouse_audit` bereit.
   - **AI-Act Art. 50:** Ist ein erkannter Chatbot KI-gestützt? Gibt es foto-realistische
     KI-Bilder oder ungeprüfte KI-Texte? Reines KI-als-Werkzeug ist nicht kennzeichnungspflichtig.
   - Frage gezielt nach, wenn der Geschäftstyp für die Einordnung fehlt.

5. **Report liefern.** Auf Deutsch, priorisiert nach Schwere:
   - **Sofort beheben (FAIL)** — Verstoß/Abmahnrisiko, mit konkretem Fix + Rechtsgrundlage
   - **Prüfen/Nachbessern (WARN)**
   - **Manuell klären (MANUAL)** — mit Entscheidungshilfe
   - **In Ordnung (PASS)** — kurz bestätigen
   Pro Punkt: was ist das Problem, warum (Rechtsgrundlage), wie fixen.
   Schließe **immer** mit dem Hinweis, dass dies keine Rechtsberatung ersetzt.

## Grenzen

- Heuristik, kein Anwalt. FAIL = hohe Wahrscheinlichkeit, kein Urteil.
- **SPA/JS-gerenderte Seiten (React, Lovable, Vue …):** der Baseline-Fetch sieht nur
  die Shell — Impressum/Datenschutz scheinen dann fälschlich „nicht gefunden". Bei
  solchen Seiten **immer `--deep`** verwenden: dann werden Links und Inhalte auf dem
  echten, gerenderten DOM geprüft. Ohne `--deep` sind „nicht gefunden"-FAILs bei
  SPAs mit Vorsicht zu behandeln.
- Content-Tiefe (z.B. vollständige Datenschutzerklärung, echte Drittland-Garantien)
  braucht menschliche Prüfung. A11y: `--deep` deckt via axe-core Kontraste/ARIA/Labels
  ab; rein manuell bleiben Fokus-Reihenfolge und Sinnzusammenhang.
- Stand der Referenzen: Juni 2026. Fristen/Rechtslage ändern sich — bei kritischen
  Fällen Quelle und Aktualität gegenprüfen.
