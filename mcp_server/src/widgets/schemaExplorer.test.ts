import { describe, expect, it } from "vitest";

import { buildSchemaExplorerHtml, type DatabaseSchema } from "./schemaExplorer.js";

describe("buildSchemaExplorerHtml", () => {
  const schemas: DatabaseSchema[] = [
    {
      database: "api_service",
      tables: [
        {
          name: "clientes",
          columns: [
            { name: "cod_cliente", dataType: "bigint", nullable: false, isPrimaryKey: true },
            { name: "idade", dataType: "integer", nullable: false, isPrimaryKey: false },
          ],
        },
      ],
      foreignKeys: [],
    },
    {
      database: "model_service",
      tables: [
        {
          name: "politicas",
          columns: [
            { name: "policy_id", dataType: "character varying", nullable: false, isPrimaryKey: true },
          ],
        },
      ],
      foreignKeys: [
        {
          sourceTable: "ciclos_retreino",
          sourceColumn: "policy_id",
          targetTable: "politicas",
          targetColumn: "policy_id",
        },
      ],
    },
  ];

  it("includes every table name and column name", () => {
    const html = buildSchemaExplorerHtml(schemas);
    expect(html).toContain("clientes");
    expect(html).toContain("cod_cliente");
    expect(html).toContain("politicas");
    expect(html).toContain("policy_id");
  });

  it("marks primary key columns with a PK badge", () => {
    const html = buildSchemaExplorerHtml(schemas);
    expect(html).toContain('<span class="badge pk">PK</span>');
  });

  it("escapes table/column names that could break out of the HTML", () => {
    const malicious: DatabaseSchema[] = [
      {
        database: "api_service",
        tables: [
          {
            name: '<script>alert(1)</script>',
            columns: [{ name: "x", dataType: "text", nullable: true, isPrimaryKey: false }],
          },
        ],
        foreignKeys: [],
      },
    ];
    const html = buildSchemaExplorerHtml(malicious);
    expect(html).not.toContain("<script>alert(1)</script>");
    expect(html).toContain("&lt;script&gt;");
  });

  it("is a self-contained HTML document with no external resource references", () => {
    const html = buildSchemaExplorerHtml(schemas);
    expect(html).toMatch(/^<!doctype html>/i);
    expect(html).not.toMatch(/https?:\/\//);
  });
});
