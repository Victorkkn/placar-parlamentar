"""Reviewed mapping of Câmara history texts (`descricaoStatus`) to their effect (Phase B, B1.2).

Built from the 64 distinct texts in the cache on 2026-11-01. A text may join several parts with
" / "; each part is read on its own.

Rules:
- Only parts listed in ENTRY, ENTRY_DECISIONS, EXIT or EXIT_DECISIONS open or close a period.
- A part that starts with "Entrada -" or "Saída -" but is not listed is UNKNOWN: logged, never
  guessed, and it does not change any period.
- Other parts (DIVERSO notes, name changes, office letters) do not affect periods in office.
- The date of a "Saída" is the last day in office (end-of-legislature exits are stamped 23:59 on
  the last day; data issue 12).
"""

from __future__ import annotations

from dataclasses import dataclass

from placar.legislators.models import EndReason, EventKind, StartReason

ENTRY: dict[str, str] = {
    "Entrada - Posse de Eleito Titular - Posse na Sessão Preparatória": StartReason.ELECTED_OATH,
    "Entrada - Posse de Eleito Titular - Posse Individual do Eleito": StartReason.ELECTED_OATH,
    "Entrada - Posse de Suplente - Posse como Suplente": StartReason.ALTERNATE_OATH,
    "Entrada - Posse de Suplente - Posse como Titular": StartReason.ALTERNATE_AS_TITULAR,
    "Entrada - Reassunção": StartReason.RETURN,
}

EXIT: dict[str, str] = {
    "Saída - Afastamento definitivo - Término da Legislatura": EndReason.TERM_END,
    "Saída - Afastamento definitivo - Renúncia": EndReason.RESIGNATION,
    "Saída - Afastamento definitivo - Falecimento": EndReason.DEATH,
    "Saída - Afastamento definitivo - Perda de Mandato por Ato da Mesa": EndReason.LOSS_OF_MANDATE,
    "Saída - Afastamento com prazo determinado - Licença para Tratamento de Saúde": EndReason.LEAVE,
    "Saída - Afastamento com prazo determinado - Licença para Tratar de Interesse Particular": (
        EndReason.LEAVE
    ),
    "Saída - Afastamento com prazo determinado - Afastamento Conjunto Consecutivo": (
        EndReason.OTHER_ABSENCE
    ),
    "Saída - Afastamento com prazo determinado - Suspensão": EndReason.SUSPENSION,
    "Saída - Afastamento sem prazo determinado - Afastamento de Suplente (automático)": (
        EndReason.TITULAR_RETURNED
    ),
    "Saída - Afastamento sem prazo determinado - Afastamento por Decisão Judicial": (
        EndReason.COURT_DECISION
    ),
    "Saída - Afastamento sem prazo determinado - Afastamento por Decisão da Presidência sem "
    "Convocação de Suplente": EndReason.OTHER_ABSENCE,
    "Saída - Afastamento sem prazo determinado - Ministro de Estado": EndReason.EXECUTIVE_OFFICE,
    "Saída - Afastamento sem prazo determinado - Secretário de Estado": EndReason.EXECUTIVE_OFFICE,
    "Saída - Afastamento sem prazo determinado - Secretário de Prefeitura de Capital": (
        EndReason.EXECUTIVE_OFFICE
    ),
}

# "Decisão da Mesa" notes that remove a titular. The Câmara records these only as DIVERSO
# notes (no "Saída" event follows; the situation becomes SUPLENCIA), so they are read as exits.
# Added 2026-11-01 after checking every occurrence in the cache (data issue 14).
EXIT_DECISIONS: dict[str, str] = {
    "DIVERSO - Decisão da Mesa - Afastamento de titular  por Recontagem de Votos": (
        EndReason.RECOUNT
    ),
    "DIVERSO - Decisão da Mesa - Torna-se suplente por retotalização": EndReason.RECOUNT,
}

# "Decisão da Mesa" notes that put someone into office without an "Entrada" event (the situation
# becomes Exercício). Added 2026-11-01 after checking every occurrence in the cache (data issue 14).
ENTRY_DECISIONS: dict[str, str] = {
    "DIVERSO - Decisão da Mesa - Restabelecimento ao mandato na condição de titular": (
        StartReason.MESA_DECISION
    ),
    "DIVERSO - Decisão da Mesa - Torna-se titular por Retotalização": StartReason.MESA_DECISION,
}

PARTY_CHANGE = "Alteração de partido"
START_OF_LEGISLATURE = {"Nome no início da legislatura", "Partido no início da legislatura"}


@dataclass(frozen=True)
class Reading:
    kind: str
    start_reason: str | None = None
    end_reason: str | None = None
    matched_text: str = ""
    unknown_part: str | None = None


def read_status(text: str | None) -> Reading:
    parts = [p.strip() for p in (text or "").split(" / ") if p.strip()]
    entries = [p for p in parts if p in ENTRY or p in ENTRY_DECISIONS]
    exits = [p for p in parts if p in EXIT or p in EXIT_DECISIONS]
    unknown = [p for p in parts if p.startswith(("Entrada -", "Saída -")) and p not in ENTRY | EXIT]
    if unknown or (entries and exits):
        return Reading(kind=EventKind.UNKNOWN, unknown_part=(unknown or [text or ""])[0])
    if entries:
        reason = ENTRY.get(entries[0]) or ENTRY_DECISIONS[entries[0]]
        return Reading(EventKind.ENTRY, start_reason=reason, matched_text=entries[0])
    if exits:
        reason = EXIT.get(exits[0]) or EXIT_DECISIONS[exits[0]]
        return Reading(EventKind.EXIT, end_reason=reason, matched_text=exits[0])
    if PARTY_CHANGE in parts:
        return Reading(EventKind.PARTY, matched_text=PARTY_CHANGE)
    if parts and set(parts) <= START_OF_LEGISLATURE:
        return Reading(EventKind.START_OF_LEGISLATURE)
    return Reading(EventKind.OTHER)
