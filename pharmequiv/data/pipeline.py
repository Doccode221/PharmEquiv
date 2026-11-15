"""Pipeline de préparation : CSV brut de l'ARP -> table propre et enrichie.

Étapes :
1. Renommage des colonnes, nettoyage des valeurs d'affichage.
2. Suppression des lignes sans DCI et des doublons exacts.
3. Découpage des DCI en molécules + correction automatique des fautes de frappe
   (ex. 'AMOXCILLINE' -> 'amoxicilline', 'LAMIVIDUNE' -> 'lamivudine').
4. Clés de comparaison : dci_key, dosage_key, forme_famille, voie_norm.
5. Inférence de la classe thérapeutique manquante à partir des autres
   spécialités partageant la même DCI.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

from pharmequiv import config
from pharmequiv.data import normalize as nz

OUTPUT_COLUMNS = [
    "id", "nom", "dci", "dosage", "presentation", "forme", "voie", "laboratoire",
    "classe", "classe_famille", "classe_inferee", "molecules", "n_molecules", "dci_key",
    "dosage_key", "forme_famille", "voie_norm", "groupe_id",
]


def load_raw(path: Path | str = config.RAW_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = set(config.RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans {path}: {sorted(missing)}")
    return df[config.RAW_COLUMNS].rename(columns=config.COLUMN_MAP)


# Paires de mots proches à l'écrit mais désignant des substances DIFFÉRENTES :
# ne jamais les fusionner.
DISTINCT_WORDS = {
    frozenset(p) for p in [
        ("folinique", "folique"), ("ampicilline", "amoxicilline"),
        ("betametasone", "beclometasone"), ("betamethasone", "beclometasone"),
        ("ethyle", "methyle"), ("cefixime", "cefuroxime"),
        ("prednisone", "prednisolone"), ("hydroxyzine", "hydralazine"),
    ]
}
_STOPWORDS = {"de", "d", "du", "des", "la", "le"}


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[\s’'\-]+", text) if w and w not in _STOPWORDS]


def is_safe_typo(wrong: str, right: str) -> bool:
    """Garde-fous médicaux avant de considérer `wrong` comme une faute de `right`."""
    if re.sub(r"\D", "", wrong) != re.sub(r"\D", "", right):
        return False  # vitamine b2 ≠ vitamine d2, carbomer 934 ≠ 940
    w1, w2 = _words(wrong), _words(right)
    if len(w1) != len(w2):
        return False
    for a, b in zip(w1, w2):
        if a == b:
            continue
        if frozenset((a, b)) in DISTINCT_WORDS:
            return False
        # 'levocetirizine' vs 'cetirizine', 'dexketoprofene' vs 'ketoprofene' :
        # un préfixe ajouté change la molécule (énantiomère, dérivé...)
        if a.endswith(b) or b.endswith(a):
            return False
        if fuzz.ratio(a, b) < config.TYPO_MIN_SIMILARITY - 5:
            return False
    return True


def build_typo_map(molecule_lists: pd.Series) -> dict[str, str]:
    """Associe chaque molécule rare à une molécule fréquente très proche.

    Une molécule vue <= TYPO_MAX_RARE_COUNT fois est comparée aux molécules au
    moins 3x plus fréquentes ; si la similarité dépasse TYPO_MIN_SIMILARITY et
    que la première lettre est identique, on la considère comme une faute.
    """
    counts = Counter(m for mols in molecule_lists for m in mols)
    frequent = [m for m, c in counts.items() if c > config.TYPO_MAX_RARE_COUNT]
    mapping: dict[str, str] = {}
    for mol, count in counts.items():
        if count > config.TYPO_MAX_RARE_COUNT or len(mol) < 6:
            continue
        candidates = [f for f in frequent if f[0] == mol[0] and counts[f] >= 3 * count]
        if not candidates:
            continue
        matches = process.extract(mol, candidates, scorer=fuzz.ratio,
                                  score_cutoff=config.TYPO_MIN_SIMILARITY, limit=3)
        for target, _score, _ in matches:
            if is_safe_typo(mol, target):
                mapping[mol] = target
                break
    return mapping


def _infer_classes(df: pd.DataFrame) -> pd.DataFrame:
    known = df[df["classe"] != ""]
    mode_by_dci = known.groupby("dci_key")["classe"].agg(lambda s: s.value_counts().index[0])
    missing = df["classe"] == ""
    inferred = df.loc[missing, "dci_key"].map(mode_by_dci)
    df["classe_inferee"] = missing & inferred.notna().reindex(df.index, fill_value=False)
    df.loc[missing, "classe"] = inferred.fillna("")
    df["classe"] = df["classe"].replace("", "Non renseignée")
    return df


def build_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    df = raw.copy()
    for col in df.columns:
        df[col] = df[col].map(nz.clean_display)

    df = df[df["dci"].notna() & df["nom"].notna()].drop_duplicates().reset_index(drop=True)

    def _canon(m: str) -> str:
        m = nz.CURATED_FIXES.get(m, m)
        return nz.CURATED_FIXES.get(nz.active_moiety(m), nz.active_moiety(m))

    mols = df["dci"].map(lambda d: sorted({_canon(m) for m in nz.split_molecules(d)}))
    typo_map = build_typo_map(mols)

    def _fix(m: str) -> str:
        seen = set()
        while m in typo_map and m not in seen:  # corrections transitives
            seen.add(m)
            m = typo_map[m]
        return nz.CURATED_FIXES.get(m, m)

    mols = mols.map(lambda ms: sorted({_fix(m) for m in ms}))
    df = df[mols.map(len) > 0].copy()
    mols = mols[df.index]

    df["molecules"] = mols.map(" | ".join)
    df["n_molecules"] = mols.map(len)
    df["dci_key"] = mols.map(nz.dci_key)
    df["dosage_key"] = df["dosage"].map(nz.dosage_key)
    df["forme_famille"] = [nz.forme_famille(f, n) for f, n in zip(df["forme"], df["nom"])]
    df["voie_norm"] = df["voie"].map(nz.voie_norm)
    df["classe"] = df["classe"].map(nz.classe_norm)
    df = _infer_classes(df)
    df["classe_famille"] = df["classe"].map(nz.classe_famille).replace("", "Non renseignée")

    for col in ["dosage", "presentation", "forme", "voie", "laboratoire"]:
        df[col] = df[col].fillna("—")

    # Groupe d'équivalence stricte = même DCI + même dosage + même forme
    df["groupe_id"] = df.groupby(["dci_key", "dosage_key", "forme_famille"], sort=False).ngroup()
    df = df.sort_values(["dci_key", "nom"]).reset_index(drop=True)
    df["id"] = df.index
    return df[OUTPUT_COLUMNS], typo_map


def load_processed(path: Path | str = config.PROCESSED_CSV) -> pd.DataFrame:
    """Charge la table propre ; la reconstruit depuis le brut si absente."""
    path = Path(path)
    if path.exists():
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        for col in ["id", "n_molecules", "groupe_id"]:
            df[col] = df[col].astype(int)
        df["classe_inferee"] = df["classe_inferee"].map({"True": True, "False": False})
        return df
    df, _ = build_dataset(load_raw())
    return df
