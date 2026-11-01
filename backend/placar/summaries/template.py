"""Template summary: fixed pt-BR sentences filled from the fact sheet (decision 0010, item 9).

Wording owned by the technical writer and reviewed by the owner (Phase D, task D8). Every
sentence cites the facts its values come from, so it passes the same validator as model drafts.
"""

from __future__ import annotations

from .facts import ATTENDANCE, BILLS, COVERAGE, OFFICIAL, SPEECHES, VOTES, FactSheet
from .validator import Sentence


def _rate(values) -> str:
    rate = values.get("por_365_dias_no_cargo")
    return f", ou {rate} por 365 dias no cargo" if rate else ""


def template_summary(sheet: FactSheet) -> list[Sentence]:
    facts = sheet.by_id()
    who, cov = facts[OFFICIAL].values, facts[COVERAGE].values
    lead = (
        f"Entre {cov['inicio_periodo']} e {cov['fim_periodo']}, "
        f"{who['nome']} ({who['casa']}, {who['uf']})"
    )
    if sheet.days_in_office == 0:
        text = f"{lead} não esteve no exercício do cargo, segundo os registros oficiais."
        return [Sentence(text, (OFFICIAL, COVERAGE))]
    sentences = [
        Sentence(
            f"{lead} esteve no cargo em {cov['dias_no_cargo']} de {cov['dias_no_periodo']} dias "
            f"({cov['proporcao']}).",
            (OFFICIAL, COVERAGE),
        )
    ]
    parties = [f for f in sheet.facts if f.type == "filiacao_partidaria"]
    if len(parties) == 1:
        sentences.append(
            Sentence(f"Partido no período: {parties[0].values['partido']}.", (parties[0].id,))
        )
    elif parties:
        names = ", ".join(p.values["partido"] for p in parties)
        sentences.append(
            Sentence(f"Partidos no período, em ordem: {names}.", tuple(p.id for p in parties))
        )

    if ATTENDANCE in facts:
        v = facts[ATTENDANCE].values
        text = (
            f"Sessões deliberativas do Plenário nos dias no cargo: {v['sessoes_nos_dias_no_cargo']}"
        )
        if v["sessoes_nos_dias_no_cargo"] != "0":
            text += f"; com presença registrada: {v['sessoes_com_presenca']} ({v['proporcao']})"
        if v["dias_de_licenca"] != "0":
            text += f"; dias de licença no período: {v['dias_de_licenca']}"
        sentences.append(Sentence(text + ".", (ATTENDANCE, COVERAGE)))
    if BILLS in facts:
        v = facts[BILLS].values
        sentences.append(
            Sentence(
                "Proposições apresentadas (PL, PLP, PEC, PDL), inclusive em coautoria: "
                f"{v['total']}{_rate(v)}.",
                (BILLS, COVERAGE),
            )
        )
    if VOTES in facts:
        v = facts[VOTES].values
        text = (
            "Votações nominais nos dias no cargo, sem contar as presididas: "
            f"{v['votacoes_nos_dias_no_cargo']}"
        )
        if v["votacoes_nos_dias_no_cargo"] != "0":
            text += f"; com voto registrado: {v['votacoes_com_voto']} ({v['proporcao']})"
        if v["votacoes_presididas"] != "0":
            text += f"; presididas: {v['votacoes_presididas']}"
        sentences.append(Sentence(text + ".", (VOTES, COVERAGE)))
    if SPEECHES in facts:
        v = facts[SPEECHES].values
        text = f"Discursos registrados nos dias no cargo: {v['total']}{_rate(v)}."
        sentences.append(Sentence(text, (SPEECHES, COVERAGE)))
    return sentences
