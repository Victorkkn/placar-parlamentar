import { text } from "../text/pt-BR";

export function HomePage() {
  return (
    <main>
      <h1>{text.appName}</h1>
      <p>{text.tagline}</p>
      <p>{text.notAvailableYet}</p>
    </main>
  );
}
