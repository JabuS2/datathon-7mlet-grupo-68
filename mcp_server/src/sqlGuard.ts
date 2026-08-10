/**
 * Defense-in-depth checks on agent-generated SQL, on top of the hard boundary
 * that actually matters: the `readonly_reporting` Postgres role has no grant
 * beyond SELECT, so none of this can be bypassed into a write even if it were
 * wrong. This layer exists to fail fast with a clear message instead of
 * letting Postgres reject a malformed/dangerous statement, and to enforce the
 * row cap that the role alone can't express.
 */

const STATEMENT_TIMEOUT_MS = 5000;
const ROW_CAP = 200;

// Anything on this list has no business appearing in a reporting query, even
// one the read-only role couldn't execute — e.g. it might name a function or
// be part of a dollar-quoted trick. Matched as whole words, case-insensitively.
const DENYLIST = [
  "insert",
  "update",
  "delete",
  "drop",
  "alter",
  "truncate",
  "grant",
  "revoke",
  "create",
  "copy",
  "call",
  "do",
  "vacuum",
  "execute",
  "into",
  "dblink",
  "pg_read_file",
  "pg_write_file",
  "lo_import",
  "lo_export",
];

export class SqlGuardError extends Error {}

/**
 * Validates that `sql` is a single read-only SELECT/WITH statement, and
 * returns it wrapped so the row cap applies regardless of what the inner
 * query does (its own LIMIT, if any, still narrows further).
 */
export function guardSelectStatement(sql: string): string {
  const trimmed = sql.trim();
  if (!trimmed) {
    throw new SqlGuardError("Empty SQL statement.");
  }

  // Strip at most one trailing semicolon; anything else with a semicolon in
  // it is a multi-statement attempt.
  const withoutTrailingSemicolon = trimmed.replace(/;\s*$/, "");
  if (withoutTrailingSemicolon.includes(";")) {
    throw new SqlGuardError("Only a single SQL statement is allowed (no semicolons inside the query).");
  }

  if (!/^(select|with)\b/i.test(withoutTrailingSemicolon)) {
    throw new SqlGuardError("Only SELECT/WITH (read-only) statements are allowed.");
  }

  for (const word of DENYLIST) {
    const pattern = new RegExp(`\\b${word}\\b`, "i");
    if (pattern.test(withoutTrailingSemicolon)) {
      throw new SqlGuardError(`Statement contains a disallowed keyword: '${word}'.`);
    }
  }

  return `SELECT * FROM (\n${withoutTrailingSemicolon}\n) AS _guarded_query LIMIT ${ROW_CAP}`;
}

export { STATEMENT_TIMEOUT_MS, ROW_CAP };
