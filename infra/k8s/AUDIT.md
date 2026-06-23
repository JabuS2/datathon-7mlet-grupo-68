# Kubernetes Implementation Audit — `infra/k8s/`

Audit date: 2026-06-15
Scope: bug / misconfiguration / inconsistency review of the Helmfile-based
Kubernetes setup, **with fixes applied**.

Tooling note: `helm`/`helmfile` are not installed in this environment, so
validation was performed by reading upstream chart templates
(`opensearch` `_helpers.tpl`, bitnami `neo4j` values), cross-checking the API's
`api_service/settings.py`, and YAML-parsing the edited files. A `helmfile lint`
run on a machine with the tooling is still recommended.

---

## Summary

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| 1 | HIGH | OpenSearch service-name mismatch (API + Dashboards) | ✅ Fixed |
| 2 | HIGH | Neo4j secret key not consumed by bitnami chart | ✅ Fixed |
| 3 | MEDIUM | Orphaned, conflicting raw manifests (neo4j, pgadmin) | ✅ Removed |
| 4 | MEDIUM | Bitnami chart-repo deprecation (2025) | ⚠️ Advisory |
| 5 | LOW | `_helpers.tpl` `fullname` ignores `nameOverride` | ℹ️ Documented |
| 6 | LOW | README NodePort table wording | ℹ️ Documented |
| 7 | INFO | Secret/ConfigMap keys cross-checked vs `settings.py` | ✅ Verified OK |

---

## 1. HIGH — OpenSearch service-name mismatch

**Files:** `charts/api/values.yaml`, `values/opensearch-dashboards.values.yaml`

The OpenSearch chart computes the master service name as
`{{ .Values.clusterName }}-master` (see upstream
`opensearch/templates/_helpers.tpl` → `opensearch.masterService`). With
`clusterName: datathon-opensearch`, the real service is
**`datathon-opensearch-master`**.

But two consumers pointed at the chart's *default* name
`opensearch-cluster-master`, which does not exist here:

- API ConfigMap: `connections.opensearchHost: opensearch-cluster-master`
- Dashboards: `opensearchHosts: "https://opensearch-cluster-master:9200"`

Result: both the API and OpenSearch Dashboards would fail DNS resolution and
never connect. (The README already used the correct name.)

**Fix applied:** both values updated to `datathon-opensearch-master`.

## 2. HIGH — Neo4j secret key not consumed by the bitnami chart

**Files:** `values/neo4j.values.yaml`, `secrets/neo4j.secrets.yaml.example`

`neo4j.values.yaml` set `auth.existingSecret: neo4j-secret` with no
`existingSecretPasswordKey`. The bitnami/neo4j chart defaults that key to
**`neo4j-password`**, but the secret only provides `NEO4J_PASSWORD` /
`NEO4J_AUTH` / `NEO4J_USER`. The chart would not find a password and the release
would fail (or generate a random password the API doesn't know).

There were effectively three different secret schemas for the same secret:
the chart expected `neo4j-password`, the API deployment reads
`NEO4J_USER` + `NEO4J_PASSWORD`, and the (now-removed) raw manifest read
`NEO4J_AUTH`.

**Fix applied:**
- `neo4j.values.yaml`: added `existingSecretPasswordKey: NEO4J_PASSWORD` so the
  chart reads the same key the API uses → single source of truth.
- `neo4j.secrets.yaml.example`: dropped the now-unused `NEO4J_AUTH` and clarified
  which components consume `NEO4J_USER` / `NEO4J_PASSWORD`.

> Action required for existing deployments: ensure the real (gitignored)
> `neo4j.secrets.yaml` contains a `NEO4J_PASSWORD` key (it already should).

## 3. MEDIUM — Orphaned, conflicting raw manifests

**Files (removed):** `manifests/neo4j.yaml`, `manifests/pgadmin.yaml`

These raw manifests were **not referenced by `helmfile.yaml`** and were not
listed in the README file-structure. They created resources with the **same
names and NodePorts** as the Helm releases:

- `manifests/neo4j.yaml` → StatefulSet/Service `datathon-neo4j`
  (vs. `bitnami/neo4j` release `datathon-neo4j`, NodePorts 30474/30687).
- `manifests/pgadmin.yaml` → Deployment/Service `datathon-pgadmin`, NodePort
  30050 (vs. `runix/pgadmin4` release `datathon-pgadmin`, NodePort 30050).

If anyone `kubectl apply`-ed the `manifests/` directory alongside
`helmfile apply`, the two would collide (duplicate Services / NodePort
conflicts) and the raw Neo4j used a different secret schema (`NEO4J_AUTH`).

**Decision:** Helmfile is the single source of truth (per the README's two
deployment targets: Docker Compose *or* Helmfile). The orphaned raw manifests
were removed to eliminate the conflict and the divergent Neo4j secret schema.

## 4. MEDIUM — Bitnami chart-repo deprecation (advisory)

**File:** `helmfile.yaml` (`bitnami/postgresql`, `bitnami/redis`, `bitnami/neo4j`)

In 2025 Bitnami restructured its public catalog: many tagged images backing
`charts.bitnami.com/bitnami` charts were moved to a `bitnamilegacy` registry and
the free Helm index changed. Depending on *when* this is deployed, pulls for
PostgreSQL / Redis / Neo4j images may fail with `ImagePullBackOff`.

**Not auto-changed** — the correct remediation (pin image tags, repoint
`global.imageRegistry`/`image.repository` to `bitnamilegacy`, or move to
alternative charts) depends on the target cluster and current registry state,
and a blind change could break a currently-working setup.

**Recommendation:** when deploying, if Bitnami images fail to pull, set the
image registry to `docker.io/bitnamilegacy` (or pin known-good tags) in the
respective `values/*.yaml`, or migrate to maintained alternatives.

## 5. LOW — `_helpers.tpl` `fullname` ignores `nameOverride`

**File:** `charts/api/templates/_helpers.tpl`

`datathon-api.fullname` returns only `.Release.Name`, so `nameOverride` /
`fullnameOverride` have no effect. This is harmless for the current single
release (`datathon-api`) and was left as-is to avoid renaming resources, but
note it deviates from the standard Helm helper pattern.

## 6. LOW — README NodePort wording

**File:** `README.md`

The services table lists PostgreSQL/Redis/OpenSearch under "Kubernetes
(NodePort)" as `localhost:<port>`; these are actually **ClusterIP** services
reachable only via the documented `kubectl port-forward` (the "(via
port-forward)" note is present but the column header "NodePort" is misleading).
Left as documentation-only; consider relabelling the column "Kubernetes
(access)".

## 7. INFO — ConfigMap / Secret keys verified against the app

Cross-checked every env var the API consumes (`api_service/settings.py`)
against the ConfigMap and Secret references in `charts/api/templates`:

`POSTGRES_SERVER/PORT/USER/PASSWORD/DB`, `REDIS_HOST/PORT/PASSWORD/DB`,
`OPENSEARCH_HOST/PORT/USER/ADMIN_PASSWORD`, `NEO4J_URI/USER/PASSWORD`,
`SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`BACKEND_CORS_ORIGINS`, `PROJECT_NAME`, `VERSION`, `API_PORT` — **all match**.
The liveness/readiness probe path `/api/v1/health` is also correct
(`router` mounted at `/api/v1`, health route `/health`).

---

## Changes applied in this audit

- `charts/api/values.yaml` — `opensearchHost` → `datathon-opensearch-master`.
- `values/opensearch-dashboards.values.yaml` — `opensearchHosts` →
  `https://datathon-opensearch-master:9200`.
- `values/neo4j.values.yaml` — added `auth.existingSecretPasswordKey: NEO4J_PASSWORD`.
- `secrets/neo4j.secrets.yaml.example` — removed unused `NEO4J_AUTH`, clarified usage.
- Removed `manifests/neo4j.yaml` and `manifests/pgadmin.yaml` (orphaned/conflicting).

## Recommended follow-ups (not applied)

- Run `helmfile lint` and `helm template ./charts/api` on a machine with the tooling.
- Address Bitnami registry deprecation (#4) if image pulls fail.
- Optionally clean up the unused `neo4j` Helm repo entry in `helmfile.yaml`
  (the `bitnami/neo4j` chart is used, not `neo4j/neo4j`).
