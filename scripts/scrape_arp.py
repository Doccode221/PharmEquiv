"""Met à jour data/raw/medicaments_amm_senegal.csv depuis le site de l'ARP.

Usage :
    python scripts/scrape_arp.py                    # toutes les pages
    python scripts/scrape_arp.py --last-page 5      # test rapide
Puis : python scripts/build_dataset.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pharmequiv import config  # noqa: E402
from pharmequiv.data.scraper import scrape  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-page", type=int, default=1)
    parser.add_argument("--last-page", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--out", type=Path, default=config.RAW_CSV)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    df = scrape(args.first_page, args.last_page, args.delay)
    if df.empty:
        sys.exit("Aucune donnée récupérée : le CSV existant n'a pas été modifié.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"{len(df)} lignes écrites dans {args.out}")


if __name__ == "__main__":
    main()
