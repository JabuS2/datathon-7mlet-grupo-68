import { describe, expect, it } from "vitest";

import { buildSqlResultsHtml, type SqlResultsData } from "./sqlResults.js";

const baseData: SqlResultsData = {
  database: "api_service",
  question: "how many clientes are active?",
  sql: "select count(*) from clientes where ind_ativo = true",
  columns: ["count"],
  rows: [[42]],
  rowCap: 200,
};

describe("buildSqlResultsHtml", () => {
  it("renders the question, sql and result rows", () => {
    const html = buildSqlResultsHtml(baseData);
    expect(html).toContain("how many clientes are active?");
    expect(html).toContain("select count(*) from clientes");
    expect(html).toContain("42");
  });

  it("renders null cells distinctly instead of the literal word from data", () => {
    const html = buildSqlResultsHtml({ ...baseData, columns: ["x"], rows: [[null]] });
    expect(html).toContain('<span class="null">null</span>');
  });

  it("shows a truncation note only when the row count hits the cap", () => {
    const truncated = buildSqlResultsHtml({ ...baseData, rows: [[1]], rowCap: 1 });
    expect(truncated).toContain("truncated");

    const notTruncated = buildSqlResultsHtml({ ...baseData, rows: [[1]], rowCap: 200 });
    expect(notTruncated).not.toContain("truncated");
  });

  it("escapes SQL/question text that could break out of the HTML", () => {
    const html = buildSqlResultsHtml({
      ...baseData,
      question: "<img src=x onerror=alert(1)>",
      sql: "select '<script>evil()</script>'",
    });
    expect(html).not.toContain("<img src=x onerror=alert(1)>");
    expect(html).not.toContain("<script>evil()</script>");
  });

  it("is a self-contained HTML document with no external resource references", () => {
    const html = buildSqlResultsHtml(baseData);
    expect(html).toMatch(/^<!doctype html>/i);
    expect(html).not.toMatch(/https?:\/\//);
  });
});
