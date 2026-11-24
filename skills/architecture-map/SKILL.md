---
name: architecture-map
description: Generate a self-contained HTML architecture map of a multi-service codebase - a home page with a dependency diagram of every service and a risk summary per service and severity, plus one page per service with a context diagram (outputs left, inputs right, databases and queues below), its input and output interfaces, and a verified risk review rated by severity and category. Use when asked to map, document or review the architecture, services, interfaces or risks of a repository or monorepo, or to update an existing architecture map.
---

# Architecture map

Produce a static HTML site, in one self-contained file, that documents every service in a codebase and reviews its risks. You write one JSON data file; `scripts/build.py` validates it and injects it into `assets/template.html`. Never hand-edit the generated HTML; change the data and rebuild.

## Output

A home page plus one page per service, switched with a picker at the top (`#` is home, `#<service-id>` is a service page).

**Home page**

1. A diagram of every service, actor and shared external system, with an arrow from each caller or producer to its callee or consumer. Clicking a service opens its page.
2. A risk summary table: one row per service, one column per level (High, Medium, Low) plus Total, and an "All services" totals row. The cross-cutting themes follow the table.

**Service page**

1. A context diagram with the service in the middle, its **outputs** (what it calls or sends to) on the **left**, its **inputs** (callers, webhooks, sockets) on the **right**, and **databases, queues, caches and object stores at the bottom**. Arrows follow the direction of the call or data, so they run right to left.
2. Interfaces in two columns: every input on one side (with scheduled jobs underneath, since timers also trigger the service) and every output on the other. Each entry names the other party, the interface (route, topic, operation) and its purpose.
3. A list of risks, each with its level and one or more categories.

See `assets/example-data.json` for a complete small example and `references/data-format.md` for every field.

## Workflow

1. **Find the services.** Look for deployables: `apps/*`, `services/*`, `packages/*` with a server entry point, Dockerfiles, docker-compose services, Kubernetes/Helm manifests, serverless configs, CI deploy matrices. Note the gateway or ingress config, because it decides what is publicly reachable. List shared libraries separately: they are not services, but their behaviour (auth guards, clients, connection modules) shows up in services' findings.
2. **Map each service.** Read entry point, module wiring, controllers/routes, consumers, clients and config. For each service record:
   - `summary`: what it owns, in one or two sentences.
   - `core`: 2-4 sections of what it does, including an `IN-MEMORY` or `TIMERS` section when it keeps state in process.
   - `inbound` (diagram, right): who calls it directly (HTTP routes grouped by caller, webhooks, sockets), with the auth mechanism in `sub`.
   - `outbound` (diagram, left): what it calls directly (other services, third-party APIs), with the env var or key that configures it in `sub`.
   - `storage` (diagram, bottom): databases (and which tables or schemas), caches, object stores, local disk, and the queues and topics it consumes from or publishes to. Use `kind: "evt"` for queues and topics and `dir` for direction (`from` = consumes, `to` = publishes); name the producer or consumer in `sub`.
   - `tablesIn`/`tablesOut`: one row per input or output interface, including queue messages, for the Interfaces section.
   - `jobs`: crons, intervals, pollers and sweeps with their cadence; listed under the inputs.
   - Mark env-gated, optional or unused paths with `opt: true` and say so in the text.
3. **Build the graph.** One node per service, plus actor nodes (users, operators, devices) and external systems that several services touch. Edges are `[from, to, "http" | "evt", what, optional?]`, pointing from caller or producer to callee or consumer. Draw queue and pub/sub traffic as a direct producer → consumer `evt` edge. Use `evt` also for coupling through a shared database. Put actors first in `graph.order`, then order the ring so tightly coupled services sit next to each other.
4. **Review risks** following `references/risk-review.md`. Every finding is verified in committed code before it goes in.
5. **Write cross-cutting themes**: 4-7 patterns that recur across services (shared keys, per-pod state, unauthenticated services, direct cross-service data access, removal candidates).
6. **Build and check:**
   ```bash
   python3 <skill-dir>/scripts/build.py architecture-map.json docs/architecture.html
   ```
   Fix every validation error it prints. Open the page (or screenshot it headlessly) and check that the home page and one or two service pages render.

## Working at scale

For more than about five services, map and review services in parallel: give each subagent a group of services, the field list above, `references/risk-review.md`, and an output path for a JSON fragment (`{ "<service-id>": { ...service fields... } }`). Merge the fragments yourself, then write the graph and themes, which need the whole picture.

## Updating an existing map

Keep the data file next to the generated page (for example `docs/architecture-map.json` beside `docs/architecture.html`). To update, re-verify every existing finding against the current code: keep, rewrite or drop each one, then look for new ones. Rebuild from the data file.

## Rules

- Cite only committed files. Check with `git ls-files <path>` before citing a path; untracked notes, local configs and scratch files are not evidence.
- No speculation presented as fact. If a risk depends on deployed configuration you cannot see (replica counts, ingress rules, env values), keep it only when the code makes the risk real, and say what depends on deployment.
- Write for an engineer who will act on it: plain sentences, the key `path/to/file.ts:line`, and the fix in a clause. No markdown or HTML inside data strings.
- Do not put secrets, real customer data or credentials in the data file, even if you find them in the repo. Name the env var instead.
