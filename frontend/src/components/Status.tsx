import { text } from "../text/pt-BR";

export function Loading() {
  return <p role="status">{text.loading}</p>;
}

export function LoadError({ message }: { message?: string }) {
  return <p role="alert">{message ?? text.loadError}</p>;
}

export function NotAvailable({ reason }: { reason?: string | null }) {
  return <span className="not-available">{reason === "not_in_official_data" ? text.notInOfficialData : text.notAvailableYet}</span>;
}
