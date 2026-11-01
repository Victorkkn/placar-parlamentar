import { text } from "../text/pt-BR";

export function MethodologyPage() {
  return (
    <main>
      <h1>{text.methodology.title}</h1>
      <p>{text.methodology.intro}</p>
      <ul>
        {text.methodology.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <h2 id="resumos">{text.methodology.summariesTitle}</h2>
      {text.methodology.summaries.map((item) => (
        <p key={item}>{item}</p>
      ))}
    </main>
  );
}
