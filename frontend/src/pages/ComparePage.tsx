import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "../api/client";
import { FiltersForm } from "../components/FiltersForm";
import { MetricValue } from "../components/MetricValue";
import { SourceValue } from "../components/SourceLinks";
import { LoadError, Loading } from "../components/Status";
import { WindowSummary } from "../components/WindowSummary";
import { apiWindowParams, readFilters, useFilters } from "../lib/filters";
import { formatInteger, formatPercent } from "../lib/format";
import { useMeta } from "../lib/useMeta";
import { text } from "../text/pt-BR";

export function ComparePage() {
  const meta = useMeta();
  const { params } = useFilters();
  const ids = (params.get("ids") ?? "").split(",").filter((x) => /^\d+$/.test(x));
  const query = { ids: ids.join(","), ...apiWindowParams(readFilters(params, meta.data), meta.data) };
  const result = useQuery({
    queryKey: ["compare", query],
    enabled: meta.isSuccess && ids.length >= 2,
    queryFn: () => unwrap(api.GET("/api/compare", { params: { query } })),
  });

  return (
    <main>
      <h1>{text.compare.title}</h1>
      {ids.length < 2 && <p>{text.compare.hint}</p>}
      {ids.length >= 2 && <FiltersForm meta={meta.data} />}
      {result.isLoading && <Loading />}
      {result.isError && <LoadError message={result.error.message} />}
      {result.data && (
        <>
          <WindowSummary window={result.data.window} threshold={result.data.threshold} />
          <table>
            <thead>
              <tr>
                <th scope="col">{text.compare.metric}</th>
                {result.data.officials.map((d) => (
                  <th scope="col" key={d.official.id}>
                    {d.official.name} ({d.official.party ?? "—"}/{d.official.state})
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">{text.official.coverage}</th>
                {result.data.officials.map((d) => (
                  <td key={d.official.id}>
                    <SourceValue sources={d.official.coverage.sources}>
                      {formatInteger(d.official.coverage.days_in_office)} ({formatPercent(d.official.coverage.share)})
                    </SourceValue>
                    {!d.official.sufficient && (
                      <div>
                        <strong>{text.insufficientData}</strong>
                      </div>
                    )}
                  </td>
                ))}
              </tr>
              {result.data.officials[0]?.metrics.map((m, index) => (
                <tr key={m.key}>
                  <th scope="row">{text.metrics[m.key] ?? m.key}</th>
                  {result.data.officials.map((d) => {
                    const metric = d.metrics[index];
                    return <td key={d.official.id}>{metric && <MetricValue metric={metric} />}</td>;
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </main>
  );
}
