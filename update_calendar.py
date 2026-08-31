
import re
import hashlib
from datetime import datetime, date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event


BASE_URL = "https://www.preparaulm.com"
EVENTS_URL = (
    "https://www.preparaulm.com/eventos-aeronauticos"
    "?ambito=nacional&tiempo=todos"
)

OUTPUT_FILE = "docs/aviacion.ics"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AviationCalendar/1.0; "
        "+https://github.com/)"
    )
}


def parse_date_range(text):
    """
    Convierte textos como:

        4 - 6 septiembre de 2026
        6 septiembre de 2026
        13 - 19 septiembre de 2026

    en (fecha_inicio, fecha_fin).
    """

    months = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    pattern = re.compile(
        r"(\d{1,2})"
        r"(?:\s*-\s*(\d{1,2}))?"
        r"\s+([a-záéíóú]+)"
        r"\s+de\s+(\d{4})",
        re.IGNORECASE,
    )

    match = pattern.search(text)

    if not match:
        return None, None

    start_day = int(match.group(1))
    end_day = int(match.group(2) or start_day)

    month_name = match.group(3).lower()
    year = int(match.group(4))

    if month_name not in months:
        return None, None

    month = months[month_name]

    try:
        start = date(year, month, start_day)
        end = date(year, month, end_day)

        return start, end

    except ValueError:
        return None, None


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def event_uid(title, start):
    """
    Genera un UID estable.
    Si PreparaULM cambia la descripción del evento,
    seguirá siendo el mismo evento para Apple Calendar.
    """

    raw = f"{title}|{start.isoformat()}"

    digest = hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:20]

    return f"{digest}@aviacion-espana-calendar"


def extract_events(html):
    soup = BeautifulSoup(html, "html.parser")

    events = []

    # Buscamos enlaces que apunten a eventos individuales.
    links = soup.find_all("a", href=True)

    seen = set()

    for link in links:

        href = link.get("href", "")

        if "/eventos-aeronauticos/" not in href:
            continue

        if href in seen:
            continue

        seen.add(href)

        url = urljoin(BASE_URL, href)

        container = link

        # Subimos unos niveles buscando el bloque completo
        # del evento.
        for _ in range(5):
            if container.parent:
                container = container.parent

        text = clean_text(container.get_text(" ", strip=True))

        start, end = parse_date_range(text)

        if not start:
            continue

        # El enlace suele contener el título.
        title = clean_text(link.get_text(" ", strip=True))

        if not title:
            continue

        # Evitamos basura que no sean eventos reales.
        if len(title) < 5:
            continue

        # Intentamos eliminar la fecha del título si se ha
        # incluido accidentalmente.
        title = re.sub(
            r"^\d{1,2}(?:\s*-\s*\d{1,2})?\s+"
            r"[a-záéíóú]+\s+de\s+\d{4}\s*",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip()

        events.append(
            {
                "title": title,
                "start": start,
                "end": end,
                "description": text,
                "url": url,
                "location": "",
            }
        )

    return events


def create_calendar(events):

    from datetime import timedelta
    from zoneinfo import ZoneInfo

    cal = Calendar()

    cal.add("prodid", "-//Aviacion España Calendar//PreparaULM//ES")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")

    cal.add(
        "x-wr-calname",
        "Eventos de Aviación en España"
    )

    cal.add(
        "x-wr-timezone",
        "Europe/Madrid"
    )

    # Fecha actual en España
    today = datetime.now(
        ZoneInfo("Europe/Madrid")
    ).date()

    print(f"Fecha actual: {today}")
    print(f"Eventos extraídos: {len(events)}")

    # Eventos futuros
    future_events = [
        e for e in events
        if e["end"] >= today
    ]

    print(
        f"Eventos futuros: {len(future_events)}"
    )

    # Eliminar duplicados
    unique = {}

    for event in future_events:

        key = (
            event["title"],
            event["start"],
            event["url"],
        )

        unique[key] = event

    future_events = list(unique.values())

    # Orden cronológico
    future_events.sort(
        key=lambda x: (
            x["start"],
            x["title"]
        )
    )

    for data in future_events:

        event = Event()

        event.add(
            "uid",
            event_uid(
                data["title"],
                data["start"],
            ),
        )

        event.add(
            "dtstamp",
            datetime.utcnow(),
        )

        event.add(
            "dtstart",
            data["start"],
        )

        # DTEND es exclusivo en ICS
        event.add(
            "dtend",
            data["end"] + timedelta(days=1),
        )

        event.add(
            "summary",
            data["title"],
        )

        event.add(
            "description",
            (
                "Evento obtenido de PreparaULM.\n\n"
                + data["description"]
                + "\n\nFuente: "
                + data["url"]
            ),
        )

        if data["location"]:
            event.add(
                "location",
                data["location"],
            )

        event.add(
            "url",
            data["url"],
        )

        cal.add_component(event)

    return cal


def main():

    print("Descargando eventos de PreparaULM...")

    response = requests.get(
        EVENTS_URL,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    print(
        f"HTTP {response.status_code} "
        f"({len(response.text)} caracteres)"
    )

    events = extract_events(response.text)

    print(
        f"Eventos encontrados: {len(events)}"
    )

    calendar = create_calendar(events)

    with open(
        OUTPUT_FILE,
        "wb",
    ) as f:
        f.write(calendar.to_ical())

    print(
        f"Calendario generado: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
