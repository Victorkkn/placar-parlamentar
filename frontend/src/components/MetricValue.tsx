import type { Metric } from "../api/client";
import { formatDecimal, formatInteger, formatPercent } from "../lib/format";
import { text } from "../text/pt-BR";
import { SourceValue } from "./SourceLinks";
import { NotAvailable } from "./Status";

export function MetricValue({ metric }: { metric: Metric }) {
  if (!metric.available) return <NotAvailable reason={metric.reason} />;
  const n = metric.numerator ?? 0;
  const details = metric.details as Record<string, unknown>;
  let main: string;
  if (metric.denominator === null || metric.denominator === undefined) {
    main = text.metricValue.count(formatInteger(n));
  } else if (metric.denominator === 0) {
    main = text.metricValue.noneInPeriod;
  } else {
    main = text.metricValue.ratio(formatPercent(metric.value ?? 0), formatInteger(n), formatInteger(metric.denominator));
  }
  return (
    <div>
      <SourceValue sources={metric.sources}>{main}</SourceValue>
      {metric.per_365_days_in_office !== null && metric.per_365_days_in_office !== undefined && (
        <div>{text.metricValue.perYear(formatDecimal(metric.per_365_days_in_office))}</div>
      )}
      {typeof details.leave_days === "number" && <div>{text.metricValue.leaveDays(formatInteger(details.leave_days))}</div>}
      {typeof details.presided_excluded === "number" && details.presided_excluded > 0 && (
        <div>{text.metricValue.presidedExcluded(formatInteger(details.presided_excluded))}</div>
      )}
    </div>
  );
}
