import type { Schemas } from "../api/client";
import { readFilters, useFilters, type Preset, type ThresholdMode } from "../lib/filters";
import { text } from "../text/pt-BR";

export function FiltersForm({ meta, showOfficialFilters = false }: { meta?: Schemas["MetaOut"]; showOfficialFilters?: boolean }) {
  const { params, update } = useFilters();
  const filters = readFilters(params, meta);
  return (
    <form
      aria-label="Filtros"
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        const value = (name: string) => (data.get(name) as string | null) ?? undefined;
        update({
          periodo: value("periodo"),
          inicio: value("periodo") === "personalizado" ? value("inicio") : undefined,
          fim: value("periodo") === "personalizado" ? value("fim") : undefined,
          modo: value("modo"),
          minimo: value("minimo"),
          ...(showOfficialFilters ? { casa: value("casa"), uf: value("uf"), partido: value("partido"), busca: value("busca") } : {}),
        });
      }}
    >
      <fieldset>
        <legend>{text.filters.period}</legend>
        <label>
          {text.filters.period}{" "}
          <select name="periodo" defaultValue={filters.preset}>
            {(Object.keys(text.filters.presets) as Preset[]).map((p) => (
              <option key={p} value={p}>
                {text.filters.presets[p]}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          {text.filters.start} <input type="date" name="inicio" defaultValue={filters.start} min={meta?.earliest_date} max={meta?.snapshot_date ?? undefined} />
        </label>{" "}
        <label>
          {text.filters.end} <input type="date" name="fim" defaultValue={filters.end} min={meta?.earliest_date} max={meta?.snapshot_date ?? undefined} />
        </label>
      </fieldset>
      <fieldset>
        <legend>{text.filters.threshold}</legend>
        <label>
          {text.filters.threshold} <input type="number" name="minimo" min={0} step={1} defaultValue={filters.minimum} />
        </label>{" "}
        <select name="modo" aria-label={text.filters.threshold} defaultValue={filters.mode}>
          {(Object.keys(text.filters.mode) as ThresholdMode[]).map((m) => (
            <option key={m} value={m}>
              {text.filters.mode[m]}
            </option>
          ))}
        </select>
      </fieldset>
      {showOfficialFilters && (
        <fieldset>
          <label>
            {text.filters.house}{" "}
            <select name="casa" defaultValue={params.get("casa") ?? ""}>
              <option value="">{text.filters.allHouses}</option>
              <option value="CAMARA">{text.filters.houses.CAMARA}</option>
              <option value="SENADO">{text.filters.houses.SENADO}</option>
            </select>
          </label>{" "}
          <label>
            {text.filters.state} <input name="uf" maxLength={2} size={3} defaultValue={params.get("uf") ?? ""} />
          </label>{" "}
          <label>
            {text.filters.party} <input name="partido" maxLength={40} size={10} defaultValue={params.get("partido") ?? ""} />
          </label>{" "}
          <label>
            {text.filters.search} <input name="busca" maxLength={100} defaultValue={params.get("busca") ?? ""} />
          </label>
        </fieldset>
      )}
      <button type="submit">{text.filters.apply}</button>
    </form>
  );
}
