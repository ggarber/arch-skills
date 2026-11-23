---
name: architecture-map
description: Generate a self-contained HTML architecture map of a multi-service codebase - one system-context diagram per service (callers, events, dependencies, storage), interface tables, background jobs, a dependency ring of all services, and a verified risk review rated by severity and category. Use when asked to map, document or review the architecture, services, interfaces or risks of a repository or monorepo, or to update an existing architecture map.
---

# Architecture map

Produce a single static HTML page that documents every service in a codebase and reviews its risks. You write one JSON data file; `scripts/build.py` validates it and injects it into `assets/template.html`. Never hand-edit the generated HTML; change the data and rebuild.

## Output

One page with:

- A picker with one chip per service plus an `all` view.
- Per service: summary, a system-context diagram (inbound callers and event sources on the left, the service core in the middle, outbound calls on the right, storage below), inbound/outbound interface tables, background jobs, and a risk table (severity, category, issue).
- `all` view: a ring of every service and external actor with caller → callee edges, a risk summary (counts, per-service table, cross-cutting themes, every high-severity issue) and the full edge list.

See `assets/example-data.json` for a complete small example and `references/data-format.md` for every field.

## Workflow

1. **Find the services.** Look for deployables: `apps/*`, `services/*`, `packages/*` with a server entry point, Dockerfiles, docker-compose services, Kubernetes/Helm manifests, serverless configs, CI deploy matrices. Note the gateway or ingress config, because it decides what is publicly reachable. List shared libraries separately: they are not services, but their behaviour (auth guards, clients, connection modules) shows up in services' findings.
2. **Map each service.** Read entry point, module wiring, controllers/routes, consumers, clients and config. For each service record:
   - `summary`: what it owns, in one or two sentences.
   - `core`: 2-4 sections of what it does, including an `IN-MEMORY` or `TIMERS` section when it keeps state in process.
   - `inbound`: who calls it or what it consumes (HTTP routes grouped by caller, queues, pub/sub, webhooks, sockets), with auth mechanism in `sub`.
   - `outbound`: what it calls (other services, third-party APIs, queues it publishes to), with the env var or key that configures it in `sub`.
   - `storage`: databases (and which tables or schemas), caches, object stores, local disk.
   - `tablesIn`/`tablesOut`/`jobs`: the same, as reference rows. Jobs include crons, intervals, pollers and sweeps with their cadence.
   - Mark env-gated, optional or unused paths with `opt: true` and say so in the text.
3. **Build the graph.** One node per service, plus actor nodes (users, operators, devices) and external systems that several services touch. Edges are `[from, to, "http" | "evt", what, optional?]`, pointing from caller or producer to callee or consumer. Draw queue and pub/sub traffic as a direct producer → consumer `evt` edge. Use `evt` also for coupling through a shared database. Put actors first in `graph.order`, then order the ring so tightly coupled services sit next to each other.
4. **Review risks** following `references/risk-review.md`. Every finding is verified in committed code before it goes in.
5. **Write cross-cutting themes**: 4-7 patterns that recur across services (shared keys, per-pod state, unauthenticated services, direct cross-service data access, removal candidates).
6. **Build and check:**
   ```bash
   python3 <skill-dir>/scripts/build.py architecture-map.json docs/architecture.html
   ```
   Fix every validation error it prints. Open the page (or screenshot it headlessly) and check the `all` view and one or two services render.

## Working at scale

For more than about five services, map and review services in parallel: give each subagent a group of services, the field list above, `references/risk-review.md`, and an output path for a JSON fragment (`{ "<service-id>": { ...service fields... } }`). Merge the fragments yourself, then write the graph and themes, which need the whole picture.

## Updating an existing map

Keep the data file next to the generated page (for example `docs/architecture-map.json` beside `docs/architecture.html`). To update, re-verify every existing finding against the current code: keep, rewrite or drop each one, then look for new ones. Rebuild from the data file.

## Rules

- Cite only committed files. Check with `git ls-files <path>` before citing a path; untracked notes, local configs and scratch files are not evidence.
- No speculation presented as fact. If a risk depends on deployed configuration you cannot see (replica counts, ingress rules, env values), keep it only when the code makes the risk real, and say what depends on deployment.
- Write for an engineer who will act on it: plain sentences, the key `path/to/file.ts:line`, and the fix in a clause. No markdown or HTML inside data strings.
- Do not put secrets, real customer data or credentials in the data file, even if you find them in the repo. Name the env var instead.
