# Cookies & Consent — § 25 TDDDG + DSGVO

**Stand: Juni 2026.** Keine Rechtsberatung.

## Rechtsgrundlage
§ 25 TDDDG (seit Mai 2024 der neue Name des TTDSG) **plus** DSGVO. Beides muss
erfüllt sein: TDDDG für den Zugriff auf das Endgerät (Cookies/Speicher), DSGVO für
die anschließende Verarbeitung personenbezogener Daten.

## Kernregeln (hier scheitern die meisten Banner)
1. **Einwilligung VOR dem Laden.** Nicht-essenzielle Cookies/Tracking (Analytics,
   Meta-/TikTok-/LinkedIn-Pixel, Google Maps, eingebettete YouTube-Videos, Google
   Fonts via CDN, Hotjar/Clarity …) dürfen erst **nach aktiver Zustimmung** laden.
   Vorab-Laden = Verstoß.
2. **Technisch notwendige Cookies** brauchen keine Einwilligung (Session, Warenkorb,
   Speicherung der Consent-Entscheidung selbst).
3. **Ablehnen so leicht wie Zustimmen.** „Alle akzeptieren" und „Alle ablehnen"
   gleichwertig auf **erster Ebene** — gleiche Größe/Gewichtung. Ablehnen erst im
   Untermenü = verbotenes Dark Pattern.
4. Kein vorausgewähltes Häkchen, kein „Weiterscrollen = Zustimmung".
5. Granulare Auswahl nach Zweck/Kategorie.
6. Widerruf jederzeit, so einfach wie die Erteilung (z.B. „Cookie-Einstellungen"
   im Footer).

## Neu
- **EinwV (seit 01.04.2025):** gesetzliche Grundlage für PIMS (zentrale
  Consent-Verwaltung). Noch kein Praxiszwang, aber Richtung erkennbar → wartbares
  Consent-Management-Tool statt selbstgebautem Banner.

## Sanktion
DSGVO-Bußgelder bis 20 Mio. € / 4 % des weltweiten Jahresumsatzes; in der Praxis
Aufsichtsbehörden-Verfahren und Abmahnungen. Häufigster realer Auslöser:
Google Analytics / Meta Pixel ohne wirksame Einwilligung.

## Was die Engine prüft
- Bekannte Tracker im HTML/Code (GA4, GTM, Meta Pixel, Google Fonts CDN, YouTube,
  Maps, LinkedIn, TikTok, Hotjar, HubSpot, Clarity …)
- Bekanntes Consent-Tool (Usercentrics, Cookiebot, Borlabs, Complianz, OneTrust,
  Klaro, Real Cookie Banner, Iubenda …)
- Tracker **ohne** CMP → FAIL (lädt höchstwahrscheinlich ungefragt)
- **Deep-Modus (Playwright):** beweist, ob Tracker-Domains **vor** jeder
  Interaktion kontaktiert werden, und ob „Ablehnen" gleichwertig vorhanden ist

## Quellen
- TDDDG erklärt: https://cortina-consult.com/web-compliance/wissen/tdddg/
- Cookie-Banner rechtssicher 2026: https://dsgvo-vergleich.de/cookie-banner-rechtssicher-2026/
- Ablehnen-Button Pflicht: https://instinktdesign.de/dsgvo-cookie-banner-2025-ablehnen-button/
