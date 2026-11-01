import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { api, unwrap } from "../api/client";
import { FiltersForm } from "../components/FiltersForm";
import { SourceValue } from "../components/SourceLinks";
import { LoadError, Loading } from "../components/Status";
import { WindowSummary } from "../components/WindowSummary";
import { apiWindowParams, readFilters, useFilters } from "../lib/filters";
import { formatInteger, formatPercent } from "../lib/format";
import { useMeta } from "../lib/useMeta";
import { text } from "../text/pt-BR";

const MAX_COMPARE = 6;

export function OfficialsPage() {
  const meta = useMeta();
  const { params, update } = useFilters();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<number[]>([]);
  const filters = readFilters(params, meta.data);
  const page = Number(params.get("pagina") ?? "1") || 1;
  const query = {
    ...apiWindowParams(filters, meta.data),
    ...(params.get("casa") ? { house: params.get("casa")! } : {}),
    ...(params.get("uf") ? { state: params.get("uf")! } : {}),
    ...(params.get("partido") ? { party: params.get("partido")! } : {}),
    ...(params.get("busca") ? { q: params.get("busca")! } : {}),
    page,
    page_size: 50,
  };
  const officials = useQuery({
    queryKey: ["officials", query],
    enabled: meta.isSuccess,
    queryFn: () => unwrap(api.GET("/api/officials", { params: { query } })),
  });

  const toggle = (id: number) =>
    setSelected((current) => (current.includes(id) ? current.filter((x) => x !== id) : current.length < MAX_COMPARE ? [...current, id] : current));

  return (
    <main>
      <h1>{text.officials.title}</h1>
      <FiltersForm meta={meta.data} showOfficialFilters />
      {officials.isLoading && <Loading />}
      {officials.isError && <LoadError message={officials.error.message} />}
      {officials.data && (
        <>
          <WindowSummary window={officials.data.window} threshold={officials.data.threshold} />
          <p>{text.officials.total(officials.data.total)}</p>
          <button type="button" disabled={selected.length < 2} onClick={() => navigate(`/comparar?ids=${selected.join(",")}&${params.toString()}`)}>
            {text.officials.compareSelected} ({selected.length})
          </button>
          <table>
            <thead>
              <tr>
                <th scope="col" />
                <th scope="col">{text.officials.columns.name}</th>
                <th scope="col">{text.officials.columns.house}</th>
                <th scope="col">{text.officials.columns.state}</th>
                <th scope="col">{text.officials.columns.party}</th>
                <th scope="col">{text.officials.columns.days}</th>
                <th scope="col">{text.officials.columns.share}</th>
                <th scope="col">{text.officials.columns.status}</th>
              </tr>
            </thead>
            <tbody>
              {officials.data.items.map((o) => (
                <tr key={o.id}>
                  <td>
                    <input type="checkbox" aria-label={text.officials.select(o.name)} checked={selected.includes(o.id)} onChange={() => toggle(o.id)} />
                  </td>
                  <td>
                    <Link to={`/parlamentar/${o.id}?${params.toString()}`}>{o.name}</Link> <SourceValue sources={o.sources}>{""}</SourceValue>
                  </td>
                  <td>{text.filters.houses[o.house] ?? o.house}</td>
                  <td>{o.state}</td>
                  <td>{o.party ?? "—"}</td>
                  <td>
                    <SourceValue sources={o.coverage.sources}>{formatInteger(o.coverage.days_in_office)}</SourceValue>
                  </td>
                  <td>{formatPercent(o.coverage.share)}</td>
                  <td>{o.sufficient ? text.officials.sufficient : <strong>{text.insufficientData}</strong>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {officials.data.not_in_office > 0 && <p>{text.officials.notInOffice(officials.data.not_in_office)}</p>}
          <nav aria-label="Paginação">
            <button type="button" disabled={page <= 1} onClick={() => update({ pagina: String(page - 1) })}>
              {text.officials.previous}
            </button>{" "}
            <button type="button" disabled={page * officials.data.page_size >= officials.data.total} onClick={() => update({ pagina: String(page + 1) })}>
              {text.officials.next}
            </button>
          </nav>
        </>
      )}
    </main>
  );
}
