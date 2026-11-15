"""Fragments HTML réutilisables (toutes les valeurs sont échappées)."""

from __future__ import annotations

from html import escape

import pandas as pd

from pharmequiv.ui.theme import LEVEL_COLORS


def _e(value) -> str:
    return escape("" if value is None else str(value))


def brand(source_url: str) -> str:
    return (
        '<div class="pe-brand"><div class="pe-cross" aria-hidden="true"></div>'
        '<span class="pe-brand-name">PharmEquiv</span>'
        f'<span class="pe-brand-src">d\'après la base AMM de '
        f'<a href="{_e(source_url)}" target="_blank">l\'ARP Sénégal</a></span></div>'
    )


def hero() -> str:
    return (
        '<div class="pe-hero"><span class="pe-eyebrow">Base AMM officielle · Sénégal</span>'
        '<h1>Trouvez le générique disponible au Sénégal.</h1>'
        '<p>Tapez un nom de marque ou une molécule. PharmEquiv retrouve les spécialités '
        'autorisées qui contiennent la même substance, au même dosage et sous la même forme, '
        'puis les alternatives de la même classe thérapeutique.</p></div>'
    )


def figures(stats: dict[str, int]) -> str:
    items = [
        (stats["specialites"], "spécialités autorisées"),
        (stats["dci"], "molécules ou associations"),
        (stats["laboratoires"], "laboratoires"),
        (stats["specialites_substituables"], "spécialités ayant au moins un générique"),
    ]
    inner = "".join(f"<span><b>{n:,}</b>{_e(lbl)}</span>".replace(",", " ") for n, lbl in items)
    return f'<div class="pe-figures">{inner}</div>'


def med_label(row: pd.Series, level: str = "ref", reference: bool = False) -> str:
    color = LEVEL_COLORS[level]
    classe = row["classe"] + (" (déduite)" if bool(row.get("classe_inferee")) else "")
    cls = "pe-label pe-ref" if reference else "pe-label"
    return (
        f'<div class="{cls}" style="--band:{color}">'
        f'<div><span class="nom">{_e(row["nom"])}</span>'
        f'<span class="pe-dose">{_e(row["dosage"])}</span></div>'
        f'<div class="dci">{_e(row["molecules"].replace(" | ", " + "))}</div>'
        f'<div class="meta">{_e(row["forme"])} · voie {_e(row["voie_norm"].lower())} · '
        f'{_e(row["presentation"])} · {_e(row["laboratoire"])}</div>'
        f'<div class="meta">{_e(classe)}</div></div>'
    )


def ladder(n_strict: int, n_molecule: int, n_alt: int) -> str:
    rungs = [
        ("strict", n_strict, "Génériques stricts", "même molécule, même dosage, même forme"),
        ("molecule", n_molecule, "Même molécule", "autre dosage ou autre forme"),
        ("alternative", n_alt, "Alternatives", "autres molécules de la même classe"),
    ]
    inner = "".join(
        f'<div class="pe-rung{" is-empty" if n == 0 else ""}" style="--c:{LEVEL_COLORS[k]}"><b>{n}</b>'
        f'<span>{_e(title)}</span><small>{_e(sub)}</small></div>'
        for k, n, title, sub in rungs
    )
    return f'<div class="pe-ladder">{inner}</div>'


def section(level: str, title: str, subtitle: str) -> str:
    return (f'<div class="pe-section"><span class="pe-dot" style="--c:{LEVEL_COLORS[level]}"></span>'
            f'<h3>{_e(title)}</h3><p>{_e(subtitle)}</p></div>')


def empty(message: str) -> str:
    return f'<div class="pe-empty">{_e(message)}</div>'


def note(message_html: str) -> str:
    return f'<div class="pe-note">{message_html}</div>'


def chips(values: list[str]) -> str:
    return '<div class="pe-chips">' + "".join(
        f'<span class="pe-chip">{_e(v)}</span>' for v in values) + "</div>"


def alternative(molecule: str, count: int, examples: str, formes: str) -> str:
    return (f'<div class="pe-alt"><div><span class="mol">{_e(molecule)}</span>'
            f'<span class="count">{count} spécialité{"s" if count > 1 else ""}</span></div>'
            f'<div class="ex">ex. {_e(examples)} · {_e(formes)}</div></div>')
