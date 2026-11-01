import type { Source } from "../api/client";
import { text } from "../text/pt-BR";

const SHOWN = 3;

function href(source: Source): string {
  return source.public_url ?? source.api_url;
}

/** Links to the official records behind a number (rule 3). */
export function SourceLinks({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;
  const first = sources.slice(0, SHOWN);
  const rest = sources.slice(SHOWN);
  return (
    <span className="sources">
      {first.map((source, index) => (
        <a key={`${source.api_url}-${index}`} href={href(source)} target="_blank" rel="noopener noreferrer" title={source.label || source.api_url}>
          {text.sourceShort}
          {sources.length > 1 ? ` ${index + 1}` : ""}
        </a>
      ))}
      {rest.length > 0 && (
        <details>
          <summary>{text.moreSources(rest.length)}</summary>
          <ul>
            {rest.map((source, index) => (
              <li key={`${source.api_url}-${index + SHOWN}`}>
                <a href={href(source)} target="_blank" rel="noopener noreferrer">
                  {source.label || source.api_url}
                </a>
              </li>
            ))}
          </ul>
        </details>
      )}
    </span>
  );
}

/** Every number on screen goes through this component (decision 0009, item 12). */
export function SourceValue({ children, sources }: { children: React.ReactNode; sources: Source[] }) {
  return (
    <span data-testid="sourced-value">
      {children} <SourceLinks sources={sources} />
    </span>
  );
}
