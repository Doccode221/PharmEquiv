import pandas as pd
import pytest

from pharmequiv.data.pipeline import build_dataset
from pharmequiv.engine.search import EquivalenceEngine, SearchFilters

ROWS = [
    # nom, dci, dosage, presentation, forme, voie, labo, classe
    ("DOLIPRANE", "PARACETAMOL", "500 mg", "B/16", "comprimé", "orale", "SANOFI", "ANTALGIQUE"),
    ("EFFERALGAN", "Paracétamol", "500mg", "B/16", "Comprimé pelliculé", "Orale", "UPSA", "—"),
    ("PARACETAMOL DENK", "PARACETAMOL", "1 g", "B/8", "comprimé", "orale", "DENK", "ANTALGIQUE"),
    ("DOLIPRANE SIROP", "PARACETAMOL", "2,4 %", "FL/100ml", "sirop", "orale", "SANOFI", "ANTALGIQUE"),
    ("TRAMAL", "TRAMADOL", "50 mg", "B/20", "gélule", "orale", "GRUNENTHAL", "ANTALGIQUE"),
    ("AUGMENTIN", "AMOXICILLINE / ACIDE CLAVULANIQUE", "1 g / 125 mg", "B/16", "comprimé", "orale", "GSK",
     "ANTIBIOTIQUE"),
    ("CLAMOXYL", "AMOXCILLINE", "1 g", "B/14", "comprimé", "orale", "GSK", "ANTIBIOTIQUE"),
    ("AMOXIL", "AMOXICILLINE", "1000 mg", "B/14", "comprimé dispersible", "orale", "X", "ANTIBIOTIQUE"),
]


@pytest.fixture(scope="module")
def engine():
    raw = pd.DataFrame(ROWS, columns=["nom", "dci", "dosage", "presentation", "forme",
                                      "voie", "laboratoire", "classe"])
    df, _ = build_dataset(raw)
    return EquivalenceEngine(df)


def _id(engine, name):
    return int(engine.df.loc[engine.df["nom"] == name, "id"].iloc[0])


def test_search_by_brand_and_dci(engine):
    assert engine.search("doliprane").iloc[0]["nom"].startswith("DOLIPRANE")
    assert set(engine.search("paracetamol")["dci_key"]) == {"paracetamol"}


def test_search_tolerates_typos_and_accents(engine):
    assert engine.search("paracétamole").iloc[0]["dci_key"] == "paracetamol"


def test_search_filters(engine):
    res = engine.search("paracetamol", SearchFilters(formes=["Sirop"]))
    assert list(res["nom"]) == ["DOLIPRANE SIROP"]


def test_strict_generics(engine):
    eq = engine.equivalents(_id(engine, "DOLIPRANE"))
    assert list(eq.strict["nom"]) == ["EFFERALGAN"]           # 500mg = 500 mg, comprimé
    assert set(eq.same_molecule["nom"]) == {"PARACETAMOL DENK", "DOLIPRANE SIROP"}


def test_therapeutic_alternatives(engine):
    eq = engine.equivalents(_id(engine, "DOLIPRANE"))
    assert "tramadol" in set(eq.therapeutic["dci_key"])


def test_typo_and_unit_harmonisation(engine):
    # AMOXCILLINE (faute) 1 g == AMOXICILLINE 1000 mg, mais forme différente
    eq = engine.equivalents(_id(engine, "CLAMOXYL"))
    assert "AMOXIL" in set(eq.same_molecule["nom"]) | set(eq.strict["nom"])
    assert "AUGMENTIN" not in set(eq.strict["nom"])


def test_class_inference(engine):
    row = engine.get(_id(engine, "EFFERALGAN"))
    assert row["classe"] == "Antalgique" and row["classe_inferee"]
