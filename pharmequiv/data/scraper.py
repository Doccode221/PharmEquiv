"""Collecte de la liste des médicaments autorisés sur le site de l'ARP Sénégal.

La page https://arp.sn/bases-de-donnees/medicaments-autorises est paginée
(`?page=N`) et contient un tableau HTML à 8 colonnes par page.
"""

from __future__ import annotations

import logging
import time
from io import StringIO

import pandas as pd
import requests

from pharmequiv import config

log = logging.getLogger(__name__)
HEADERS = {"User-Agent": "PharmEquiv/1.0 (+https://github.com/; usage de recherche)"}


def fetch_page(page: int, session: requests.Session, timeout: int = 20) -> pd.DataFrame | None:
    resp = session.get(config.ARP_URL, params={"page": page}, timeout=timeout)
    resp.raise_for_status()
    for table in pd.read_html(StringIO(resp.text)):
        if table.shape[1] == len(config.RAW_COLUMNS) and not table.empty:
            table.columns = config.RAW_COLUMNS
            return table
    return None


def scrape(first_page: int = 1, last_page: int | None = None, delay: float = 0.5,
           max_empty: int = 3) -> pd.DataFrame:
    """Parcourt les pages jusqu'à `last_page` ou jusqu'à `max_empty` pages vides d'affilée."""
    frames, empty_streak, page = [], 0, first_page
    with requests.Session() as session:
        session.headers.update(HEADERS)
        while last_page is None or page <= last_page:
            try:
                table = fetch_page(page, session)
            except requests.RequestException as exc:
                log.warning("Page %s : %s", page, exc)
                table = None
            if table is None:
                empty_streak += 1
                if empty_streak >= max_empty:
                    break
            else:
                empty_streak = 0
                frames.append(table)
                log.info("Page %s : %s lignes", page, len(table))
            page += 1
            time.sleep(delay)  # politesse envers le serveur de l'ARP
    if not frames:
        return pd.DataFrame(columns=config.RAW_COLUMNS)
    return pd.concat(frames, ignore_index=True).dropna(how="all")
