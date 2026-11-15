"""Moteur de recherche et d'équivalence.

Deux briques indépendantes de Streamlit (testables seules) :

* **Recherche floue** : TF-IDF sur n-grammes de caractères (insensible aux
  fautes, accents, majuscules) appliqué au nom commercial ET à la DCI.
* **Équivalence** : à partir d'un médicament de référence, classe les autres
  spécialités en trois niveaux.

    ┌────────────────────┬──────────────────────────────────────────────┐
    │ Niveau             │ Règle                                        │
    ├────────────────────┼──────────────────────────────────────────────┤
    │ 1. Générique strict│ même DCI + même dosage + même forme          │
    │ 2. Même molécule   │ même DCI, dosage ou forme différents         │
    │ 3. Alternative     │ même famille de classe + même voie,          │
    │    thérapeutique   │ DCI différente                               │
    └────────────────────┴──────────────────────────────────────────────┘
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from pharmequiv import config
from pharmequiv.data.normalize import normalize_text

UNKNOWN_CLASS = "Non renseignée"


@dataclass
class SearchFilters:
    classes: list[str] = field(default_factory=list)
    formes: list[str] = field(default_factory=list)
    voies: list[str] = field(default_factory=list)
    laboratoires: list[str] = field(default_factory=list)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = pd.Series(True, index=df.index)
        if self.classes:
            mask &= df["classe_famille"].isin(self.classes)
        if self.formes:
            mask &= df["forme_famille"].isin(self.formes)
        if self.voies:
            mask &= df["voie_norm"].isin(self.voies)
        if self.laboratoires:
            mask &= df["laboratoire"].isin(self.laboratoires)
        return df[mask]


@dataclass
class Equivalents:
    reference: pd.Series
    strict: pd.DataFrame
    same_molecule: pd.DataFrame
    therapeutic: pd.DataFrame  # une ligne par DCI alternative

    @property
    def total(self) -> int:
        return len(self.strict) + len(self.same_molecule)


class EquivalenceEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.reset_index(drop=True)
        self._name_text = self.df["nom"].map(normalize_text)
        self._dci_text = self.df["molecules"].str.replace("|", " ", regex=False)

        self._vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)
        self._vec.fit(pd.concat([self._name_text, self._dci_text]))
        self._name_m = self._vec.transform(self._name_text)
        self._dci_m = self._vec.transform(self._dci_text)

        # Vocabulaire pour les suggestions "Vouliez-vous dire…"
        mols = {m for ms in self.df["molecules"] for m in ms.split(" | ")}
        self._vocab = sorted(mols | set(self._name_text))

    # ------------------------------------------------------------------ search
    def search(self, query: str, filters: SearchFilters | None = None,
               top_k: int = config.SEARCH_TOP_K,
               min_score: float = config.SEARCH_MIN_SCORE) -> pd.DataFrame:
        q = normalize_text(query)
        if not q:
            return self.df.iloc[0:0].assign(score=[], match=[])
        qv = self._vec.transform([q])
        s_name = linear_kernel(qv, self._name_m).ravel()
        s_dci = linear_kernel(qv, self._dci_m).ravel()

        # Bonus si la requête apparaît telle quelle (début de nom / molécule)
        starts_name = self._name_text.str.startswith(q).to_numpy()
        contains_dci = self._dci_text.str.contains(q, regex=False).to_numpy()
        s_name = np.where(starts_name, np.maximum(s_name, 0.6) + 0.25, s_name)
        s_dci = np.where(contains_dci, np.maximum(s_dci, 0.6) + 0.25, s_dci)

        score = np.clip(np.maximum(s_name, s_dci), 0, 1)
        match = np.where(s_name >= s_dci, "nom", "dci")

        res = self.df.assign(score=score, match=match)
        res = res[res["score"] >= min_score]
        if filters:
            res = filters.apply(res)
        return res.sort_values(["score", "n_molecules", "nom"],
                               ascending=[False, True, True]).head(top_k)

    def suggest(self, query: str, limit: int = 3) -> list[str]:
        q = normalize_text(query)
        if not q:
            return []
        hits = process.extract(q, self._vocab, scorer=fuzz.WRatio, limit=limit, score_cutoff=70)
        return [h[0] for h in hits]

    # ------------------------------------------------------------- equivalence
    def get(self, med_id: int) -> pd.Series:
        return self.df.loc[self.df["id"] == med_id].iloc[0]

    def equivalents(self, med_id: int, max_alternatives: int = 8) -> Equivalents:
        ref = self.get(med_id)
        same_dci = self.df[(self.df["dci_key"] == ref["dci_key"]) & (self.df["id"] != med_id)]
        is_strict = (same_dci["dosage_key"] == ref["dosage_key"]) & (
            same_dci["forme_famille"] == ref["forme_famille"])
        strict = same_dci[is_strict].sort_values("nom")
        same_mol = same_dci[~is_strict].sort_values(["forme_famille", "dosage_key", "nom"])

        therapeutic = self.df.iloc[0:0]
        if ref["classe_famille"] != UNKNOWN_CLASS:
            pool = self.df[(self.df["classe_famille"] == ref["classe_famille"]) &
                           (self.df["dci_key"] != ref["dci_key"]) &
                           (self.df["voie_norm"] == ref["voie_norm"])]
            if not pool.empty:
                therapeutic = (pool.groupby("dci_key")
                               .agg(nb_specialites=("id", "size"),
                                    exemples=("nom", lambda s: ", ".join(sorted(set(s))[:3])),
                                    formes=("forme_famille", lambda s: ", ".join(sorted(set(s)))),
                                    id_exemple=("id", "first"))
                               .sort_values("nb_specialites", ascending=False)
                               .head(max_alternatives).reset_index())
        return Equivalents(ref, strict, same_mol, therapeutic)

    def molecule_overview(self, dci_key: str) -> pd.DataFrame:
        """Toutes les présentations disponibles d'une DCI, regroupées."""
        sub = self.df[self.df["dci_key"] == dci_key]
        return (sub.groupby(["forme_famille", "dosage"], dropna=False)
                .agg(specialites=("nom", lambda s: ", ".join(sorted(set(s)))),
                     laboratoires=("laboratoire", "nunique"))
                .reset_index().sort_values(["forme_famille", "dosage"]))

    # ------------------------------------------------------------------- stats
    def stats(self) -> dict[str, int]:
        df = self.df
        group_sizes = df.groupby("groupe_id").size()
        return {
            "specialites": len(df),
            "dci": df["dci_key"].nunique(),
            "laboratoires": df.loc[df["laboratoire"] != "—", "laboratoire"].nunique(),
            "classes": df.loc[df["classe_famille"] != UNKNOWN_CLASS, "classe_famille"].nunique(),
            "groupes_multi": int((group_sizes > 1).sum()),
            "specialites_substituables": int(group_sizes[group_sizes > 1].sum()),
        }
