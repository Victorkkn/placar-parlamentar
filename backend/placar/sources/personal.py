"""Personal and contact fields removed from official responses (decisions 0008 and 0019).

Removed before a response is written to the raw cache and again when fixtures are recorded,
so neither the local cache nor git holds them. No parser reads any of these fields.
"""

from __future__ import annotations

from typing import Any

# Keys removed anywhere in a response (compared case-insensitively). These are personal or
# contact fields outside the project's scope (decisions 0008 and 0019).
PERSONAL_KEYS = frozenset(
    key.lower()
    for key in (
        "cpf",
        "dataNascimento",
        "dataFalecimento",
        "municipioNascimento",
        "ufNascimento",
        "escolaridade",
        "redeSocial",
        "email",
        "EmailParlamentar",
        "sexo",
        "SexoParlamentar",
        "Telefones",
        "telefone",
        "EnderecoParlamentar",
        "endereco",
    )
)


def strip_personal(data: Any, path: str = "") -> tuple[Any, list[str]]:
    """Return a copy without personal keys, and the paths that were removed."""
    removed: list[str] = []
    if isinstance(data, dict):
        clean = {}
        for key, value in data.items():
            here = f"{path}.{key}" if path else key
            if key.lower() in PERSONAL_KEYS:
                removed.append(here)
                continue
            clean[key], inner = strip_personal(value, here)
            removed.extend(inner)
        return clean, removed
    if isinstance(data, list):
        clean_list = []
        for index, value in enumerate(data):
            item, inner = strip_personal(value, f"{path}[{index}]")
            clean_list.append(item)
            removed.extend(inner)
        return clean_list, removed
    return data, removed


def find_personal_keys(data: Any, path: str = "") -> list[str]:
    return strip_personal(data, path)[1]
