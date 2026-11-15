"""Fonctions pures de normalisation des champs de la base AMM.

Chaque fonction prend une valeur brute (souvent sale) et renvoie une forme
canonique utilisable comme *clé de comparaison*. Les valeurs d'origine sont
toujours conservées à part pour l'affichage.
"""

from __future__ import annotations

import re
import unicodedata

from pharmequiv.config import MISSING_TOKENS

# ---------------------------------------------------------------------------
# Texte générique
# ---------------------------------------------------------------------------


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def normalize_text(value) -> str:
    """Minuscules, sans accents, espaces compactés. Renvoie '' si vide."""
    if value is None:
        return ""
    text = str(value)
    text = strip_accents(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return "" if text in MISSING_TOKENS else text


def clean_display(value) -> str | None:
    """Valeur lisible pour l'affichage (espaces nettoyés), ou None si vide."""
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return None if normalize_text(text) == "" else text


# ---------------------------------------------------------------------------
# DCI (Dénomination Commune Internationale)
# ---------------------------------------------------------------------------

_DCI_SPLIT = re.compile(r"\s*(?:/|\+|,|;|&|\bet\b|\band\b)\s*")
_DCI_NOISE = re.compile(r"[()\[\]\"'.*]")


def split_molecules(dci) -> list[str]:
    """'Amoxicilline / Acide Clavulanique' -> ['acide clavulanique', 'amoxicilline']."""
    text = normalize_text(dci)
    if not text:
        return []
    text = _DCI_NOISE.sub(" ", text)
    parts = [re.sub(r"\s+", " ", p).strip(" -") for p in _DCI_SPLIT.split(text)]
    # Unicité + tri : l'ordre des molécules ne change pas l'équivalence
    return sorted({p for p in parts if len(p) > 1})


# Fautes fréquentes (trop présentes pour être détectées comme "rares") et
# synonymes établis. Appliqué AVANT la correction automatique.
CURATED_FIXES = {
    "amoxcilline": "amoxicilline", "amoxilline": "amoxicilline",
    "amoxiciliine": "amoxicilline", "amoxycilline": "amoxicilline",
    "amoxicillin": "amoxicilline", "lamividune": "lamivudine",
    "valsartran": "valsartan", "glimepride": "glimepiride",
    "dapaglifozine": "dapagliflozine", "vitaminec": "vitamine c",
    "vitamineb1": "vitamine b1", "vitamineb6": "vitamine b6",
    "acidepantothenique": "acide pantothenique", "ibuprofen": "ibuprofene",
    "clavulanate de potassium": "acide clavulanique",
    "clavulanate potassium": "acide clavulanique",
    "clavulanate de potassium dilue": "acide clavulanique",
    "acide acetylsalicylique": "acide acetylsalicylique",
    "aspirine": "acide acetylsalicylique", "chlorphenamine": "chlorpheniramine",
    "artemeter": "artemether", "acide clavunique": "acide clavulanique",
    "potassium clavunique": "acide clavulanique", "clavunate de potassium": "acide clavulanique",
    "clavulanate": "acide clavulanique", "acide clavulanique potassique": "acide clavulanique",
}

# Sels / états d'hydratation : ils ne changent pas le principe actif.
_SALT_WORDS = (
    "dichlorhydrate|chlorhydrate|chlorydrate|hydrochloride|hcl|bromhydrate|"
    "trihydrate|trihydratee|dihydrate|monohydrate|sesquihydrate|hemihydrate|hydrate|anhydre|"
    "besilate|besylate|mesilate|mesylate|hemifumarate|fumarate|tartrate|succinate|"
    "erbumine|tert-butylamine|ter-butylamine|sodique|potassique|calcique|usp|bp"
)
_SALT_RE = re.compile(rf"\b(?:{_SALT_WORDS})\b(?:\s+(?:de|d)\b)?")


def active_moiety(molecule: str) -> str:
    """'chlorhydrate de metformine' -> 'metformine' ; 'amlodipine besilate' -> 'amlodipine'."""
    stripped = _SALT_RE.sub(" ", molecule)
    stripped = re.sub(r"\s+", " ", stripped).strip(" -")
    stripped = re.sub(r"^(?:de|d)\s+", "", stripped)
    # On ne garde la version épurée que si elle reste un nom plausible
    if len(stripped.replace(" ", "")) >= 5:
        return stripped
    return molecule


def dci_key(molecules: list[str]) -> str:
    return " + ".join(sorted(set(molecules)))


# ---------------------------------------------------------------------------
# Dosage
# ---------------------------------------------------------------------------

_UNIT_FACTORS = {  # converti en unité de référence
    "g": ("mg", 1000.0),
    "gr": ("mg", 1000.0),
    "mg": ("mg", 1.0),
    "ug": ("mg", 0.001),
    "µg": ("mg", 0.001),
    "mcg": ("mg", 0.001),
    "ml": ("ml", 1.0),
    "l": ("ml", 1000.0),
    "%": ("%", 1.0),
    "ui": ("ui", 1.0),
    "u": ("ui", 1.0),
}
_DOSE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mcg|µg|ug|mg|gr|g|ml|ui|u|l|%)(?![a-z])")


def _fmt(x: float) -> str:
    return f"{x:.4f}".rstrip("0").rstrip(".")


def dosage_key(dosage) -> str:
    """Clé de dosage comparable et indépendante de l'écriture.

    * unités harmonisées : '1 G' et '1000mg' -> '1000mg'
    * concentrations ramenées à 1 ml : '250 mg / 5 ml' et '50 mg/ml' -> '50mg/ml'
    * associations triées : '500 mg / 125 mg' et '125mg/500mg' -> '125mg+500mg'

    Si aucune dose n'est reconnue, renvoie le texte normalisé sans espaces
    (comparaison exacte en dernier recours).
    """
    text = normalize_text(dosage)
    if not text:
        return ""
    text = text.replace("µ", "u")
    text = re.sub(r"/\s*ml\b", "/1 ml", text)  # 'mg/ml' -> 'mg/1 ml'
    found = _DOSE_RE.findall(text)
    if not found:
        return re.sub(r"\s+", "", text)
    doses = []
    for num, unit in found:
        ref_unit, factor = _UNIT_FACTORS[unit]
        doses.append((float(num.replace(",", ".")) * factor, ref_unit))

    volume = None
    if len(doses) >= 2 and doses[-1][1] == "ml" and all(u != "ml" for _, u in doses[:-1]):
        volume = doses.pop()[0] or None
    if volume:
        parts = sorted(_fmt(v / volume) + u for v, u in doses)
        return "+".join(parts) + "/ml"
    return "+".join(sorted(_fmt(v) + u for v, u in doses))


# ---------------------------------------------------------------------------
# Forme galénique & voie d'administration
# ---------------------------------------------------------------------------

# Ordre important : la première règle qui correspond l'emporte.
_FORME_RULES: list[tuple[str, str]] = [
    (r"effervescent", "Comprimé effervescent"),
    (r"orodispersible|dispersible|lyoc", "Comprimé dispersible"),
    (r"compr|cpr|\bcp\b", "Comprimé"),
    (r"pastille|comprime a sucer", "Pastille"),
    (r"gel+ul+e|capsule|caps", "Gélule"),
    (r"sirop", "Sirop"),
    (r"suspension (buvable|orale)|susp.*buv|poudre pour suspension", "Suspension buvable"),
    (r"solution (buvable|orale)|gouttes? (buvables?|orales?)|buvable", "Solution buvable"),
    (r"perfusion", "Perfusion"),
    (r"i[jn]+ectable|inject|ampoule|flacon|seringue|poudre a reconstituer", "Injectable"),
    (r"collyre|ophtalm", "Collyre"),
    (r"suppositoire", "Suppositoire"),
    (r"ovule|vaginal", "Ovule / forme vaginale"),
    (r"creme", "Crème"),
    (r"pommade", "Pommade"),
    (r"\bgel\b", "Gel"),
    (r"sachet|granule", "Sachet / granulés"),
    (r"spray|aerosol|inhal|nebul", "Spray / inhalation"),
    (r"gouttes|auriculaire|nasal", "Gouttes"),
    (r"lotion|solution.*(externe|cutan|dermi|locale)|shampo|savon|lait dermique", "Solution externe"),
    (r"bain de bouche|collutoire|buccal", "Bain de bouche / collutoire"),
    (r"baume", "Pommade"),
    (r"patch|dispositif transdermique", "Patch"),
    (r"poudre", "Poudre"),
    (r"\bsolution\b|\bsuspension\b", "Solution / suspension"),
]


_MODIFIED_RELEASE = re.compile(
    r"liberation (prolongee|modifiee|retardee|controlee)|\bretard\b|\b(lp|lm|xr|sr|er|cr|xl|od|mr)\b"
)
_GASTRO_RESISTANT = re.compile(r"gastro.?resistant|enrobage entero|\bgr\b")


def release_type(forme, nom="") -> str:
    """'' (libération immédiate), 'LP' (prolongée/modifiée) ou 'gastro-résistant'.

    Deux spécialités de même DCI et même dosage ne sont PAS interchangeables si
    l'une est à libération prolongée (ex. Glucophage vs Glucophage Retard).
    """
    text = f"{normalize_text(forme)} {normalize_text(nom)}"
    if _MODIFIED_RELEASE.search(text):
        return "LP"
    if _GASTRO_RESISTANT.search(text):
        return "gastro-résistant"
    return ""


def forme_famille(forme, nom="") -> str:
    text = normalize_text(forme)
    if not text:
        return "Non renseignée"
    family = "Autre"
    for pattern, label in _FORME_RULES:
        if re.search(pattern, text):
            family = label
            break
    release = release_type(forme, nom)
    if release and family in {"Comprimé", "Gélule", "Comprimé dispersible", "Autre"}:
        family = f"{family} {release}"
    return family


_VOIE_RULES: list[tuple[str, str]] = [
    (r"intra ?ve[iy]?ne?u|\bi\.?v\b|perfusion", "Intraveineuse"),
    (r"intra ?muscul|\bim\b", "Intramusculaire"),
    (r"sous.?cutan", "Sous-cutanée"),
    (r"inject|parenter", "Injectable"),
    (r"oral|buccal|per os|sublingu", "Orale"),
    (r"cutan|dermi|topique|locale|externe", "Cutanée"),
    (r"ocul|ophtalm", "Oculaire"),
    (r"rect", "Rectale"),
    (r"vagin", "Vaginale"),
    (r"nasal", "Nasale"),
    (r"auric", "Auriculaire"),
    (r"inhal|pulmon|respir", "Inhalée"),
]


def voie_norm(voie) -> str:
    text = normalize_text(voie)
    if not text:
        return "Non renseignée"
    for pattern, label in _VOIE_RULES:
        if re.search(pattern, text):
            return label
    return text.capitalize()


# ---------------------------------------------------------------------------
# Classe thérapeutique
# ---------------------------------------------------------------------------


def classe_norm(classe) -> str:
    """'ANTIINFLAMMATOIRE NON STEROÏDIEN' et 'Anti-inflammatoire non stéroïdien'
    -> 'Antiinflammatoire non steroidien'."""
    text = normalize_text(classe)
    if not text:
        return ""
    text = re.sub(r"\banti[\s-]+", "anti", text)
    text = re.sub(r"\s*-\s*", "-", text)
    return text[:1].upper() + text[1:]


_VAGUE_CLASS_WORDS = {"complement", "agent", "inhibiteur", "solute", "solution", "produit",
                      "medicament", "traitement", "supplement", "vaccin", "hormone"}


def classe_famille(classe: str) -> str:
    """Regroupement grossier pour les alternatives thérapeutiques.

    'Antidiabetiques oraux / biguanides' et 'Antidiabetique' -> 'Antidiabetique'.
    Les anti-inflammatoires restent séparés en stéroïdiens / non stéroïdiens.
    """
    key = normalize_text(classe)
    if not key or key == "non renseignee":
        return ""
    words = [w for w in re.split(r"[\s/,()]+", key) if w and w not in {"de", "d", "du", "des", "a"}]
    first = words[0]
    first = first[:-1] if first.endswith("s") and len(first) > 5 else first
    if first in _VAGUE_CLASS_WORDS and len(words) > 1:
        first = f"{first} {words[1]}"
    if first == "antiinflammatoire":
        first += " non steroidien" if "non" in key else (" steroidien" if "steroid" in key else "")
    return first[:1].upper() + first[1:]
