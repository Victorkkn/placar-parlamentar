import type { Schemas } from "../api/client";
import { formatDate, formatInteger, formatPercent } from "../lib/format";
import { text } from "../text/pt-BR";

/** The effective window and threshold, shown at the top of every comparison. */
export function WindowSummary({ window, threshold }: { window: Schemas["Window"]; threshold: Schemas["Threshold"] }) {
  return (
    <p data-testid="window-summary">
      {text.window(formatDate(window.start), formatDate(window.end), formatInteger(window.days))}{" "}
      {threshold.min_days !== null && threshold.min_days !== undefined
        ? text.thresholdDays(formatInteger(threshold.min_days))
        : text.thresholdShare(formatPercent(threshold.min_share ?? 0))}
    </p>
  );
}
