"""Construit data/processed/medicaments_clean.csv à partir du CSV brut.

Usage :
    python scripts/build_dataset.py            # chemins par défaut
    python scripts/build_dataset.py --raw autre.csv --show-typos
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pharmequiv import config  # noqa: E402
from pharmequiv.data.pipeline import build_dataset, load_raw  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=config.RAW_CSV)
    parser.add_argument("--out", type=Path, default=config.PROCESSED_CSV)
    parser.add_argument("--show-typos", action="store_true",
                        help="Affiche les corrections de DCI appliquées")
    args = parser.parse_args()

    raw = load_raw(args.raw)
    df, typo_map = build_dataset(raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    print(f"Lignes brutes        : {len(raw)}")
    print(f"Lignes conservées    : {len(df)}")
    print(f"DCI distinctes       : {df['dci_key'].nunique()}")
    print(f"Groupes d'équivalence: {df['groupe_id'].nunique()}")
    print(f"Classes inférées     : {int(df['classe_inferee'].sum())}")
    print(f"Fautes corrigées     : {len(typo_map)}")
    if args.show_typos:
        for wrong, right in sorted(typo_map.items()):
            print(f"  {wrong:35s} -> {right}")
    print(f"Écrit dans {args.out}")


if __name__ == "__main__":
    main()
