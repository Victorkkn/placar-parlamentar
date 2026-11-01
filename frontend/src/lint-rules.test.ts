import { ESLint } from "eslint";
import { describe, expect, it } from "vitest";

// Proves the decision 0012 / 0009 lint bans are active (fails if the config stops enforcing them).
describe("lint rules", () => {
  const eslint = new ESLint();

  it("bans dangerouslySetInnerHTML", async () => {
    const code = "export const X = () => <div dangerouslySetInnerHTML={{ __html: 'x' }} />;\n";
    const [result] = await eslint.lintText(code, { filePath: "src/Probe.tsx" });
    expect(result?.messages.map((m) => m.message).join(" ")).toContain("banned");
  });

  it("bans visitor storage", async () => {
    const [result] = await eslint.lintText("localStorage.setItem('a', 'b');\n", {
      filePath: "src/probe.ts",
    });
    expect(result?.messages.some((m) => m.ruleId === "no-restricted-globals")).toBe(true);
  });
});
