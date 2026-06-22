# Website-Recht-Check — Report (Beispiel)

**Ziel:** `https://example.de`  
**Modus:** Live-URL + Deep (Playwright)  
**Ergebnis:** 2× FAIL · 2× WARN · 5× PASS · 2× manuell · 1× Info

> Deterministische Maschinen-Befunde. Keine Rechtsberatung. Einzelfall anwaltlich pruefen lassen.

## Impressum

- ⚠️ **WARN** — Veralteter Rechtsverweis (TMG statt DDG)
  - Das Impressum verweist auf das TMG. Seit 14.05.2024 gilt das DDG (§ 5 DDG). Bezug aktualisieren.
  - _Rechtsgrundlage: § 5 DDG_
- ✅ **PASS** — Impressum-Link auf Startseite (1 Klick)
  - Linktext: "Impressum"
  - _Rechtsgrundlage: § 5 DDG; Erreichbarkeit max. 2 Klicks (st. Rspr.)_
- ✅ **PASS** — E-Mail-Kontakt vorhanden
  - _Rechtsgrundlage: § 5 Abs. 1 Nr. 2 DDG_
- ✅ **PASS** — Anschrift/PLZ erkennbar
  - _Rechtsgrundlage: § 5 Abs. 1 Nr. 1 DDG_
- ✅ **PASS** — Vertretungsberechtigte genannt
  - _Rechtsgrundlage: § 5 Abs. 1 Nr. 1 DDG_

## Datenschutz

- ✅ **PASS** — Datenschutz-Link auf Startseite
  - Linktext: "Datenschutzerklärung"
  - _Rechtsgrundlage: Art. 13 DSGVO_
- ✅ **PASS** — Kern-Pflichtangaben vorhanden
  - Verantwortlicher, Rechtsgrundlage, Betroffenenrechte, Aufsichtsbehoerde und Speicherdauer erkannt.
  - _Rechtsgrundlage: Art. 13 DSGVO_

## Cookies/Consent

- ❌ **FAIL** — Tracking-Anfragen VOR jeder Einwilligung
  - Diese Tracker-Domains wurden ohne Opt-in kontaktiert: google-analytics.com, fonts.googleapis.com. Klarer § 25 TDDDG-Verstoss.
  - _Rechtsgrundlage: § 25 Abs. 1 TDDDG_
- ❌ **FAIL** — Akzeptieren ohne gleichwertiges Ablehnen (Dark Pattern)
  - Ein 'Akzeptieren'-Button ohne ebenbuertiges 'Ablehnen' auf erster Ebene ist unzulaessig.
  - _Rechtsgrundlage: § 25 TDDDG; EDSA-Leitlinien zu Dark Patterns_
- ℹ️ **INFO** — Consent-Tool erkannt: Cookiebot
  - Vorhandensein allein genuegt nicht — Konfiguration entscheidet.
  - _Rechtsgrundlage: § 25 TDDDG_

## Barrierefreiheit (BFSG)

- ⚠️ **WARN** — 4 von 12 Bildern ohne alt-Attribut
  - Informative Bilder brauchen Alt-Text (dekorative: alt="").
  - _Rechtsgrundlage: WCAG 2.1 (1.1.1)_
- ✅ **PASS** — Sprach-Attribut gesetzt (lang="de")
  - _Rechtsgrundlage: WCAG 2.1 / EN 301 549_

## KI-Transparenz (AI Act)

- 🔍 **MANUAL** — Chat-Widget erkannt: Intercom
  - Falls KI-gestuetzt: ab 02.08.2026 muss der Nutzer bei der ersten Interaktion klar erkennen, dass er mit einer KI spricht.
  - _Rechtsgrundlage: Art. 50 EU AI Act_
- 🔍 **MANUAL** — KI-generierte Bilder/Texte manuell pruefen
  - Foto-realistische KI-Bilder, die als echt durchgehen koennten, sind kennzeichnungspflichtig. Reines KI-als-Werkzeug ist es nicht.
  - _Rechtsgrundlage: Art. 50 EU AI Act, ab 02.08.2026_
