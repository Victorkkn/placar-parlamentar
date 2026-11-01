import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { api, unwrap } from "../api/client";
import { FiltersForm } from "../components/FiltersForm";
import { LoadError, Loading, NotAvailable } from "../components/Status";
import { WindowSummary } from "../components/WindowSummary";
import { apiWindowParams, readFilters, useFilters } from "../lib/filters";
import { formatDecimal, formatInteger, formatPercent } from "../lib/format";
import { useMeta } from "../lib/useMeta";
import { text } from "../text/pt-BR";

const COUNT_METRICS = new Set(["bills_authored", "speeches"]);

function show(key: string, value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return COUNT_METRICS.has(key) ? formatDecimal(value) : formatPercent(value);
}

export function PartiesPage() {
  const meta = useMeta();
  const { params, update } = useFilters();
  const house = params.get("casa") === "SENADO" ? "SENADO" : "CAMARA";
  const query = { house, ...apiWindowParams(readFilters(params, meta.data), meta.data) };
  const result = useQuery({
    queryKey: ["parties", query],
    enabled: meta.isSuccess,
    queryFn: () => unwrap(api.GET("/api/parties", { params: { query } })),
  });
  const metricKeys = result.data?.parties[0]?.aggregates.map((a) => a.key) ?? [];

  return (
    <main>
      <h1>{text.parties.title}</h1>
      <label>
        {text.filters.house}{" "}
        <select value={house} onChange={(e) => update({ casa: e.target.value })}>
          <option value="CAMARA">{text.filters.houses.CAMARA}</option>
          <option value="SENADO">{text.filters.houses.SENADO}</option>
        </select>
      </label>
      <FiltersForm meta={meta.data} />
      {result.isLoading && <Loading />}
      {result.isError && <LoadError message={result.error.message} />}
      {result.data && (
        <>
          <WindowSummary window={result.data.window} threshold={result.data.threshold} />
          <p>{text.parties.aggregateNote}</p>
          <table>
            <thead>
              <tr>
                <th scope="col">{text.parties.columns.party}</th>
                <th scope="col">{text.parties.columns.inWindow}</th>
                <th scope="col">{text.parties.columns.atStart}</th>
                <th scope="col">{text.parties.columns.atEnd}</th>
                <th scope="col">{text.parties.columns.sufficient}</th>
                {metricKeys.map((k) => (
                  <th scope="col" key={k}>
                    {text.metrics[k] ?? k}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.data.parties.map((p) => (
                <tr key={p.party}>
                  <th scope="row">
                    {p.party}
                    {p.membership_changed && (
                      <div>
                        <small>{text.parties.changed}</small>
                      </div>
                    )}
                  </th>
                  <td>
                    {/* Party figures come from the listed members, each with official sources. */}
                    <Link to={`/comparar?ids=${p.member_ids.slice(0, 6).join(",")}&${params.toString()}`} data-testid="party-members">
                      {formatInteger(p.members_in_window)}
                    </Link>
                  </td>
                  <td>{formatInteger(p.members_at_start)}</td>
                  <td>{formatInteger(p.members_at_end)}</td>
                  <td>{formatInteger(p.members_with_sufficient_data)}</td>
                  {p.aggregates.map((a) => (
                    <td key={a.key}>
                      {!a.available ? <NotAvailable reason="not_loaded_yet" /> : a.members_counted === 0 ? "—" : `${show(a.key, a.median)} (${show(a.key, a.minimum)}–${show(a.key, a.maximum)})`}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </main>
  );
}
