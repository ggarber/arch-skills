# Risk review

Each service gets a `notes` list of `[severity, category, text]`. Only verified findings go in.

## What to look for

Review every service for at least these areas:

- **In-memory state.** Maps, sets, caches, timers, sessions, sockets, in-process locks and rate limiters, leader election, cron jobs without a cross-instance lock, fallbacks to memory when a shared store is not configured. Ask: what is lost on restart, what breaks during a rolling upgrade, and what goes wrong with two replicas?
- **Removal or merge.** Services or large modules with no callers, ones excluded from CI/CD, thin relays with a single caller, legacy paths behind a flag, duplicated functionality. Add a finding only when removal or merging is warranted.
- **Security and auth.** Routes with no authentication, authentication with no authorization (any logged-in user can act on any resource id), missing tenant or ownership checks, public endpoints that leak tokens or trigger cost, shared static keys and non-constant-time comparison, injection (SQL, shell, command protocols, path traversal), SSRF, unsigned webhooks, TLS verification disabled, secrets logged.
- **Performance and scalability.** N+1 queries, unbounded queries or `limit` parameters, missing indexes on hot filters, heavy synchronous work on the request path, outbound calls with no timeout, one connection per subscriber, polling, components that cannot run more than one instance.
- **Complexity and coupling.** Services that read or write another service's tables directly, too many outbound dependencies, very large controllers or use cases, the same concept owned in two places, configuration conventions that differ between callers.
- **Bugs.** Route shadowing, wrong URLs or headers between services, health checks that always fail, double counting, flows that silently fall back and hide failures.
- **Observability.** Failures that are only logged as warnings, missing metrics or traces on critical paths, alerts that can never fire.

## Verification

For every existing and candidate finding:

1. Find it in committed code and cite the file and line.
2. Keep it only if it is a real problem today. Rewrite it if details are wrong. Drop it if it is false, already fixed, or not worth an engineer's time.
3. If it depends on deployed configuration you cannot see, keep it only when the code makes the risk real regardless, and state the dependency in the text.
4. Never cite untracked or uncommitted files; check with `git ls-files`.

## Severity

| Value | Meaning |
|---|---|
| `high` | Exploitable security hole, likely outage or data loss, or in-memory state that prevents upgrading or restarting without disrupting users (lost sessions, dropped calls, lost in-flight work). A single instance that cannot be scaled or replaced without downtime is also high. |
| `med` | A real problem worth scheduling. |
| `low` | Cleanup, documentation drift, minor waste. |

State that lives in memory only when an optional shared store is not configured is usually `med` or `low`: the normal deploy is not disrupted. Raise it if production is likely to run without the store.

## Category

| Value | Use for |
|---|---|
| `reliability` | State lost on restart or upgrade, split state across replicas, missing timeouts/retries, crons without locks, single points of failure. |
| `observability` | Silent failures, missing metrics, logs or traces, alerts that cannot fire. |
| `maintainability` | Coupling, direct access to another service's data, god classes, duplicated ownership, removal or merge candidates, stale config and docs. |
| `security` | Authentication, authorization, tenancy, secrets, injection, exposure. |
| `bugs` | Incorrect behaviour today. |
| `scalability` | Performance limits, unbounded work, connection or memory growth, components that cannot scale out. |

## Writing a finding

One to three sentences: what is wrong, where (`path/file.ts:line`), the consequence, and the fix. Example:

> Checkout sessions live in an in-process Map (src/checkout/session.store.ts:12), so every deploy or restart drops carts in checkout and a second replica cannot see them. Move them to the shared database or cache.

## Review metadata

Set `project.reviewMeta` to one sentence on what was reviewed (branch or commit, month) and what could not be checked (for example deployment manifests in another repository).
