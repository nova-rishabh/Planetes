/** Parse the results table in docs/VALIDATION.md (the single source of truth for the Validation page). */

export type ValidationRow = {
  id: string;
  test: string;
  result: string;
  pass: string;
  evidence: string;
};

export type ValidationState = "pass" | "fail" | "cut" | "pending";

export function parseValidation(markdown: string): ValidationRow[] {
  return markdown
    .split(/\r?\n/)
    .filter((line) => /^\|\s*V\d+\s*\|/.test(line))
    .map((line) => {
      const cells = line.split("|").slice(1, -1).map((c) => c.trim());
      const [id = "", test = "", result = "", pass = "", evidence = ""] = cells;
      return { id, test, result, pass, evidence };
    });
}

export function stateOf(row: ValidationRow): ValidationState {
  const p = row.pass.toLowerCase();
  if (p.includes("pass")) return "pass";
  if (p.includes("fail")) return "fail";
  if (row.result.toLowerCase() === "cut") return "cut";
  return "pending";
}

/** Markdown code spans and emphasis to plain text, for display. */
export function plain(text: string): string {
  return text.replace(/`([^`]*)`/g, "$1").replace(/\*\*([^*]*)\*\*/g, "$1").replace(/[✅❌]\s*/g, "");
}
