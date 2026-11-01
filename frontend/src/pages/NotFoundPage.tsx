import { Link } from "react-router";

import { text } from "../text/pt-BR";

export function NotFoundPage() {
  return (
    <main>
      <h1>{text.notFoundTitle}</h1>
      <Link to="/">{text.backHome}</Link>
    </main>
  );
}
