import { describe, expect, it } from "vitest";

import { guardSelectStatement, ROW_CAP, SqlGuardError } from "./sqlGuard.js";

describe("guardSelectStatement", () => {
  it("allows a plain SELECT and wraps it with the row cap", () => {
    const guarded = guardSelectStatement("select * from clientes");
    expect(guarded).toContain("select * from clientes");
    expect(guarded).toContain(`LIMIT ${ROW_CAP}`);
  });

  it("allows a WITH (CTE) statement", () => {
    const guarded = guardSelectStatement(
      "with recent as (select * from decisoes) select * from recent",
    );
    expect(guarded).toContain(`LIMIT ${ROW_CAP}`);
  });

  it("strips a single trailing semicolon", () => {
    const guarded = guardSelectStatement("select 1;");
    expect(guarded).toContain("select 1");
  });

  it("rejects an empty statement", () => {
    expect(() => guardSelectStatement("   ")).toThrow(SqlGuardError);
  });

  it("rejects multi-statement input (semicolon-separated)", () => {
    expect(() => guardSelectStatement("select 1; drop table clientes")).toThrow(SqlGuardError);
  });

  it("rejects statements that don't start with SELECT/WITH", () => {
    expect(() => guardSelectStatement("update clientes set idade = 0")).toThrow(SqlGuardError);
    expect(() => guardSelectStatement("delete from clientes")).toThrow(SqlGuardError);
    expect(() => guardSelectStatement("insert into clientes default values")).toThrow(
      SqlGuardError,
    );
  });

  it("rejects denylisted keywords even inside a SELECT-shaped statement", () => {
    expect(() =>
      guardSelectStatement("select * from clientes where 1=1; drop table clientes"),
    ).toThrow(SqlGuardError);
    expect(() => guardSelectStatement("select pg_read_file('/etc/passwd')")).toThrow(
      SqlGuardError,
    );
    expect(() => guardSelectStatement("select dblink('host=evil', 'select 1')")).toThrow(
      SqlGuardError,
    );
  });

  it("is case-insensitive for both the leading keyword and the denylist", () => {
    const guarded = guardSelectStatement("SELECT * FROM clientes");
    expect(guarded).toContain(`LIMIT ${ROW_CAP}`);
    expect(() => guardSelectStatement("SELECT * FROM clientes; DROP TABLE clientes")).toThrow(
      SqlGuardError,
    );
  });
});
