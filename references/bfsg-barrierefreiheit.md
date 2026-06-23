# Barrierefreiheit — BFSG

**Stand: Juni 2026.** Keine Rechtsberatung.

## Rechtsgrundlage & Inkrafttreten
Barrierefreiheitsstärkungsgesetz (BFSG), **in Kraft seit 28.06.2025**. Setzt den
European Accessibility Act um. Der am häufigsten übersehene Pflichtblock.

## Wer ist betroffen
B2C-Anbieter von „Dienstleistungen im elektronischen Geschäftsverkehr" — typischer­weise:
- Online-Shops
- Buchungs-/Termin-/Reservierungsstrecken
- SaaS/Apps mit Verbraucher-Zielgruppe
- alles mit Vertragsabschluss-Funktion gegenüber Endverbrauchern

**Nicht** erfasst (Faustregel): reine B2B-Angebote und reine Info-/Image-Websites
ohne Vertragsabschluss-Funktion.

## Kleinstunternehmen-Ausnahme
< 10 Beschäftigte **und** ≤ 2 Mio. € Jahresumsatz → ausgenommen — **aber nur bei
Dienstleistungen**. Wer **Produkte** über die Seite in Verkehr bringt, fällt trotzdem
darunter.

## Anforderungen
- Technischer Standard: **WCAG 2.1 AA / EN 301 549** — Kontraste, vollständige
  Tastaturbedienbarkeit, Alt-Texte, Screenreader-Tauglichkeit, klare Formular-Labels,
  Fokus-Sichtbarkeit, Sprach-Attribut
- **Barrierefreiheitserklärung** auf der Seite (Stand, bekannte Einschränkungen,
  Feedback-Mechanismus)

## Sanktion
Bußgeld **bis 100.000 €**, zusätzlich mögliche Untersagung des Angebots durch die
Marktüberwachungsbehörde.

## Einordnung (für die manuelle Bewertung)
1. Richtet sich das Angebot an Endverbraucher (B2C)? Wenn nein → meist raus.
2. Gibt es eine Vertrags-/Shop-/Buchungsfunktion? Wenn nein (reine Info-Seite) → meist raus.
3. Kleinstunternehmen + nur Dienstleistung → ausgenommen. Produkte → erfasst.
4. Im Zweifel: erfasst behandeln + Fachanwalt.

## Was die Engine prüft
**Baseline (statisch):** `lang`-Attribut, Bilder ohne `alt`, Überschriften-Hierarchie
(genau eine h1), Formularfelder ohne zugängliche Beschriftung, Links/Buttons ohne
erkennbaren Namen, fehlendes `<main>`-Landmark, Barrierefreiheitserklärung vorhanden.

**`--deep` (echter WCAG-Audit):** injiziert **axe-core** (dieselbe Engine, die
Lighthouse für seinen Accessibility-Score nutzt) in den gerenderten DOM und meldet
WCAG-2.1-Verstöße nach Schweregrad — u.a. Farbkontraste, ARIA-Korrektheit,
Label-Zuordnung, Rollen. Das ist die belastbare Tiefe für den BFSG-Teil.

**Bleibt manuell:** Fokus-Reihenfolge, Sinnzusammenhang von Alt-Texten, Tastatur-Fallen,
Inhalts-Logik — das kann kein automatischer Test abschließend beurteilen.

## Quellen
- BFSG-Gesetz: https://bfsg-gesetz.de/
- Neue Pflichten ab 28.06.2025: https://www.srd-rechtsanwaelte.de/blog/barrierefreiheitsstaerkungsgesetz-bfsg-neue-pflichten-fuer-unternehmen-ab-28-juni-2025
- eRecht24 BFSG: https://www.e-recht24.de/ecommerce/13236-barrierefreiheitsstaerkungsgesetz.html
