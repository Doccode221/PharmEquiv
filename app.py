"""PharmEquiv — point d'entrée Streamlit.

    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from pharmequiv import config
from pharmequiv.data.pipeline import load_processed
from pharmequiv.engine.search import UNKNOWN_CLASS, EquivalenceEngine, SearchFilters
from pharmequiv.ui import components as ui
from pharmequiv.ui.theme import CSS, INK, OFFICINE, RULE

st.set_page_config(page_title="PharmEquiv · Génériques au Sénégal", page_icon="💊",
                   layout="wide", initial_sidebar_state="auto")
st.markdown(CSS, unsafe_allow_html=True)

EXAMPLES = ["Doliprane", "Augmentin", "Metformine", "Amlodipine", "Coartem"]


@st.cache_resource(show_spinner="Préparation de la base AMM…")
def get_engine() -> EquivalenceEngine:
    return EquivalenceEngine(load_processed())


engine = get_engine()
df = engine.df


def set_query(value: str) -> None:
    st.session_state["query"] = value


def pick_example() -> None:
    if st.session_state.get("example"):
        st.session_state["query"] = st.session_state["example"]
    st.session_state["example"] = None


# --------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Affiner la recherche")
    classes = sorted(c for c in df["classe_famille"].unique() if c != UNKNOWN_CLASS)
    f_classes = st.multiselect("Classe thérapeutique", classes, placeholder="Toutes")
    f_formes = st.multiselect("Forme", sorted(df["forme_famille"].unique()), placeholder="Toutes")
    f_voies = st.multiselect("Voie d'administration", sorted(df["voie_norm"].unique()),
                             placeholder="Toutes")
    filters = SearchFilters(f_classes, f_formes, f_voies)
    st.caption("Les filtres s'appliquent à la liste des résultats, pas au calcul des "
               "équivalents.")
    st.divider()
    st.caption("PharmEquiv aide à repérer des équivalences dans la base AMM. Toute "
               "substitution reste une décision du pharmacien ou du prescripteur.")

# ---------------------------------------------------------------------- header
st.markdown(ui.brand(config.ARP_URL), unsafe_allow_html=True)
tab_search, tab_explore, tab_method = st.tabs(
    ["Trouver un équivalent", "Explorer la base", "Comment ça marche"])

# ======================================================================= SEARCH
with tab_search:
    st.markdown(ui.hero(), unsafe_allow_html=True)
    query = st.text_input("Nom de marque ou molécule", key="query",
                          placeholder="ex. Doliprane, amoxicilline, metformine…",
                          label_visibility="collapsed")
    st.pills("Essayer", EXAMPLES, key="example", on_change=pick_example)

    if not query:
        st.markdown(ui.figures(engine.stats()), unsafe_allow_html=True)
    else:
        results = engine.search(query, filters)
        if results.empty:
            st.markdown(ui.empty(f"Aucune spécialité ne correspond à « {query} » avec les "
                                 "filtres actuels. Vérifiez l'orthographe ou retirez un filtre."),
                        unsafe_allow_html=True)
            suggestions = engine.suggest(query)
            if suggestions:
                st.write("Vouliez-vous dire :")
                scols = st.columns(len(suggestions) + 2)
                for c, s in zip(scols, suggestions):
                    c.button(s, key=f"sug_{s}", on_click=set_query, args=(s,))
        else:
            st.markdown(f"**{len(results)}** présentation(s) trouvée(s). "
                        "Cliquez sur une ligne pour choisir le médicament de référence.")
            table = pd.DataFrame({
                "Spécialité": results["nom"],
                "Molécule(s)": results["molecules"].str.replace(" | ", " + ", regex=False),
                "Dosage": results["dosage"],
                "Forme": results["forme_famille"],
                "Laboratoire": results["laboratoire"],
                "Pertinence": results["score"],
            })
            event = st.dataframe(
                table, hide_index=True, width="stretch", height=280,
                on_select="rerun", selection_mode="single-row", key=f"res_{query}",
                column_config={"Pertinence": st.column_config.ProgressColumn(
                    "Pertinence", min_value=0.0, max_value=1.0, format=" ", width="small")},
            )
            rows = event.selection.rows if event and event.selection else []
            ref_id = int(results.iloc[rows[0] if rows else 0]["id"])
            eq = engine.equivalents(ref_id)
            ref = eq.reference

            st.markdown("#### Médicament de référence")
            st.markdown(ui.med_label(ref, "ref", reference=True), unsafe_allow_html=True)
            st.markdown(ui.ladder(len(eq.strict), len(eq.same_molecule), len(eq.therapeutic)),
                        unsafe_allow_html=True)

            # Niveau 1 ---------------------------------------------------------
            st.markdown(ui.section("strict", "Génériques stricts",
                                   f"{ref['molecules'].replace(' | ', ' + ')} · "
                                   f"{ref['dosage']} · {ref['forme_famille'].lower()}"),
                        unsafe_allow_html=True)
            if eq.strict.empty:
                st.markdown(ui.empty("Aucune autre spécialité autorisée n'a exactement la même "
                                     "composition, le même dosage et la même forme. Regardez "
                                     "les autres dosages ci-dessous."), unsafe_allow_html=True)
            else:
                shown = eq.strict.head(12)
                c1, c2 = st.columns(2)
                for i, (_, row) in enumerate(shown.iterrows()):
                    (c1 if i % 2 == 0 else c2).markdown(ui.med_label(row, "strict"),
                                                        unsafe_allow_html=True)
                if len(eq.strict) > len(shown):
                    with st.expander(f"Voir les {len(eq.strict)} génériques stricts"):
                        st.dataframe(eq.strict[["nom", "dosage", "forme", "presentation",
                                                "laboratoire"]], hide_index=True,
                                     width="stretch")
                labs = sorted(eq.strict["laboratoire"].unique())
                st.caption(f"{len(labs)} laboratoire(s) : " + ", ".join(labs[:12])
                           + ("…" if len(labs) > 12 else ""))

            # Niveau 2 ---------------------------------------------------------
            st.markdown(ui.section("molecule", "Même molécule",
                                   "autre dosage ou autre forme : adaptation de la posologie "
                                   "nécessaire"), unsafe_allow_html=True)
            if eq.same_molecule.empty:
                st.markdown(ui.empty("Cette molécule n'existe pas sous d'autres dosages ou "
                                     "formes dans la base."), unsafe_allow_html=True)
            else:
                st.dataframe(
                    eq.same_molecule[["nom", "dosage", "forme_famille", "forme", "laboratoire"]]
                    .rename(columns={"nom": "Spécialité", "dosage": "Dosage",
                                     "forme_famille": "Forme", "forme": "Forme (libellé AMM)",
                                     "laboratoire": "Laboratoire"}),
                    hide_index=True, width="stretch",
                    height=min(38 + 35 * len(eq.same_molecule), 320))

            # Niveau 3 ---------------------------------------------------------
            st.markdown(ui.section("alternative", "Alternatives thérapeutiques",
                                   f"autres molécules · {ref['classe_famille'].lower()} · "
                                   f"voie {ref['voie_norm'].lower()}"), unsafe_allow_html=True)
            if eq.therapeutic.empty:
                st.markdown(ui.empty("Classe thérapeutique non renseignée ou sans autre "
                                     "molécule pour cette voie."), unsafe_allow_html=True)
            else:
                with st.container(border=True):
                    for _, alt in eq.therapeutic.iterrows():
                        a1, a2 = st.columns([5, 1.3], vertical_alignment="center")
                        a1.markdown(ui.alternative(alt["dci_key"], int(alt["nb_specialites"]),
                                                   alt["exemples"], alt["formes"]),
                                    unsafe_allow_html=True)
                        a2.button("Voir cette molécule", key=f"alt_{alt['dci_key']}",
                                  on_click=set_query, args=(alt["dci_key"],),
                                  width="stretch")

            st.markdown(ui.note(
                "<b>À vérifier avant toute substitution.</b> Même DCI, même dosage et même "
                "forme ne garantissent pas la bioéquivalence (excipients, libération modifiée, "
                "marge thérapeutique étroite). Les alternatives thérapeutiques relèvent de "
                "la prescription médicale."), unsafe_allow_html=True)

            export = pd.concat([
                eq.strict.assign(niveau="Générique strict"),
                eq.same_molecule.assign(niveau="Même molécule"),
            ])[["niveau", "nom", "molecules", "dosage", "forme", "voie", "presentation",
                "laboratoire", "classe"]]
            st.download_button("Télécharger les équivalents (CSV)",
                               export.to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"equivalents_{ref['nom'].lower().replace(' ', '_')}.csv",
                               mime="text/csv")

# ====================================================================== EXPLORE
PLOT_CONFIG = {"displayModeBar": False}


def bar(data: pd.DataFrame, x: str, y: str, title: str):
    fig = px.bar(data, x=x, y=y, orientation="h", title=title)
    fig.update_traces(marker_color=OFFICINE, marker_line_width=0,
                      hovertemplate="%{y} : %{x} spécialités<extra></extra>")
    fig.update_layout(
        height=30 * len(data) + 90, margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Atkinson Hyperlegible, sans-serif", color=INK, size=13),
        title=dict(font=dict(family="Bricolage Grotesque, sans-serif", size=17)),
        yaxis=dict(title=None, autorange="reversed", tickfont=dict(color=INK)), bargap=0.3,
        xaxis=dict(title=None, gridcolor=RULE, zeroline=False),
    )
    return fig


with tab_explore:
    st.markdown("### Une molécule, toutes ses présentations")
    dci_counts = df["dci_key"].value_counts()
    choice = st.selectbox("Choisir une molécule ou une association",
                          dci_counts.index.tolist(),
                          format_func=lambda k: f"{k}  ({dci_counts[k]} spécialités)")
    sub = df[df["dci_key"] == choice]
    st.markdown(ui.chips([f"{sub['nom'].nunique()} marques",
                          f"{sub['laboratoire'].nunique()} laboratoires",
                          f"{sub['dosage_key'].nunique()} dosages",
                          f"Classe : {sub['classe'].mode().iat[0]}"]), unsafe_allow_html=True)
    st.dataframe(engine.molecule_overview(choice).rename(columns={
        "forme_famille": "Forme", "dosage": "Dosage", "specialites": "Spécialités",
        "laboratoires": "Nb labos"}), hide_index=True, width="stretch")

    st.markdown("### Le marché en un coup d'œil")
    c1, c2 = st.columns(2)
    top_dci = dci_counts.head(15).rename_axis("Molécule").reset_index(name="n")
    c1.plotly_chart(bar(top_dci, "n", "Molécule", "Molécules les plus génériquées"),
                    width="stretch", config=PLOT_CONFIG)
    top_cls = (df.loc[df["classe_famille"] != UNKNOWN_CLASS, "classe_famille"].value_counts().head(15)
               .rename_axis("Classe").reset_index(name="n"))
    c2.plotly_chart(bar(top_cls, "n", "Classe", "Classes thérapeutiques"),
                    width="stretch", config=PLOT_CONFIG)
    c3, c4 = st.columns(2)
    top_lab = df.loc[df["laboratoire"] != "—", "laboratoire"].value_counts().head(15).rename_axis("Laboratoire") \
        .reset_index(name="n")
    c3.plotly_chart(bar(top_lab, "n", "Laboratoire", "Laboratoires les plus présents"),
                    width="stretch", config=PLOT_CONFIG)
    formes = df["forme_famille"].value_counts().head(15).rename_axis("Forme").reset_index(name="n")
    c4.plotly_chart(bar(formes, "n", "Forme", "Formes galéniques les plus fréquentes"), width="stretch", config=PLOT_CONFIG)

# ======================================================================= METHOD
with tab_method:
    st.markdown("### Trois niveaux d'équivalence")
    st.markdown(ui.ladder(1, 2, 3), unsafe_allow_html=True)
    st.markdown("""
| Niveau | Règle | Usage |
|---|---|---|
| **Générique strict** | même DCI + même dosage + même forme galénique | substitution directe envisageable |
| **Même molécule** | même DCI, dosage ou forme différents | adapter la posologie / le mode de prise |
| **Alternative thérapeutique** | même classe + même voie, autre DCI | nécessite un avis médical |

### Ce que fait le moteur

1. **Recherche floue** — la requête est comparée au nom commercial et à la DCI par
   TF-IDF sur des n-grammes de caractères : « amoxiciline », « Paracétamol » ou
   « augmentin » donnent le bon résultat.
2. **Normalisation des DCI** — accents, majuscules, ordre des molécules
   (« amoxicilline / acide clavulanique » = « acide clavulanique + amoxicilline »),
   sels retirés (« chlorhydrate de metformine » → « metformine ») et fautes de
   frappe corrigées automatiquement, avec des garde-fous (acide folinique ≠ acide
   folique, lévocétirizine ≠ cétirizine).
3. **Normalisation des dosages** — « 1 g » = « 1000 mg », « 250 mg / 5 ml » =
   « 50 mg/ml ».
4. **Familles de formes** — « comprimé pelliculé », « Comprime », « cp » → *Comprimé*.
   Les formes à libération prolongée (« LP », « Retard », « SR », « XR »…) et
   gastro-résistantes forment des familles à part : *Glucophage Retard* n'est pas
   proposé comme générique de *Glucophage*.
5. **Classe déduite** — quand la classe thérapeutique manque, elle est reprise des
   autres spécialités de même DCI (signalée « déduite »).

### Limites
* La base reflète les AMM publiées par l'ARP au moment de l'extraction ; une AMM ne
  signifie pas une disponibilité en officine.
* La libération modifiée est détectée à partir du libellé de forme et du nom ; quand
  aucun des deux ne l'indique, elle passe inaperçue : vérifiez la boîte.
""")
    st.caption(f"Source : {config.ARP_URL}")

st.markdown('<div class="pe-footer">PharmEquiv · projet open source · données publiques de '
            "l'Agence sénégalaise de Réglementation Pharmaceutique. Outil d'aide, ne remplace "
            "pas l'avis d'un professionnel de santé.</div>", unsafe_allow_html=True)
