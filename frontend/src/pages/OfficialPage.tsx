import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import { api, unwrap } from "../api/client";
import { FiltersForm } from "../components/FiltersForm";
import { MetricValue } from "../components/MetricValue";
import { SourceLinks, SourceValue } from "../components/SourceLinks";
import { LoadError, Loading } from "../components/Status";
import { WindowSummary } from "../components/WindowSummary";
import { apiWindowParams, readFilters, useFilters } from "../lib/filters";
import { formatDate, formatInteger, formatPercent } from "../lib/format";
import { useMeta } from "../lib/useMeta";
import { text } from "../text/pt-BR";

export function OfficialPage() {
  const { id } = useParams();
  const meta = useMeta();
  const { params } = useFilters();
  const query = apiWindowParams(readFilters(params, meta.data), meta.data);
  const official_id = Number(id);
  const detail = useQuery({
    queryKey: ["official", official_id, query],
    enabled: meta.isSuccess && Number.isInteger(official_id) && official_id > 0,
    queryFn: () => unwrap(api.GET("/api/officials/{official_id}", { params: { path: { official_id }, query } })),
  });

  if (detail.isLoading || meta.isLoading) return <Loading />;
  if (detail.isError) return <LoadError message={detail.error.message} />;
  if (!detail.data) return <LoadError />;
  const { official, periods, affiliations, metrics, window, threshold } = detail.data;

  return (
    <main>
      <h1>
        {official.name} <SourceLinks sources={official.sources} />
      </h1>
      <p>
        {text.filters.houses[official.house] ?? official.house} · {official.state} · {official.party ?? "—"}
      </p>
      <FiltersForm meta={meta.data} />
      <WindowSummary window={window} threshold={threshold} />
      <h2>{text.official.coverage}</h2>
      <p>
        <SourceValue sources={official.coverage.sources}>
          {text.official.days(formatInteger(official.coverage.days_in_office), formatInteger(official.coverage.window_days))} ({formatPercent(official.coverage.share)})
        </SourceValue>
      </p>
      {!official.sufficient && (
        <p role="note">
          <strong>{text.insufficientData}.</strong> {text.official.insufficientNote}
        </p>
      )}
      <h2>{text.official.metrics}</h2>
      <table>
        <tbody>
          {metrics.map((m) => (
            <tr key={m.key}>
              <th scope="row">{text.metrics[m.key] ?? m.key}</th>
              <td>
                <MetricValue metric={m} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2>{text.official.periods}</h2>
      <table>
        <thead>
          <tr>
            <th scope="col">{text.official.from}</th>
            <th scope="col">{text.official.to}</th>
            <th scope="col">{text.official.startReason}</th>
            <th scope="col">{text.official.endReason}</th>
          </tr>
        </thead>
        <tbody>
          {periods.map((p) => (
            <tr key={`${p.start}-${p.end ?? "open"}`}>
              <td>
                <SourceValue sources={p.sources}>{formatDate(p.start)}</SourceValue>
              </td>
              <td>{p.end ? formatDate(p.end) : text.official.ongoing}</td>
              <td>{text.reasons[p.start_reason] ?? p.start_reason}</td>
              <td>{text.reasons[p.end_reason] ?? p.end_reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2>{text.official.affiliations}</h2>
      <ul>
        {affiliations.map((a) => (
          <li key={`${a.party}-${a.start}`}>
            <SourceValue sources={a.sources}>
              {a.party}: {formatDate(a.start)} – {a.end ? formatDate(a.end) : text.official.ongoing}
            </SourceValue>
            {a.precision === "AT_EVENT" && <small> ({text.official.precisionAtEvent})</small>}
          </li>
        ))}
      </ul>
    </main>
  );
}
