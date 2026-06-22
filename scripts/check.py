#!/usr/bin/env python3
"""
website-recht-check — Compliance-Engine fuer deutsche Websites.

Prueft die rechtlichen Pflichten einer Website oder ihres Quellcodes:
  - Impressum / Anbieterkennzeichnung  (§ 5 DDG, frueher § 5 TMG)
  - Datenschutzerklaerung               (Art. 13 DSGVO)
  - Cookies / Consent                   (§ 25 TDDDG + DSGVO)
  - Barrierefreiheit                    (BFSG, seit 28.06.2025)
  - KI-Transparenz                      (EU AI Act, Art. 50, ab 02.08.2026)

Aufruf:
  python check.py https://example.de                 # Live-Check einer URL
  python check.py ./pfad/zum/quellcode               # Code-Check (Repo/Export)
  python check.py https://example.de --deep          # zusaetzlich Playwright-Laufzeit-Check
  python check.py https://example.de --json out.json # Ergebnis als JSON
  python check.py https://example.de --report r.md   # Report-Datei (Default: compliance-report.md)

Abhaengigkeiten:  pip install -r requirements.txt   (requests, beautifulsoup4)
Optional fuer --deep:  pip install playwright && playwright install chromium

Die Engine liefert deterministische Befunde. Die juristische Gesamtbewertung
(z.B. BFSG-Betroffenheit, Deepfake-Einstufung) trifft der aufrufende Claude-Skill
anhand der Dateien in references/. Kein Ersatz fuer anwaltliche Pruefung.
"""

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

# --- Severity-Stufen ---------------------------------------------------------
FAIL = "FAIL"      # klarer Verstoss / Pflicht nicht erfuellt
WARN = "WARN"      # wahrscheinliches Problem / veraltet / pruefen
PASS = "PASS"      # Pflicht erkennbar erfuellt
MANUAL = "MANUAL"  # nur durch Mensch/Claude entscheidbar
INFO = "INFO"      # Kontext / Hinweis

# --- Bekannte Tracker (laden ohne Einwilligung = i.d.R. unzulaessig) ---------
TRACKER_SIGNATURES = {
    "Google Analytics (GA4)": [r"googletagmanager\.com/gtag", r"gtag\(\s*['\"]config['\"]",
                               r"google-analytics\.com/g/collect"],
    "Google Tag Manager": [r"googletagmanager\.com/gtm", r"GTM-[A-Z0-9]{4,}"],
    "Universal Analytics (alt)": [r"google-analytics\.com/analytics\.js", r"UA-\d{4,}"],
    "Meta/Facebook Pixel": [r"connect\.facebook\.net", r"fbq\(", r"fbevents\.js"],
    "Google Fonts (CDN)": [r"fonts\.googleapis\.com", r"fonts\.gstatic\.com"],
    "YouTube (Tracking-Modus)": [r"youtube\.com/embed", r"youtube\.com/iframe_api"],
    "Google Maps": [r"maps\.googleapis\.com", r"maps\.google\.com/maps"],
    "LinkedIn Insight": [r"snap\.licdn\.com", r"_linkedin_partner_id"],
    "TikTok Pixel": [r"analytics\.tiktok\.com", r"ttq\."],
    "Hotjar": [r"static\.hotjar\.com", r"hotjar"],
    "HubSpot": [r"js\.hs-scripts\.com", r"js\.hsforms\.net"],
    "Microsoft Clarity": [r"clarity\.ms"],
}

# Tracker-Domains fuer den Netzwerk-Check im Deep-Modus
TRACKER_DOMAINS = [
    "google-analytics.com", "googletagmanager.com", "analytics.google.com",
    "connect.facebook.net", "facebook.com/tr", "fonts.googleapis.com",
    "fonts.gstatic.com", "youtube.com", "ytimg.com", "maps.googleapis.com",
    "snap.licdn.com", "analytics.tiktok.com", "hotjar.com", "hotjar.io",
    "hs-scripts.com", "hsforms.net", "clarity.ms", "doubleclick.net",
]

# --- Bekannte Consent-Management-Tools (CMP) ---------------------------------
CMP_SIGNATURES = {
    "Usercentrics": [r"usercentrics", r"uc\.js"],
    "Cookiebot": [r"cookiebot", r"consent\.cookiebot\.com"],
    "CookieFirst": [r"cookiefirst"],
    "Borlabs Cookie": [r"borlabs-cookie", r"BorlabsCookie"],
    "Complianz": [r"complianz", r"cmplz"],
    "OneTrust": [r"onetrust", r"otSDKStub"],
    "Klaro": [r"klaro"],
    "Cookie Consent (Osano)": [r"cookieconsent"],
    "Real Cookie Banner": [r"real-cookie-banner"],
    "Iubenda": [r"iubenda"],
}

# --- Bekannte Chatbot-Widgets (AI-Act-Transparenz pruefen) -------------------
CHATBOT_SIGNATURES = {
    "Intercom": [r"widget\.intercom\.io", r"intercomSettings"],
    "Drift": [r"js\.driftt\.com", r"drift\.load"],
    "Tidio": [r"code\.tidio\.co"],
    "Crisp": [r"client\.crisp\.chat"],
    "HubSpot Chat": [r"js\.hs-banner\.com"],
    "Zendesk/Zopim": [r"static\.zdassets\.com", r"zopim"],
    "Userlike": [r"userlike\.com"],
    "LiveChat": [r"cdn\.livechatinc\.com"],
}

CODE_EXTENSIONS = {".html", ".htm", ".jsx", ".tsx", ".ts", ".js", ".vue",
                   ".svelte", ".astro", ".php", ".ejs", ".hbs", ".liquid"}

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) website-recht-check/1.0 Safari/537.36")


class Report:
    """Sammelt Befunde und gibt sie strukturiert aus."""

    def __init__(self, target, mode):
        self.target = target
        self.mode = mode
        self.findings = []

    def add(self, category, severity, title, detail="", basis=""):
        self.findings.append({
            "category": category,
            "severity": severity,
            "title": title,
            "detail": detail,
            "basis": basis,
        })

    def counts(self):
        c = {FAIL: 0, WARN: 0, PASS: 0, MANUAL: 0, INFO: 0}
        for f in self.findings:
            c[f["severity"]] = c.get(f["severity"], 0) + 1
        return c

    def to_dict(self):
        return {"target": self.target, "mode": self.mode,
                "counts": self.counts(), "findings": self.findings}

    def to_markdown(self):
        icon = {FAIL: "❌", WARN: "⚠️", PASS: "✅", MANUAL: "🔍", INFO: "ℹ️"}
        c = self.counts()
        lines = [
            f"# Website-Recht-Check — Report",
            "",
            f"**Ziel:** `{self.target}`  ",
            f"**Modus:** {self.mode}  ",
            f"**Ergebnis:** {c[FAIL]}× FAIL · {c[WARN]}× WARN · {c[PASS]}× PASS · "
            f"{c[MANUAL]}× manuell · {c[INFO]}× Info",
            "",
            "> Deterministische Maschinen-Befunde. Keine Rechtsberatung. "
            "Einzelfall anwaltlich pruefen lassen.",
            "",
        ]
        order = [FAIL, WARN, MANUAL, PASS, INFO]
        cats = ["Impressum", "Datenschutz", "Cookies/Consent",
                "Barrierefreiheit (BFSG)", "KI-Transparenz (AI Act)"]
        for cat in cats:
            block = [f for f in self.findings if f["category"] == cat]
            if not block:
                continue
            lines.append(f"## {cat}")
            lines.append("")
            block.sort(key=lambda f: order.index(f["severity"]))
            for f in block:
                lines.append(f"- {icon[f['severity']]} **{f['severity']}** — {f['title']}")
                if f["detail"]:
                    lines.append(f"  - {f['detail']}")
                if f["basis"]:
                    lines.append(f"  - _Rechtsgrundlage: {f['basis']}_")
            lines.append("")
        return "\n".join(lines)


# =============================================================================
# Hilfsfunktionen
# =============================================================================
def fetch(url, timeout=15):
    """Laedt eine URL statisch (ohne JS), gibt (status, html, final_url) zurueck."""
    import requests
    r = requests.get(url, headers={"User-Agent": USER_AGENT},
                     timeout=timeout, allow_redirects=True)
    return r.status_code, r.text, str(r.url)


def render_html(url, timeout=25000):
    """Rendert eine Seite mit Playwright (fuehrt JS aus) und gibt das DOM zurueck.
    None, wenn Playwright fehlt oder das Rendern scheitert."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            # "load" statt "networkidle": networkidle feuert auf Seiten mit
            # offenen Verbindungen (HMR-Websocket, Chat, Polling) nie.
            page.goto(url, wait_until="load", timeout=timeout)
            page.wait_for_timeout(2000)  # SPA-Hydration abwarten
            # Bis zum Footer scrollen — viele SPAs rendern ihn erst beim Sichtbarwerden.
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1200)
            except Exception:
                pass
            html = page.content()
            browser.close()
            return html
    except Exception:
        return None


def get_page(url, deep, timeout=15):
    """Holt Seiten-HTML. Im Deep-Modus gerendert (mit Fallback auf statisch),
    sonst statisch. So sehen die Inhalts-Checks bei SPAs das echte DOM."""
    if deep:
        html = render_html(url)
        if html is not None:
            return 200, html, url
    return fetch(url, timeout=timeout)


def find_legal_links(soup, base_url):
    """Findet Impressum- und Datenschutz-Links: (href, sichtbarer Text)."""
    impressum, datenschutz = [], []
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True).lower()
        href = a["href"].lower()
        full = urljoin(base_url, a["href"])
        if "impressum" in text or "impressum" in href or "imprint" in href:
            impressum.append((full, a.get_text(" ", strip=True)))
        if ("datenschutz" in text or "datenschutz" in href
                or "privacy" in href or "privacy" in text):
            datenschutz.append((full, a.get_text(" ", strip=True)))
    return impressum, datenschutz


def detect_signatures(html, signatures):
    """Gibt die Liste der Tools/Tracker zurueck, deren Signatur im HTML matcht."""
    found = []
    for name, patterns in signatures.items():
        for p in patterns:
            if re.search(p, html, re.IGNORECASE):
                found.append(name)
                break
    return found


# =============================================================================
# LIVE-MODUS
# =============================================================================
def check_live(url, deep, report):
    from bs4 import BeautifulSoup

    try:
        status, html, final = get_page(url, deep)
    except Exception as e:
        report.add("Impressum", FAIL, "Seite nicht erreichbar",
                   f"Abruf von {url} fehlgeschlagen: {e}")
        return
    if status >= 400:
        report.add("Impressum", FAIL, f"HTTP {status} beim Abruf",
                   f"{url} liefert Status {status}.")
        return

    soup = BeautifulSoup(html, "html.parser")

    # --- 1. Impressum: Erreichbarkeit + Klick-Tiefe -------------------------
    impressum_links, datenschutz_links = find_legal_links(soup, final)
    if impressum_links:
        report.add("Impressum", PASS, "Impressum-Link auf Startseite (1 Klick)",
                   f"Linktext: \"{impressum_links[0][1]}\"",
                   "§ 5 DDG; Erreichbarkeit max. 2 Klicks (st. Rspr.)")
        _check_impressum_content(impressum_links[0][0], report, deep)
    else:
        # Tiefe 2: eine Ebene weiter suchen
        found = _bfs_for_link(final, soup, "impressum", report, deep)
        if found:
            report.add("Impressum", PASS, "Impressum erst auf 2. Ebene (2 Klicks)",
                       f"Gefunden unter: {found}",
                       "§ 5 DDG; gerade noch im 2-Klick-Rahmen")
            _check_impressum_content(found, report, deep)
        else:
            report.add("Impressum", FAIL, "Kein Impressum in 2 Klicks gefunden",
                       "Weder auf der Startseite noch eine Ebene tiefer wurde ein "
                       "klar benannter Impressum-Link gefunden.",
                       "§ 5 DDG; Ordnungswidrigkeit bis 50.000 € (§ 33 DDG)")

    # --- 2. Datenschutz: Erreichbarkeit -------------------------------------
    if datenschutz_links:
        url_dse, text_dse = datenschutz_links[0]
        report.add("Datenschutz", PASS, "Datenschutz-Link auf Startseite",
                   f"Linktext: \"{text_dse}\"", "Art. 13 DSGVO")
        if url_dse.lower().endswith(".pdf"):
            report.add("Datenschutz", FAIL, "Datenschutzerklaerung als PDF verlinkt",
                       "PDF ist nicht barrierefrei und gilt als 'versteckt'/abmahnbar. "
                       "Als normale HTML-Seite bereitstellen.",
                       "Art. 13 DSGVO i.V.m. Transparenzgebot; BFSG")
        else:
            _check_datenschutz_content(url_dse, report, deep)
    else:
        found = _bfs_for_link(final, soup, "datenschutz", report, deep)
        if found:
            report.add("Datenschutz", WARN, "Datenschutz erst auf 2. Ebene",
                       f"Gefunden unter: {found}. Sollte direkt im Footer stehen.",
                       "Art. 13 DSGVO")
            _check_datenschutz_content(found, report, deep)
        else:
            report.add("Datenschutz", FAIL, "Keine Datenschutzerklaerung gefunden",
                       "Kein klar benannter Datenschutz-Link in 2 Klicks. "
                       "Pflicht ohne Bagatellgrenze (schon wegen Server-Logs/IP).",
                       "Art. 13 DSGVO")

    # --- 3. Cookies / Tracking vs. Consent ----------------------------------
    trackers = detect_signatures(html, TRACKER_SIGNATURES)
    cmps = detect_signatures(html, CMP_SIGNATURES)
    if cmps:
        report.add("Cookies/Consent", INFO, f"Consent-Tool erkannt: {', '.join(cmps)}",
                   "Vorhandensein allein genuegt nicht — Konfiguration entscheidet "
                   "(Ablehnen gleichwertig? laedt erst nach Opt-in?).",
                   "§ 25 TDDDG")
    if trackers:
        if not cmps:
            report.add("Cookies/Consent", FAIL,
                       f"Tracker ohne erkennbares Consent-Tool: {', '.join(trackers)}",
                       "Diese Dienste benoetigen Einwilligung VOR dem Laden. "
                       "Ohne CMP werden sie hoechstwahrscheinlich ungefragt geladen.",
                       "§ 25 Abs. 1 TDDDG + Art. 6 DSGVO")
        else:
            report.add("Cookies/Consent", WARN,
                       f"Einwilligungspflichtige Dienste: {', '.join(trackers)}",
                       "Mit --deep pruefen, ob sie wirklich erst nach Opt-in laden.",
                       "§ 25 Abs. 1 TDDDG")
    else:
        report.add("Cookies/Consent", INFO, "Keine bekannten Tracker im HTML erkannt",
                   "Heuristik — eingebettete Dienste koennen dynamisch nachgeladen werden.")

    # --- 4. Barrierefreiheit (BFSG) — Heuristiken ---------------------------
    _check_a11y(soup, html, report)

    # --- 5. KI-Transparenz (AI Act) -----------------------------------------
    bots = detect_signatures(html, CHATBOT_SIGNATURES)
    if bots:
        report.add("KI-Transparenz (AI Act)", MANUAL,
                   f"Chat-Widget erkannt: {', '.join(bots)}",
                   "Falls KI-gestuetzt: ab 02.08.2026 muss der Nutzer bei der ersten "
                   "Interaktion klar erkennen, dass er mit einer KI spricht.",
                   "Art. 50 EU AI Act")
    report.add("KI-Transparenz (AI Act)", MANUAL,
               "KI-generierte Bilder/Texte manuell pruefen",
               "Foto-realistische KI-Bilder, die als echt durchgehen koennten, sowie "
               "KI-Texte zu oeffentlichem Interesse ohne menschliche Redaktion sind "
               "kennzeichnungspflichtig. Reines KI-als-Werkzeug ist es nicht.",
               "Art. 50 EU AI Act, ab 02.08.2026")

    # --- Deep-Modus: echtes Laufzeitverhalten -------------------------------
    if deep:
        _check_deep_runtime(final, report)


def _bfs_for_link(base_url, soup, keyword, report, deep=False, max_pages=12):
    """Sucht eine Ebene tiefer nach einem Link, der das Keyword enthaelt."""
    from bs4 import BeautifulSoup
    host = urlparse(base_url).netloc
    queue = deque()
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        if urlparse(full).netloc == host:
            queue.append(full)
    seen = set()
    limit = 8 if deep else max_pages  # Rendern ist teurer -> weniger Seiten
    while queue and len(seen) < limit:
        link = queue.popleft()
        if link in seen:
            continue
        seen.add(link)
        try:
            status, html, final = get_page(link, deep, timeout=10)
            if status >= 400:
                continue
            sub = BeautifulSoup(html, "html.parser")
            for a in sub.find_all("a", href=True):
                t = a.get_text(" ", strip=True).lower()
                h = a["href"].lower()
                if keyword in t or keyword in h:
                    return urljoin(final, a["href"])
        except Exception:
            continue
    return None


def _check_impressum_content(url, report, deep=False):
    """Prueft Pflichtangaben im Impressum (heuristisch am Textinhalt)."""
    try:
        status, html, _ = get_page(url, deep)
    except Exception:
        return
    text = re.sub(r"<[^>]+>", " ", html).lower()

    # Veralteter TMG-Verweis statt DDG
    if ("telemediengesetz" in text or "§ 5 tmg" in text or "5 tmg" in text
            or "tmg" in text) and "ddg" not in text:
        report.add("Impressum", WARN, "Veralteter Rechtsverweis (TMG statt DDG)",
                   "Das Impressum verweist auf das TMG. Seit 14.05.2024 gilt das DDG "
                   "(§ 5 DDG). Bezug aktualisieren.",
                   "§ 5 DDG")
    # E-Mail
    if "@" in text or "mailto:" in html.lower():
        report.add("Impressum", PASS, "E-Mail-Kontakt vorhanden", basis="§ 5 Abs. 1 Nr. 2 DDG")
    else:
        report.add("Impressum", WARN, "Keine E-Mail-Adresse erkennbar",
                   "Schnelle elektronische Kontaktaufnahme ist Pflicht.",
                   "§ 5 Abs. 1 Nr. 2 DDG")
    # Anschrift (PLZ-Muster)
    if re.search(r"\b\d{5}\b", text):
        report.add("Impressum", PASS, "Anschrift/PLZ erkennbar", basis="§ 5 Abs. 1 Nr. 1 DDG")
    else:
        report.add("Impressum", WARN, "Keine ladungsfaehige Anschrift erkennbar",
                   "Postfach genuegt nicht — vollstaendige Anschrift noetig.",
                   "§ 5 Abs. 1 Nr. 1 DDG")
    # Juristische Person: Vertretung + HR
    if re.search(r"gmbh|ug |ag |ohg|kg |e\.v\.|gbr", text):
        if "vertret" in text or "geschäftsführ" in text or "geschaeftsführ" in text:
            report.add("Impressum", PASS, "Vertretungsberechtigte genannt",
                       basis="§ 5 Abs. 1 Nr. 1 DDG")
        else:
            report.add("Impressum", WARN, "Vertretungsberechtigte(r) nicht erkennbar",
                       "Bei juristischen Personen Pflicht (z.B. Geschaeftsfuehrer).",
                       "§ 5 Abs. 1 Nr. 1 DDG")
        if "handelsregister" in text or re.search(r"hrb\s*\d+", text):
            report.add("Impressum", PASS, "Handelsregister-Angabe vorhanden",
                       basis="§ 5 Abs. 1 Nr. 4 DDG")
        else:
            report.add("Impressum", WARN, "Keine Handelsregister-Angabe erkennbar",
                       "Register + Registernummer angeben.", "§ 5 Abs. 1 Nr. 4 DDG")
    # USt-IdNr.
    if re.search(r"de\s?\d{9}", text) or "umsatzsteuer" in text or "ust-id" in text:
        report.add("Impressum", PASS, "USt-IdNr. erkennbar", basis="§ 5 Abs. 1 Nr. 6 DDG")
    # OS-Plattform-Link (seit 20.07.2025 abgeschaltet)
    if "ec.europa.eu/consumers/odr" in html.lower():
        report.add("Impressum", WARN, "Veralteter OS-Plattform-Link",
                   "Die EU-OS-Plattform wurde zum 20.07.2025 abgeschaltet. Link entfernen.",
                   "Art. 14 ODR-VO (aufgehoben)")


def _check_datenschutz_content(url, report, deep=False):
    """Prueft Vollstaendigkeit der Datenschutzerklaerung (heuristisch)."""
    try:
        status, html, _ = get_page(url, deep)
    except Exception:
        return
    text = re.sub(r"<[^>]+>", " ", html).lower()
    pflicht = {
        "Verantwortlicher": ["verantwortlich"],
        "Rechtsgrundlage": ["rechtsgrundlage", "art. 6", "artikel 6"],
        "Betroffenenrechte": ["auskunft", "loeschung", "löschung", "betroffenenrecht"],
        "Aufsichtsbehoerde / Beschwerderecht": ["aufsichtsbehörde", "aufsichtsbehoerde", "beschwerde"],
        "Speicherdauer": ["speicherdauer", "speicherfrist", "aufbewahr"],
    }
    fehlend = [k for k, kws in pflicht.items() if not any(kw in text for kw in kws)]
    if not fehlend:
        report.add("Datenschutz", PASS, "Kern-Pflichtangaben vorhanden",
                   "Verantwortlicher, Rechtsgrundlage, Betroffenenrechte, "
                   "Aufsichtsbehoerde und Speicherdauer erkannt.",
                   "Art. 13 DSGVO")
    else:
        report.add("Datenschutz", WARN, "Moegliche Luecken in der Datenschutzerklaerung",
                   "Nicht erkannt: " + ", ".join(fehlend) +
                   ". Heuristik — manuell gegenpruefen.",
                   "Art. 13 DSGVO")
    if len(text) < 1500:
        report.add("Datenschutz", WARN, "Datenschutzerklaerung wirkt sehr kurz",
                   "Sehr wenig Text — vermutlich unvollstaendig.",
                   "Art. 13 DSGVO")


def _check_a11y(soup, html, report):
    """Leichtgewichtige BFSG/WCAG-Heuristiken (kein vollwertiger A11y-Audit)."""
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        report.add("Barrierefreiheit (BFSG)", PASS,
                   f"Sprach-Attribut gesetzt (lang=\"{html_tag.get('lang')}\")",
                   basis="WCAG 2.1 / EN 301 549")
    else:
        report.add("Barrierefreiheit (BFSG)", WARN, "Kein lang-Attribut am <html>",
                   "Screenreader brauchen die Sprachangabe.", "WCAG 2.1 (3.1.1)")
    imgs = soup.find_all("img")
    missing_alt = [i for i in imgs if not i.get("alt") and i.get("alt") != ""]
    if imgs:
        if missing_alt:
            report.add("Barrierefreiheit (BFSG)", WARN,
                       f"{len(missing_alt)} von {len(imgs)} Bildern ohne alt-Attribut",
                       "Informative Bilder brauchen Alt-Text (dekorative: alt=\"\").",
                       "WCAG 2.1 (1.1.1)")
        else:
            report.add("Barrierefreiheit (BFSG)", PASS, "Alle Bilder mit alt-Attribut",
                       basis="WCAG 2.1 (1.1.1)")
    if "barrierefreiheit" in html.lower() or "barrierefreiheitserkl" in html.lower():
        report.add("Barrierefreiheit (BFSG)", PASS, "Hinweis auf Barrierefreiheitserklaerung",
                   basis="§ 14 BFSG")
    else:
        report.add("Barrierefreiheit (BFSG)", MANUAL, "Keine Barrierefreiheitserklaerung erkannt",
                   "Falls BFSG-pflichtig (B2C-Shop/Buchung, kein Kleinstunternehmen), "
                   "ist eine Erklaerung Pflicht. Betroffenheit manuell klaeren.",
                   "BFSG, seit 28.06.2025")


def _check_deep_runtime(url, report):
    """Echtes Laden via Playwright: Tracking VOR Einwilligung + Banner-Symmetrie."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        report.add("Cookies/Consent", INFO, "Deep-Modus uebersprungen",
                   "Playwright nicht installiert. "
                   "pip install playwright && playwright install chromium")
        return

    pre_consent_trackers = set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.on("request", lambda req: [
                pre_consent_trackers.add(d) for d in TRACKER_DOMAINS if d in req.url
            ])
            page.goto(url, wait_until="load", timeout=25000)
            page.wait_for_timeout(3500)  # warten, bevor irgendetwas geklickt wird
            body = page.content().lower()
            browser.close()
    except Exception as e:
        report.add("Cookies/Consent", INFO, "Deep-Check nicht abgeschlossen", str(e))
        return

    if pre_consent_trackers:
        report.add("Cookies/Consent", FAIL,
                   "Tracking-Anfragen VOR jeder Einwilligung",
                   "Diese Tracker-Domains wurden ohne Opt-in kontaktiert: "
                   + ", ".join(sorted(pre_consent_trackers)) +
                   ". Klarer § 25 TDDDG-Verstoss.",
                   "§ 25 Abs. 1 TDDDG")
    else:
        report.add("Cookies/Consent", PASS,
                   "Keine Tracker-Anfragen vor Einwilligung erkannt",
                   "Im Deep-Check wurde vor Interaktion keine bekannte Tracker-Domain "
                   "kontaktiert.", "§ 25 Abs. 1 TDDDG")

    has_accept = bool(re.search(r"akzeptieren|annehmen|zustimmen|alle erlauben", body))
    has_reject = bool(re.search(r"ablehnen|alle ablehnen|verweigern|nur notwendige", body))
    if has_accept and not has_reject:
        report.add("Cookies/Consent", FAIL,
                   "Akzeptieren ohne gleichwertiges Ablehnen (Dark Pattern)",
                   "Ein 'Akzeptieren'-Button ohne ebenbuertiges 'Ablehnen' auf erster "
                   "Ebene ist unzulaessig.",
                   "§ 25 TDDDG; EDSA-Leitlinien zu Dark Patterns")
    elif has_accept and has_reject:
        report.add("Cookies/Consent", PASS,
                   "Akzeptieren UND Ablehnen auf erster Ebene erkennbar",
                   basis="§ 25 TDDDG")


# =============================================================================
# CODE-MODUS
# =============================================================================
def check_code(root, report):
    root = Path(root)
    files = [p for p in root.rglob("*")
             if p.suffix.lower() in CODE_EXTENSIONS
             and "node_modules" not in p.parts and ".git" not in p.parts]
    if not files:
        report.add("Impressum", WARN, "Keine pruefbaren Quelldateien gefunden",
                   f"Unter {root} keine HTML/JS/TS/Framework-Dateien gefunden.")
        return

    blob = ""
    for f in files[:4000]:
        try:
            blob += f.read_text(encoding="utf-8", errors="ignore").lower() + "\n"
        except Exception:
            continue

    # Impressum / Datenschutz als Route/Link vorhanden?
    if re.search(r"impressum|/imprint", blob):
        report.add("Impressum", PASS, "Impressum-Route/Link im Code vorhanden",
                   "Laufzeit-Erreichbarkeit (Klick-Tiefe) zusaetzlich live pruefen.",
                   "§ 5 DDG")
    else:
        report.add("Impressum", FAIL, "Kein Impressum im Code gefunden",
                   "Weder Route noch Link auf ein Impressum erkennbar.", "§ 5 DDG")
    if re.search(r"datenschutz|/privacy", blob):
        report.add("Datenschutz", PASS, "Datenschutz-Route/Link im Code vorhanden",
                   basis="Art. 13 DSGVO")
    else:
        report.add("Datenschutz", FAIL, "Keine Datenschutz-Seite im Code gefunden",
                   "", "Art. 13 DSGVO")

    if ("telemediengesetz" in blob or "§ 5 tmg" in blob) and "ddg" not in blob:
        report.add("Impressum", WARN, "Veralteter TMG-Verweis im Code",
                   "Auf § 5 DDG aktualisieren (seit 14.05.2024).", "§ 5 DDG")

    trackers = detect_signatures(blob, TRACKER_SIGNATURES)
    cmps = detect_signatures(blob, CMP_SIGNATURES)
    if trackers and not cmps:
        report.add("Cookies/Consent", FAIL,
                   f"Tracker im Code ohne Consent-Tool: {', '.join(trackers)}",
                   "Einbindung so, dass erst nach Opt-in geladen wird — sonst § 25 TDDDG-Verstoss.",
                   "§ 25 Abs. 1 TDDDG")
    elif trackers:
        report.add("Cookies/Consent", WARN,
                   f"Tracker + CMP im Code ({', '.join(trackers)} / {', '.join(cmps)})",
                   "Sicherstellen, dass der Consent-Gate die Tracker wirklich blockt.",
                   "§ 25 TDDDG")
    elif cmps:
        report.add("Cookies/Consent", INFO, f"Consent-Tool im Code: {', '.join(cmps)}")

    bots = detect_signatures(blob, CHATBOT_SIGNATURES)
    if bots:
        report.add("KI-Transparenz (AI Act)", MANUAL,
                   f"Chat-Widget im Code: {', '.join(bots)}",
                   "Falls KI-gestuetzt: Kennzeichnung bei erster Interaktion noetig.",
                   "Art. 50 EU AI Act")

    # A11y-Heuristik: alt-Attribute in img/Image-Tags
    img_tags = len(re.findall(r"<img|<image|<Image", blob))
    alt_tags = len(re.findall(r"alt\s*=", blob))
    if img_tags and alt_tags < img_tags:
        report.add("Barrierefreiheit (BFSG)", WARN,
                   f"Vermutlich Bilder ohne alt-Attribut (~{img_tags} img / {alt_tags} alt)",
                   "Heuristik ueber alle Dateien — live gegenpruefen.",
                   "WCAG 2.1 (1.1.1)")
    report.add("Barrierefreiheit (BFSG)", MANUAL,
               "BFSG-Betroffenheit + A11y nur live final beurteilbar",
               "Kontraste, Fokus, Screenreader-Verhalten brauchen das gerenderte Ergebnis.",
               "BFSG")


# =============================================================================
# CLI
# =============================================================================
def main():
    ap = argparse.ArgumentParser(description="Compliance-Check fuer deutsche Websites")
    ap.add_argument("target", help="URL (https://...) oder Pfad zum Quellcode")
    ap.add_argument("--deep", action="store_true",
                    help="Playwright-Laufzeit-Check (Tracking vor Consent, Banner-Symmetrie)")
    ap.add_argument("--json", metavar="DATEI", help="Ergebnis als JSON speichern")
    ap.add_argument("--report", metavar="DATEI", default="compliance-report.md",
                    help="Markdown-Report (Default: compliance-report.md)")
    ap.add_argument("--quiet", action="store_true", help="Keine Konsolenausgabe")
    args = ap.parse_args()

    is_url = args.target.startswith("http://") or args.target.startswith("https://")
    mode = "Live-URL" + (" + Deep (Playwright)" if args.deep and is_url else "") \
        if is_url else "Code/Repo"
    report = Report(args.target, mode)

    if is_url:
        check_live(args.target, args.deep, report)
    else:
        if not Path(args.target).exists():
            print(f"Pfad nicht gefunden: {args.target}", file=sys.stderr)
            sys.exit(2)
        check_code(args.target, report)

    md = report.to_markdown()
    Path(args.report).write_text(md, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(report.to_dict(), ensure_ascii=False,
                                               indent=2), encoding="utf-8")
    if not args.quiet:
        print(md)
        print(f"\n→ Report gespeichert: {args.report}")
        if args.json:
            print(f"→ JSON gespeichert: {args.json}")

    # Exit-Code: 1 bei mindestens einem FAIL (fuer CI-Nutzung)
    sys.exit(1 if report.counts()[FAIL] > 0 else 0)


if __name__ == "__main__":
    main()
