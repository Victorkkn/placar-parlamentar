import { Link } from "react-router";

import type { Schemas } from "../api/client";
import { text } from "../text/pt-BR";
import { SourceValue } from "./SourceLinks";

/** Automatic summary (decision 0010): each sentence with the sources of its facts. */
export function SummarySection({ summary }: { summary: Schemas["SummaryOut"] }) {
  if (summary.sentences.length === 0) return null;
  return (
    <section aria-labelledby="summary-title" data-testid="summary">
      <h2 id="summary-title">{text.summary.title}</h2>
      <p role="note">
        {summary.kind === "model" ? text.summary.model : text.summary.template}{" "}
        <Link to="/metodologia#resumos">{text.summary.howItIsMade}</Link>
      </p>
      <ul>
        {summary.sentences.map((sentence, index) => (
          <li key={index}>
            <SourceValue sources={sentence.sources}>{sentence.text}</SourceValue>
          </li>
        ))}
      </ul>
    </section>
  );
}
