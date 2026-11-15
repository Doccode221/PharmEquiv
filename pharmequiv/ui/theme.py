"""Identité visuelle de PharmEquiv.

Concept : « l'étiquette d'officine ». Chaque spécialité est présentée comme la
face d'une boîte de médicament : nom commercial, DCI en gras, dosage dans une
pastille, et une bande de couleur sur le bord qui indique le niveau
d'équivalence (comme le bandeau des boîtes de génériques).

Palette
    ENCRE     #1E2A55  texte, titres (encre d'ordonnance)
    OFFICINE  #0E8A6B  générique strict, croix de pharmacie
    INDIGO    #4659A8  même molécule, autre dosage/forme
    BISSAP    #A3264B  alternative thérapeutique (fleur d'hibiscus)
    PAPIER    #FAFBF8  fond
    FILET     #D9DED6  bordures

Typographie
    Bricolage Grotesque : titres (caractère, chaleur)
    Atkinson Hyperlegible : texte et noms de médicaments — dessinée pour
    réduire les confusions entre lettres proches, utile quand une lettre
    sépare deux molécules.
"""

INK = "#1E2A55"
OFFICINE = "#0E8A6B"
INDIGO = "#4659A8"
BISSAP = "#A3264B"
PAPER = "#FAFBF8"
RULE = "#D9DED6"
MUTED = "#5B6483"

LEVEL_COLORS = {"strict": OFFICINE, "molecule": INDIGO, "alternative": BISSAP, "ref": INK}

CSS = f"""
<style>
/* Polices auto-hébergées : voir .streamlit/config.toml [[theme.fontFaces]] */

:root {{
  --ink: {INK}; --officine: {OFFICINE}; --indigo: {INDIGO}; --bissap: {BISSAP};
  --paper: {PAPER}; --rule: {RULE}; --muted: {MUTED};
  --shadow: 0 1px 2px rgba(30,42,85,.05), 0 6px 18px -6px rgba(30,42,85,.08);
}}

html, body, [class*="css"], .stMarkdown, .stTextInput input, .stSelectbox, p, li, label {{
  font-family: 'Atkinson Hyperlegible', system-ui, sans-serif;
}}
h1, h2, h3, h4, .pe-display {{
  font-family: 'Bricolage Grotesque', 'Atkinson Hyperlegible', sans-serif !important;
  color: var(--ink) !important; letter-spacing: -0.01em;
}}
.block-container {{ padding-top: 2.4rem; padding-bottom: 2rem; max-width: 1180px; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
a {{ color: var(--officine) !important; text-decoration-thickness: 1px; text-underline-offset: 2px; }}
::selection {{ background: rgba(14,138,107,.18); }}

/* ---------- En-tête ---------- */
.pe-brand {{ display:flex; align-items:center; flex-wrap:wrap; gap:.7rem; margin-bottom: .6rem; }}
.pe-cross {{ width:34px; height:34px; position:relative; flex:none; }}
.pe-cross::before, .pe-cross::after {{
  content:""; position:absolute; background: var(--officine); border-radius:3px;
}}
.pe-cross::before {{ left:11px; top:0; width:12px; height:34px; }}
.pe-cross::after  {{ top:11px; left:0; width:34px; height:12px; }}
.pe-brand-name {{ font-family:'Bricolage Grotesque',sans-serif; font-weight:800;
  font-size:1.55rem; color:var(--ink); }}
.pe-brand-src {{ color:var(--muted); font-size:.92rem; margin-left:.4rem; }}

.pe-hero {{ margin: 1.8rem 0 1rem; }}
.pe-eyebrow {{ display:inline-flex; align-items:center; gap:.45rem; color: var(--officine);
  font-weight:700; font-size:.82rem; letter-spacing:.08em; text-transform:uppercase;
  background: rgba(14,138,107,.08); border-radius:999px; padding:.25rem .75rem; margin-bottom:.9rem; }}
.pe-hero h1 {{ font-size: clamp(1.9rem, 3.8vw, 2.8rem); line-height:1.05; font-weight:800;
  margin:0 0 .6rem; max-width: 22ch; padding:0; }}
.pe-hero p {{ color: var(--muted); font-size:1.08rem; max-width: 62ch; margin:0; }}

/* Champ de recherche : grand, comme une ligne d'ordonnance */
[data-testid="stTextInputRootElement"] {{
  border: 2px solid var(--ink) !important; border-radius: 12px !important;
  background: #fff !important; box-shadow: var(--shadow);
}}
[data-testid="stTextInputRootElement"]:focus-within {{
  border-color: var(--officine) !important; box-shadow: 0 0 0 4px rgba(14,138,107,.22);
}}
.stTextInput input {{
  font-size: 1.25rem !important; padding: .95rem 1.1rem !important;
  background: #fff !important; color: var(--ink) !important;
}}

/* ---------- Étiquettes (cartes médicament) ---------- */
.pe-label {{
  position:relative; background:#fff; border:1px solid var(--rule);
  border-radius: 6px 12px 12px 6px; padding: .85rem 1rem .85rem 1.35rem;
  margin-bottom:.6rem; color: var(--ink); box-shadow: var(--shadow);
  transition: transform .15s ease, box-shadow .15s ease;
}}
.pe-label:hover {{ transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(30,42,85,.06), 0 10px 24px -8px rgba(30,42,85,.14); }}
.pe-label::before {{
  content:""; position:absolute; left:0; top:0; bottom:0; width:8px;
  border-radius: 6px 0 0 6px; background: var(--band, var(--ink));
}}
.pe-label .nom {{ font-weight:700; font-size:1.08rem; }}
.pe-label .dci {{ font-weight:700; color: var(--band, var(--ink)); }}
.pe-label .meta {{ color: var(--muted); font-size:.92rem; margin-top:.25rem; }}
.pe-dose {{ display:inline-block; border:1.5px solid var(--ink); border-radius:999px;
  padding:.05rem .6rem; font-size:.88rem; font-weight:700; margin-left:.4rem;
  white-space:nowrap; }}

/* Étiquette de référence : la boîte « au comptoir » */
.pe-ref {{ border: 2px solid var(--ink); padding: 1.1rem 1.2rem 1.1rem 1.6rem; }}
.pe-ref:hover {{ transform:none; }}
.pe-ref::before {{ width: 12px; }}
.pe-ref .nom {{ font-family:'Bricolage Grotesque',sans-serif; font-size:1.7rem; font-weight:800; }}
.pe-ref .dci {{ font-size:1.12rem; }}

/* ---------- Échelle d'équivalence ---------- */
.pe-ladder {{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:.6rem;
  margin: .8rem 0 1.2rem; }}
.pe-rung {{ border-top: 6px solid var(--c); background:#fff; border-radius: 0 0 10px 10px;
  padding:.7rem .9rem; border-left:1px solid var(--rule); border-right:1px solid var(--rule);
  border-bottom:1px solid var(--rule); box-shadow: var(--shadow); }}
.pe-rung.is-empty {{ border-top-color: var(--rule); }}
.pe-rung.is-empty b {{ color: var(--muted); opacity:.55; }}
.pe-rung b {{ font-family:'Bricolage Grotesque',sans-serif; font-size:2rem; color: var(--c);
  line-height:1; display:block; }}
.pe-rung span {{ color: var(--ink); font-weight:700; }}
.pe-rung small {{ display:block; color: var(--muted); font-size:.85rem; margin-top:.15rem; }}
@media (max-width: 720px) {{ .pe-ladder {{ grid-template-columns: 1fr; }} }}

.pe-section {{ display:flex; align-items:baseline; flex-wrap:wrap; column-gap:.6rem; row-gap:.1rem;
  margin: 2rem 0 .7rem; padding-bottom:.45rem; border-bottom:1px solid var(--rule); }}
.pe-section h3 {{ margin:0; font-size:1.3rem; }}
.pe-dot {{ width:12px; height:12px; border-radius:50%; background: var(--c); flex:none;
  transform: translateY(1px); }}
.pe-section p {{ margin:0; color: var(--muted); font-size:.95rem; }}

.pe-note {{ border-left: 4px solid var(--bissap); background:#fff; padding:.7rem 1rem;
  color: var(--ink); font-size:.95rem; border-radius: 0 8px 8px 0; }}
.pe-empty {{ border:1.5px dashed var(--rule); border-radius:10px; padding:1rem 1.1rem;
  color: var(--muted); background:#fff; }}

.pe-chips {{ display:flex; flex-wrap:wrap; gap:.4rem; margin:.4rem 0 1rem; }}
.pe-chip {{ border:1px solid var(--rule); background:#fff; border-radius:999px;
  padding:.2rem .7rem; font-size:.9rem; color: var(--ink); }}

/* Chiffres clés : quatre colonnes séparées par des filets */
.pe-figures {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); margin: 1.6rem 0 1rem;
  background:#fff; border:1px solid var(--rule); border-radius:12px; box-shadow: var(--shadow); }}
.pe-figures > span {{ padding: 1rem 1.2rem; color: var(--muted); font-size:.92rem; line-height:1.3; }}
.pe-figures > span + span {{ border-left:1px solid var(--rule); }}
.pe-figures b {{ display:block; color: var(--ink); font-family:'Bricolage Grotesque',sans-serif;
  font-size:1.9rem; font-weight:800; line-height:1.1; margin-bottom:.15rem; }}
.pe-figures > span:last-child b {{ color: var(--officine); }}
@media (max-width: 720px) {{
  .pe-figures {{ grid-template-columns: 1fr 1fr; }}
  .pe-figures > span:nth-child(3) {{ border-left:none; }}
  .pe-figures > span:nth-child(n+3) {{ border-top:1px solid var(--rule); }}
}}

/* Alternatives thérapeutiques */
.pe-alt {{ padding:.2rem 0; color: var(--ink); }}
.pe-alt .mol {{ font-weight:700; font-size:1.02rem; }}
.pe-alt .count {{ display:inline-block; margin-left:.45rem; font-size:.8rem; font-weight:700;
  color: var(--bissap); background: rgba(163,38,75,.08); border-radius:999px; padding:.05rem .55rem; }}
.pe-alt .ex {{ color: var(--muted); font-size:.92rem; margin-top:.15rem; }}

[data-testid="stVerticalBlockBorderWrapper"]:has(.pe-alt) {{ background:#fff; border-radius:12px;
  border-color: var(--rule) !important; box-shadow: var(--shadow); }}

/* Tableaux */
[data-testid="stExpander"] details {{ border-color: var(--rule); border-radius:10px; background:#fff; }}
[data-testid="stPlotlyChart"] {{ background:#fff; border:1px solid var(--rule); border-radius:12px;
  padding:.4rem .6rem; box-shadow: var(--shadow); }}
[data-testid="stTable"] table, .stMarkdown table {{ border-collapse:collapse; background:#fff; }}
.stMarkdown table th {{ background:#F1F4EF; color: var(--ink); }}
.stMarkdown table th, .stMarkdown table td {{ border-color: var(--rule) !important; padding:.55rem .8rem; }}

/* Onglets (Streamlit ≥ 1.67 : react-aria, data-testid="stTab") */
[role="tablist"] {{ gap: 1.8rem; }}
[data-testid="stTab"] {{ padding-top:.5rem; padding-bottom:.6rem; }}
[data-testid="stTab"] p {{ font-family:'Bricolage Grotesque',sans-serif !important;
  font-size:1.08rem !important; font-weight:700; color: var(--muted); transition: color .15s ease; }}
[data-testid="stTab"]:hover p,
[data-testid="stTab"][aria-selected="true"] p {{ color: var(--ink); }}

section[data-testid="stSidebar"] {{ background: #F1F4EF; border-right:1px solid var(--rule); }}
section[data-testid="stSidebar"] h2 {{ font-size: 1.15rem; }}

.stButton button, .stDownloadButton button {{ border-radius: 999px; border:1.5px solid var(--ink); color: var(--ink);
  font-weight:700; background:#fff; }}
.stButton button:hover, .stDownloadButton button:hover {{ border-color: var(--officine); color: var(--officine); }}
.stDownloadButton button {{ background: var(--ink); color:#fff; padding:.45rem 1.1rem; }}
.stDownloadButton button:hover {{ background: var(--officine); color:#fff !important; }}
.stButton button:focus-visible, .stDownloadButton button:focus-visible {{ outline: 3px solid var(--officine); outline-offset:2px; }}

.pe-footer {{ color: var(--muted); font-size:.85rem; border-top:1px solid var(--rule);
  margin-top: 2.5rem; padding-top: .8rem; }}

@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
</style>
"""
