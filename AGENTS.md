# AGENTS.md

## Scope and intent
These instructions apply to the entire repository. Follow them for all future Codex sessions unless a higher-priority user/system/developer instruction overrides them.

## Architectural guardrails
- **Plan first for non-trivial backend changes.**
  - For multi-file changes, schema updates, ingestion changes, or ranking/compare behavior updates, write a brief step plan before editing.
- **Preserve public API contracts unless explicitly asked to change them.**
  - Treat the following routes as app-facing contracts: `/catalog`, `/search`, `/autocomplete`, `/product/{id}`, `/compare`.
  - Do not change request/response fields, types, or semantics for these routes unless the task explicitly requests a contract change.
- **Do not couple routes directly to upstream provider payloads.**
  - Route handlers should serve stable app-facing models and read models, not raw provider response shapes.
- **Keep live provider logic behind provider abstractions and ingestion.**
  - Provider-specific parsing/fetching belongs in provider adapters and ingestion workflows, not in route handlers.
- **Internal normalized data is the source of truth for app reads.**
  - App-facing reads should come from normalized/canonical internal models.
  - Provider output must be mapped into normalized internal models before serving.

## Data import, reliability, and diagnostics
- **Prefer idempotent imports** and safe re-runs.
  - Avoid duplicate insert behavior; use upserts/dedup keys where appropriate.
- **Favor observable diagnostics.**
  - Add/extend diagnostics when behavior changes so operators can detect regressions quickly.
  - Diagnostics should help catch: stale data, failed imports, weak search quality, and mapping drift.
- **Search quality changes should favor explainable scoring over opaque complexity.**
  - Prefer transparent, debuggable ranking signals and thresholds.

## Change scope and delivery
- **Avoid broad rewrites when a targeted change is enough.**
  - Keep diffs focused on the problem being solved.
- **Add or update tests for behavior changes.**
  - Any user-visible or contract-relevant behavior change should include corresponding test coverage.
- **Never hardcode secrets.**
  - Use environment variables/configuration; do not commit credentials.
- **Keep logs free of API keys and sensitive headers.**
  - Redact or omit sensitive values in diagnostics/logging.

## Implementation handoff checklist
After implementing a change, summarize:
1. Files changed.
2. Any migrations or data backfill/import steps required.
3. Environment variables added/changed.
4. Local commands to run/test the change.
