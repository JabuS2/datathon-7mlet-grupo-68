#!/usr/bin/env node
/**
 * start-project — cross-platform (Windows + bash) project launcher.
 *
 * It:
 *   1. Ensures a repo-root .env exists (seeded from .env.example).
 *   2. Interactively collects the env vars required by the app stack
 *      (OpenAI key, secrets, ...), preserving existing values.
 *   3. Brings the whole stack up in Docker:
 *        infra + api (--profile api) + app (--profile app: mcp_server,
 *        agent_service, dashboard, front_service).
 *   4. Waits for the key services to become reachable.
 *   5. Generates an HTML page listing every component URL and opens it
 *      in the default browser.
 *
 * Env toggles:
 *   SKIP_START=1   only write the .env, don't start Docker
 *   FOREGROUND=1   run docker compose attached (streams logs)
 *   NO_OPEN=1      don't open the generated HTML in the browser
 */

import { spawn, spawnSync } from "node:child_process";
import { createInterface } from "node:readline";
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import https from "node:https";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const ENV_FILE = path.join(REPO_ROOT, ".env");
const ENV_EXAMPLE = path.join(REPO_ROOT, ".env.example");
const HTML_FILE = path.join(__dirname, "project-urls.html");

const IS_WIN = process.platform === "win32";

// ── Service catalogue (single source of truth for readiness + HTML) ──────────
const SERVICES = [
  {
    group: "Application",
    items: [
      { name: "Angular frontend", url: "http://localhost:4200", link: true, wait: true, desc: "front_service (Angular 22)", creds: () => APP_LOGIN },
      { name: "Admin dashboard", url: "http://localhost:3000", link: true, wait: true, desc: "Next.js dashboard", creds: () => APP_LOGIN },
      { name: "API (Swagger UI)", url: "http://localhost:8001/docs", link: true, wait: true, desc: "FastAPI — api_service", waitUrl: "http://localhost:8001/docs", creds: () => APP_LOGIN },
      { name: "Agent service", url: "http://localhost:8100", link: true, wait: true, desc: "agent_service" },
      { name: "MCP server", url: "http://localhost:8200/mcp", link: true, wait: false, desc: "mcp_server" },
    ],
  },
  {
    group: "Admin & Data tools",
    items: [
      { name: "pgAdmin", url: "http://localhost:5050", link: true, wait: false, desc: "Postgres admin UI",
        creds: () => [["Email", cred("PGADMIN_EMAIL", "admin@datathon.com")], ["Password", cred("PGADMIN_PASSWORD")]] },
      { name: "OpenSearch Dashboards", url: "http://localhost:5601", link: true, wait: false, desc: "OpenSearch UI",
        creds: () => [["User", "admin"], ["Password", cred("OPENSEARCH_ADMIN_PASSWORD")]] },
      { name: "OpenSearch", url: "https://localhost:9200", link: true, wait: false, desc: "Self-signed cert — expect a browser warning",
        creds: () => [["User", "admin"], ["Password", cred("OPENSEARCH_ADMIN_PASSWORD")]] },
      { name: "Neo4j Browser", url: "http://localhost:7474", link: true, wait: false, desc: "Graph DB browser · connect URL bolt://localhost:7687",
        creds: () => [["User", cred("NEO4J_USER", "neo4j")], ["Password", cred("NEO4J_PASSWORD")]] },
    ],
  },
  {
    group: "Infrastructure (no web UI)",
    items: [
      { name: "PostgreSQL", url: "localhost:5432", link: false, wait: false, desc: "Relational database",
        creds: () => [["User", cred("POSTGRES_USER", "postgres")], ["Password", cred("POSTGRES_PASSWORD")], ["Database", cred("POSTGRES_DB", "postgres")]] },
      { name: "Redis", url: "localhost:6379", link: false, wait: false, desc: "Cache / queue",
        creds: () => [["Password", cred("REDIS_PASSWORD")]] },
    ],
  },
];

// Seeded application admin login (api_service/seed.py) — shared by the Angular
// frontend, the Next.js dashboard and the API/Swagger UI.
const APP_LOGIN = [
  ["Email", "admin@admin.com"],
  ["Password", "admin123"],
];

// ── .env helpers ─────────────────────────────────────────────────────────────
function ensureEnvFile() {
  if (fs.existsSync(ENV_FILE)) return;
  if (fs.existsSync(ENV_EXAMPLE)) {
    fs.copyFileSync(ENV_EXAMPLE, ENV_FILE);
    console.log(`Created ${ENV_FILE} from .env.example`);
  } else {
    fs.writeFileSync(ENV_FILE, "");
    console.log(`Created empty ${ENV_FILE}`);
  }
}

function readEnvLines() {
  return fs.existsSync(ENV_FILE)
    ? fs.readFileSync(ENV_FILE, "utf8").split(/\r?\n/)
    : [];
}

function getenv(key) {
  const lines = readEnvLines();
  for (let i = lines.length - 1; i >= 0; i--) {
    const m = lines[i].match(new RegExp(`^${key}=(.*)$`));
    if (m) return m[1];
  }
  return "";
}

// Read an env value with surrounding quotes stripped; fall back to `def`.
function cred(key, def = "") {
  const raw = getenv(key).trim();
  const unquoted = raw.replace(/^["']|["']$/g, "");
  return unquoted || def;
}

function upsert(key, val) {
  const lines = readEnvLines();
  let found = false;
  const out = lines.map((line) => {
    if (line.startsWith(`${key}=`)) {
      found = true;
      return `${key}=${val}`;
    }
    return line;
  });
  if (!found) {
    // keep a single trailing newline tidy
    if (out.length && out[out.length - 1] === "") {
      out.splice(out.length - 1, 0, `${key}=${val}`);
    } else {
      out.push(`${key}=${val}`);
    }
  }
  fs.writeFileSync(ENV_FILE, out.join("\n"));
}

// ── Interactive prompt (with best-effort hidden input for secrets) ───────────
function ask(question, { secret = false } = {}) {
  return new Promise((resolve) => {
    const rl = createInterface({ input: process.stdin, output: process.stdout, terminal: true });
    if (secret) {
      // Mute echoed characters for secret input.
      const orig = rl._writeToOutput?.bind(rl);
      rl._writeToOutput = (str) => {
        if (str.includes(question)) {
          process.stdout.write(str);
        } else {
          process.stdout.write("*".repeat(0));
        }
      };
      rl.question(question, (answer) => {
        rl._writeToOutput = orig;
        process.stdout.write("\n");
        rl.close();
        resolve(answer);
      });
    } else {
      rl.question(question, (answer) => {
        rl.close();
        resolve(answer);
      });
    }
  });
}

// Values that look configured but are just template stubs — never accept these
// as real input (forces a genuine value when the field is required).
const PLACEHOLDERS = new Set(["your_key_here", "your_api_key_here", "sk-...", "changeme"]);

async function prompt(varName, desc, def = "", secret = false, required = false) {
  const current = getenv(varName);
  if (current && !PLACEHOLDERS.has(current)) def = current;
  for (;;) {
    const label = secret
      ? def
        ? `${desc} [keep current] : `
        : `${desc} : `
      : def
      ? `${desc} [${def}] : `
      : `${desc} : `;
    let value = (await ask(label, { secret })).trim();
    if (!value) value = def;
    if (required && (!value || PLACEHOLDERS.has(value))) {
      console.log("  -> a real value is required (placeholder not accepted), please try again");
      continue;
    }
    upsert(varName, value);
    return;
  }
}

// ── Docker Compose helpers ───────────────────────────────────────────────────
function detectCompose() {
  if (spawnSync("docker", ["compose", "version"], { stdio: "ignore" }).status === 0) {
    return { cmd: "docker", pre: ["compose"] };
  }
  if (spawnSync("docker-compose", ["version"], { stdio: "ignore" }).status === 0) {
    return { cmd: "docker-compose", pre: [] };
  }
  console.error("ERROR: neither 'docker compose' nor 'docker-compose' is available.");
  process.exit(1);
}

function composeArgs(compose, extra) {
  return [...compose.pre, "--profile", "api", "--profile", "app", ...extra];
}

function runCompose(compose, extra, opts = {}) {
  return spawnSync(compose.cmd, composeArgs(compose, extra), {
    cwd: REPO_ROOT,
    stdio: "inherit",
    shell: false,
    ...opts,
  });
}

// ── Readiness polling ────────────────────────────────────────────────────────
function ping(url) {
  return new Promise((resolve) => {
    const lib = url.startsWith("https") ? https : http;
    const req = lib.get(url, { rejectUnauthorized: false, timeout: 3000 }, (res) => {
      res.resume();
      // Any HTTP response (even 3xx/4xx) means the port is serving.
      resolve(res.statusCode > 0);
    });
    req.on("error", () => resolve(false));
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitForServices(timeoutMs = 300000) {
  const targets = SERVICES.flatMap((g) => g.items)
    .filter((s) => s.wait)
    .map((s) => ({ name: s.name, url: s.waitUrl || s.url }));
  const pending = new Set(targets.map((t) => t.name));
  const start = Date.now();
  console.log("\nWaiting for services to become reachable (up to 5 min)...");
  while (pending.size && Date.now() - start < timeoutMs) {
    await Promise.all(
      targets.map(async (t) => {
        if (!pending.has(t.name)) return;
        if (await ping(t.url)) {
          pending.delete(t.name);
          console.log(`  ✓ ${t.name} is up (${t.url})`);
        }
      })
    );
    if (pending.size) await sleep(3000);
  }
  if (pending.size) {
    console.log(`  ! Timed out waiting for: ${[...pending].join(", ")}`);
    console.log("    (opening the dashboard anyway — they may still be starting)");
  }
}

// ── HTML generation ──────────────────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function generateHtml() {
  const groups = SERVICES.map((g) => {
    const cards = g.items
      .map((s) => {
        const target = s.link
          ? `<a class="url" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a>`
          : `<span class="url plain">${esc(s.url)}</span>`;
        let credsHtml = "";
        const creds = s.creds ? s.creds() : null;
        if (creds && creds.length) {
          const rows = creds
            .map(
              ([label, value]) => `          <div class="cred-row">
            <span class="cred-label">${esc(label)}</span>
            <code class="cred-value">${esc(value || "—")}</code>
            <button class="copy" type="button" data-copy="${esc(value || "")}" title="Copy">⧉</button>
          </div>`
            )
            .join("\n");
          credsHtml = `
        <div class="creds">
          <div class="creds-title">Credentials</div>
${rows}
        </div>`;
        }
        return `      <div class="card${s.link ? "" : " nolink"}">
        <div class="name">${esc(s.name)}</div>
        <div class="desc">${esc(s.desc)}</div>
        ${target}${credsHtml}
      </div>`;
      })
      .join("\n");
    return `    <section>
      <h2>${esc(g.group)}</h2>
      <div class="grid">
${cards}
      </div>
    </section>`;
  }).join("\n");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>datathon-7mlet-grupo-68 — Services</title>
  <style>
    :root { color-scheme: light dark; }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding: 2rem;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: #0f172a; color: #e2e8f0;
    }
    header { margin-bottom: 2rem; }
    h1 { margin: 0 0 .25rem; font-size: 1.6rem; }
    header p { margin: 0; color: #94a3b8; font-size: .9rem; }
    h2 { font-size: 1.05rem; color: #38bdf8; border-bottom: 1px solid #1e293b; padding-bottom: .4rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; }
    .card {
      background: #1e293b; border: 1px solid #334155; border-radius: 12px;
      padding: 1rem; transition: transform .1s, border-color .1s;
    }
    .card:hover { transform: translateY(-2px); border-color: #38bdf8; }
    .card.nolink:hover { transform: none; border-color: #334155; }
    .name { font-weight: 600; margin-bottom: .2rem; }
    .desc { font-size: .8rem; color: #94a3b8; margin-bottom: .6rem; min-height: 1.6em; }
    .url { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .85rem; word-break: break-all; }
    a.url { color: #7dd3fc; text-decoration: none; }
    a.url:hover { text-decoration: underline; }
    .url.plain { color: #64748b; }
    .creds {
      margin-top: .8rem; padding-top: .7rem; border-top: 1px dashed #334155;
    }
    .creds-title {
      font-size: .68rem; text-transform: uppercase; letter-spacing: .05em;
      color: #64748b; margin-bottom: .4rem;
    }
    .cred-row { display: flex; align-items: center; gap: .4rem; margin-bottom: .25rem; }
    .cred-label { font-size: .72rem; color: #94a3b8; min-width: 62px; }
    .cred-value {
      flex: 1; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: .78rem; color: #fbbf24; background: #0f172a;
      padding: .12rem .4rem; border-radius: 6px; word-break: break-all;
    }
    .copy {
      cursor: pointer; border: 1px solid #334155; background: #0f172a; color: #94a3b8;
      border-radius: 6px; padding: .05rem .35rem; font-size: .8rem; line-height: 1;
    }
    .copy:hover { border-color: #38bdf8; color: #38bdf8; }
    .copy.copied { border-color: #22c55e; color: #22c55e; }
    footer { margin-top: 2.5rem; color: #475569; font-size: .8rem; }
  </style>
</head>
<body>
  <header>
    <h1>datathon-7mlet-grupo-68 — Service dashboard</h1>
    <p>Generated by <code>make start-project</code> · click a card to open the service · click ⧉ to copy a credential.</p>
  </header>
${groups}
  <footer>Generated at ${new Date().toISOString()} · credentials read from your local <code>.env</code></footer>
  <script>
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".copy");
      if (!btn) return;
      const val = btn.getAttribute("data-copy") || "";
      navigator.clipboard.writeText(val).then(() => {
        const prev = btn.textContent;
        btn.textContent = "✓";
        btn.classList.add("copied");
        setTimeout(() => { btn.textContent = prev; btn.classList.remove("copied"); }, 1200);
      });
    });
  </script>
</body>
</html>
`;
}

function openInBrowser(file) {
  const url = "file://" + file.replace(/\\/g, "/");
  try {
    if (IS_WIN) {
      spawn("cmd", ["/c", "start", "", url], { detached: true, stdio: "ignore" }).unref();
    } else if (process.platform === "darwin") {
      spawn("open", [url], { detached: true, stdio: "ignore" }).unref();
    } else {
      spawn("xdg-open", [url], { detached: true, stdio: "ignore" }).unref();
    }
  } catch {
    console.log(`Open this file in your browser: ${file}`);
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  // Regenerate the HTML dashboard without touching Docker or the .env.
  if (process.argv.includes("--html-only")) {
    fs.writeFileSync(HTML_FILE, generateHtml());
    console.log(`Generated service dashboard: ${HTML_FILE}`);
    if (process.env.NO_OPEN !== "1") openInBrowser(HTML_FILE);
    return;
  }

  ensureEnvFile();

  console.log("===============================================================");
  console.log(" Project launcher :: full-stack Docker configuration");
  console.log(` Values are written to ${ENV_FILE} and consumed by docker compose.`);
  console.log(" Press Enter to accept the [default]/current value.");
  console.log("===============================================================");

  await prompt("OPENAI_API_KEY", "OpenAI API key", "", true, true);
  await prompt("OPENAI_MODEL", "OpenAI model spec", "openai:gpt-4o-mini", false, false);
  await prompt("DOWNSTREAM_API_TOKEN", "Downstream admin JWT/service token", "", true, false);
  await prompt("SECRET_KEY", "JWT secret (shared by api + agent)", "your_secret_key", true, true);
  await prompt("ALGORITHM", "JWT algorithm", "HS256", false, false);
  await prompt("AGENT_NAME", "Agent name (must match the dashboard)", "admin_dashboard_agent", false, false);
  await prompt("AGENT_CORS_ORIGINS", "Agent allowed CORS origins (JSON array)", '["http://localhost:3000"]', false, false);
  await prompt("NEXT_PUBLIC_API_SERVICE_URL", "Browser-facing api_service URL", "http://localhost:8001", false, false);

  console.log(`\nWrote configuration to ${ENV_FILE}`);

  if (process.env.SKIP_START === "1") {
    console.log("SKIP_START=1 set — not starting Docker.");
    return;
  }

  const compose = detectCompose();

  console.log("\nBringing up the full stack in Docker (infra + api + app) ...");

  if (process.env.FOREGROUND === "1") {
    const res = runCompose(compose, ["up", "--build"]);
    process.exit(res.status ?? 0);
  }

  const up = runCompose(compose, ["up", "--build", "-d"]);
  if (up.status !== 0) {
    console.error("docker compose up failed.");
    process.exit(up.status ?? 1);
  }

  runCompose(compose, ["ps"]);

  await waitForServices();

  fs.writeFileSync(HTML_FILE, generateHtml());
  console.log(`\nGenerated service dashboard: ${HTML_FILE}`);

  if (process.env.NO_OPEN === "1") {
    console.log("NO_OPEN=1 set — not opening the browser.");
  } else {
    openInBrowser(HTML_FILE);
    console.log("Opened the service dashboard in your browser.");
  }

  console.log("\nStack is running in the background.");
  console.log(`  View logs:  ${compose.cmd} ${composeArgs(compose, ["logs", "-f"]).join(" ")}`);
  console.log(`  Stop stack: ${compose.cmd} ${composeArgs(compose, ["down"]).join(" ")}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
