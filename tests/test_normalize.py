import pytest

from pharmequiv.data import normalize as nz
from pharmequiv.data.pipeline import is_safe_typo


@pytest.mark.parametrize("raw, expected", [
    ("Paracétamol ", "paracetamol"),
    ("  AMOXICILLINE  ", "amoxicilline"),
    ("—", ""),
    (None, ""),
])
def test_normalize_text(raw, expected):
    assert nz.normalize_text(raw) == expected


def test_split_molecules_is_order_insensitive():
    a = nz.split_molecules("AMOXICILLINE / ACIDE CLAVULANIQUE")
    b = nz.split_molecules("acide clavulanique + amoxicilline")
    assert a == b == ["acide clavulanique", "amoxicilline"]


@pytest.mark.parametrize("raw, expected", [
    ("chlorhydrate de metformine", "metformine"),
    ("amlodipine besilate", "amlodipine"),
    ("amoxicilline trihydrate", "amoxicilline"),
    ("paracetamol", "paracetamol"),
])
def test_active_moiety(raw, expected):
    assert nz.active_moiety(raw) == expected


@pytest.mark.parametrize("a, b", [
    ("1 G", "1000 mg"),
    ("250 mg / 5 ml", "50 mg/ml"),
    ("500 mg / 125 mg", "125mg/500mg"),
])
def test_dosage_key_equivalences(a, b):
    assert nz.dosage_key(a) == nz.dosage_key(b)


def test_dosage_key_distinguishes_strengths():
    assert nz.dosage_key("500 mg") != nz.dosage_key("1000 mg")


@pytest.mark.parametrize("raw, family", [
    ("comprimé pelliculé", "Comprimé"),
    ("Comprimé effervescent", "Comprimé effervescent"),
    ("poudre pour suspension buvable", "Suspension buvable"),
    ("ampoule injectable", "Injectable"),
    ("gélulle", "Gélule"),
    ("comprimé à libération prolongée", "Comprimé LP"),
    ("comprimé gastro-résistant", "Comprimé gastro-résistant"),
])
def test_forme_famille(raw, family):
    assert nz.forme_famille(raw) == family


def test_release_detected_from_brand_name():
    # 'GLUCOPHAGE RETARD' en comprimé simple n'est pas un générique de 'GLUCOPHAGE'
    assert nz.forme_famille("comprimé", "GLUCOPHAGE RETARD") == "Comprimé LP"
    assert nz.forme_famille("comprimé", "GLUCOPHAGE 850") == "Comprimé"


@pytest.mark.parametrize("raw, voie", [
    ("intra veineuse", "Intraveineuse"),
    ("ORALE", "Orale"),
    ("cutanee", "Cutanée"),
])
def test_voie_norm(raw, voie):
    assert nz.voie_norm(raw) == voie


def test_classe_norm_merges_spellings():
    assert nz.classe_norm("ANTI-INFLAMMATOIRE NON STÉROÏDIEN") == \
        nz.classe_norm("ANTIINFLAMMATOIRE NON STEROIDIEN")


@pytest.mark.parametrize("wrong, right, safe", [
    ("amoxiciline", "amoxicilline", True),
    ("acide folinique", "acide folique", False),      # deux molécules distinctes
    ("levocetirizine", "cetirizine", False),          # énantiomère
    ("vitamine d2", "vitamine b2", False),            # lettres différentes
    ("vitamine b6", "vitamine b2", False),            # chiffres différents
])
def test_typo_guardrails(wrong, right, safe):
    assert is_safe_typo(wrong, right) is safe


@pytest.mark.parametrize("raw, fam", [
    ("Antidiabetiques oraux / biguanides", "Antidiabetique"),
    ("ANTIDIABETIQUE", "Antidiabetique"),
    ("Antiinflammatoire non steroidien", "Antiinflammatoire non steroidien"),
    ("Antiinflammatoire steroidien", "Antiinflammatoire steroidien"),
    ("Complement alimentaire", "Complement alimentaire"),
])
def test_classe_famille(raw, fam):
    assert nz.classe_famille(raw) == fam
