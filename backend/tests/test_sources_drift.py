"""Structure comparison on SYNTHETIC bodies (decision 0011, item 6)."""

from placar.sources.drift import compare, shape


def test_shape_merges_list_items():
    assert shape({"dados": [{"id": 1}, {"id": 2, "nome": "x"}]}) == {
        "dados",
        "dados[].id",
        "dados[].nome",
    }


def test_compare_reports_added_and_removed_fields():
    drift = compare("case", {"dados": [{"id": 1, "old": 1}]}, {"dados": [{"id": 1, "new": 2}]})
    assert drift.changed
    assert drift.added == ["dados.new"] and drift.removed == ["dados.old"]


def test_single_object_vs_list_is_not_a_change():
    one = {"A": {"Item": {"Codigo": "1"}}}
    many = {"A": {"Item": [{"Codigo": "1"}, {"Codigo": "2"}]}}
    assert not compare("case", one, many).changed


def test_values_are_ignored():
    assert not compare("case", {"a": 1}, {"a": 2}).changed
