"""Configuration centrale de PharmEquiv (chemins, seuils, constantes)."""

from __future__ import annotations

from pathlib import Path

# --- Chemins -----------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_CSV = DATA_DIR / "raw" / "medicaments_amm_senegal.csv"
PROCESSED_CSV = DATA_DIR / "processed" / "medicaments_clean.csv"

# --- Source ------------------------------------------------------------------
ARP_URL = "https://arp.sn/bases-de-donnees/medicaments-autorises"

# Colonnes telles qu'elles apparaissent sur le site de l'ARP
RAW_COLUMNS = [
    "Nom du Médicament",
    "DCI",
    "Dosage",
    "Présentation",
    "Forme Galénique",
    "Voie d'administration",
    "Laboratoire",
    "Classe Thérapeutique",
]

# Noms de colonnes internes (snake_case, sans accents)
COLUMN_MAP = {
    "Nom du Médicament": "nom",
    "DCI": "dci",
    "Dosage": "dosage",
    "Présentation": "presentation",
    "Forme Galénique": "forme",
    "Voie d'administration": "voie",
    "Laboratoire": "laboratoire",
    "Classe Thérapeutique": "classe",
}

# Valeurs considérées comme "vides" dans la source
MISSING_TOKENS = {"", "—", "-", "–", "nan", "none", "n/a", "na", "?"}

# --- Moteur de recherche -----------------------------------------------------
SEARCH_MIN_SCORE = 0.25      # score minimal (0-1) pour qu'un résultat soit affiché
SEARCH_TOP_K = 40            # nombre max. de médicaments renvoyés par requête
TYPO_MIN_SIMILARITY = 90     # seuil rapidfuzz (0-100) pour corriger une faute de DCI
TYPO_MAX_RARE_COUNT = 5      # une molécule vue <= N fois est candidate à correction
