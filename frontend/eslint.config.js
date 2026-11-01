// Lint rules (decisions 0009 and 0012). Built-in rules plus typescript-eslint; no React plugin
// is needed for the one React-specific ban below.
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules", "src/api/schema.d.ts"] },
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      // Decision 0012: text from official APIs is untrusted; never inject raw HTML.
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']",
          message: "dangerouslySetInnerHTML is banned (decision 0012).",
        },
      ],
      "no-restricted-globals": [
        "error",
        { name: "localStorage", message: "No visitor storage (decision 0009, item 5)." },
        { name: "sessionStorage", message: "No visitor storage (decision 0009, item 5)." },
      ],
    },
  },
);
