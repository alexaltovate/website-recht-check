# website-recht-check

**Claude-Skill, der deutsche Websites auf rechtliche Pflichten und Abmahnrisiken prüft.**
Impressum · Datenschutz · Cookies/Consent · Barrierefreiheit · KI-Transparenz.

> Die wenigsten Websites in Deutschland sind sauber. Das Impressum ist veraltet
> (noch „§ 5 TMG"), versteckt oder kaum erreichbar; Google Analytics und der
> Meta-Pixel laden, bevor irgendjemand zugestimmt hat; die Datenschutzerklärung
> nennt die Hälfte der eingesetzten Tools nicht; das BFSG (seit 28.06.2025) und die
> KI-Kennzeichnung (AI Act, ab 02.08.2026) hat kaum jemand auf dem Schirm. Dieser
> Skill findet genau das — in Minuten, auf einer Live-URL oder im Quellcode.

Geprüft werden:

| Bereich | Grundlage | Beispiel-Checks |
|---|---|---|
| **Impressum** | § 5 DDG | Erreichbar in ≤ 2 Klicks? Aktuell (DDG statt TMG)? Pflichtangaben (Anschrift, Vertreter, HR, USt-IdNr.)? Toter OS-Plattform-Link? |
| **Datenschutz** | Art. 13 DSGVO | Vorhanden & erreichbar? Als PDF versteckt (= Problem)? Kern-Pflichtangaben? |
| **Cookies/Consent** | § 25 TDDDG | Tracker ohne Consent-Tool? **Lädt Tracking vor der Einwilligung?** „Ablehnen" gleichwertig zu „Akzeptieren"? |
| **Barrierefreiheit** | BFSG | `lang`-Attribut, Alt-Texte, Barrierefreiheitserklärung; BFSG-Betroffenheit |
| **KI-Transparenz** | EU AI Act, Art. 50 | KI-Chatbot ohne Kennzeichnung? KI-Bilder/-Texte kennzeichnungspflichtig? |

*Keine Rechtsberatung — eine schnelle, reproduzierbare Risiko-Vorprüfung. Bei
kritischen Fällen Fachanwalt.*

---

## Installation als Claude-Skill

Repo in das Skill-Verzeichnis kopieren:

```bash
git clone https://github.com/<dein-user>/website-recht-check.git
cp -r website-recht-check ~/.claude/skills/website-recht-check
pip install -r ~/.claude/skills/website-recht-check/scripts/requirements.txt
# optional für den Deep-Modus:
pip install playwright && playwright install chromium
```

Danach in Claude Code einfach fragen:
> „Prüf mal https://example.de auf Rechtssicherheit"

Claude erkennt den Skill, führt die Engine aus, liest die Befunde und liefert einen
priorisierten Report mit konkreten Fixes.

## Nutzung ohne Claude (Standalone-CLI)

Die Engine läuft auch pur:

```bash
pip install -r scripts/requirements.txt

python scripts/check.py https://example.de            # Live-Check
python scripts/check.py https://example.de --deep     # + echtes Laden (Playwright)
python scripts/check.py ./mein-projekt                # Quellcode prüfen
python scripts/check.py https://example.de --json out.json
```

Ausgabe: ein Markdown-Report (`compliance-report.md`) und optional JSON.
Exit-Code `1`, sobald ein **FAIL** vorliegt — direkt CI-tauglich.

## Aufbau

```
website-recht-check/
├── SKILL.md            # Claude-Skill: Orchestrierung + juristische Einordnung
├── scripts/
│   ├── check.py        # deterministische Prüf-Engine (Live + Code, optional Playwright)
│   └── requirements.txt
├── references/         # das Rechtswissen, das Claude beim Bewerten liest
│   ├── impressum-ddg.md
│   ├── datenschutz-dsgvo.md
│   ├── cookies-tdddg.md
│   ├── bfsg-barrierefreiheit.md
│   └── ai-act-art50.md
└── examples/
    └── sample-report.md
```

Die Engine liefert **deterministische** Befunde (FAIL/WARN/PASS/MANUAL/INFO).
Die juristische Gewichtung und die MANUAL-Entscheidungen (BFSG-Betroffenheit,
Deepfake-Einstufung) trifft der Claude-Skill anhand von `references/`. Beides ist
bewusst getrennt: die Skripte sind nachvollziehbar und CI-fähig, die Bewertung
bleibt kontextabhängig.

## Grenzen

- Heuristik, kein Anwalt. **FAIL = hohe Wahrscheinlichkeit**, kein Urteil.
- Inhaltliche Tiefe (vollständige Datenschutzerklärung, Drittland-Garantien) und
  A11y-Details (Kontraste, Fokus-Reihenfolge) brauchen menschliche Prüfung.
- Rechtsstand der Referenzen: **Juni 2026**. Fristen ändern sich — bei kritischen
  Fällen Quelle und Aktualität gegenprüfen.

## Mitmachen

Tracker-/CMP-/Chatbot-Signaturen veralten und kommen neu dazu. PRs mit neuen
Signaturen oder aktualisierten Rechtsständen (mit Quelle) sind willkommen.

## Lizenz

MIT — frei nutzbar, kopierbar, anpassbar. Siehe [LICENSE](LICENSE).

---

*Gebaut von [Altovate GmbH](https://altovate.de). Kein Ersatz für anwaltliche Beratung.*
