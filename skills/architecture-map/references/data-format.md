# Data format

`scripts/build.py` reads one JSON file with this shape:

```jsonc
{
  "project": {
    "name": "Acme",                       // shown in the header and tab title
    "reviewMeta": "Reviewed against ...",  // one sentence shown above every risk table
    "notShown": "end users' browsers, ...",// optional caption under the ring
    "themes": [{ "title": "Per-pod state", "text": "..." }]  // cross-cutting themes, under the home page risk table
  },
  "allIds": ["orders-service", "..."],    // optional, picker order (may include ids not mapped yet)
  "services": [ /* Service */ ],
  "graph": {
    "order": ["customer", "orders-service", "..."],  // ring order, starting at the top
    "nodes": { "customer": { "label": "Customer", "kind": "actor" } },
    "edges": [["customer", "orders-service", "http", "Checkout", false]]
  }
}
```

## Service

| Field | Type | Notes |
|---|---|---|
| `id` | string | Unique; used in URLs (`#id`) and links. |
| `port` | number | Optional. |
| `stack` | string | Optional, shown under the name in the core box. |
| `summary` | string | One or two sentences. |
| `core` | `{ h, lines[] }[]` | Sections inside the core box. Keep lines under about 48 characters. |
| `inbound` | Box[] | Inputs: right column of the diagram. Direct callers (HTTP, webhooks, sockets). |
| `outbound` | Box[] | Outputs: left column of the diagram. Services and APIs it calls. |
| `storage` | Box[] | Row under the diagram: databases, caches, object stores, queues and topics. Kind `store` or `evt`. |
| `tablesIn` | `[from, interface, purpose][]` | Inputs column of the Interfaces section. |
| `tablesOut` | `[to, interface, purpose][]` | Outputs column of the Interfaces section. |
| `jobs` | `[name, cadence, purpose][]` | Scheduled jobs, listed under the inputs. Optional. |
| `notes` | `[severity, category \| category[], text][]` | Risks. See `risk-review.md`. |

## Box

| Field | Values | Notes |
|---|---|---|
| `kind` | `in`, `evt`, `out`, `store` | Colour and arrow style: inbound HTTP, events and queues, outbound HTTP, storage. |
| `title` | string | Required. |
| `sub` | string | Transport and auth, or the env var that configures it. |
| `lines` | string[] | Routes, topics, tables. |
| `link` | service id | Makes the box clickable. |
| `opt` | boolean | Dashed: optional, env-gated or unused. |
| `dir` | `to`, `from`, `both` | Arrow direction relative to the service. Storage defaults to `both`; use `from` for a queue it consumes, `to` for one it publishes to or a store it only writes. Inputs and outputs default to `to` (toward the service for inputs, away from it for outputs). |
| `feeds` | number | Storage only: index of another box in the same row this box feeds into. |

## Graph

- `nodes`: extra nodes that are not services. `kind: "actor"` (people, devices) or `kind: "ext"` (external systems, dashed). `link` makes a node open a service's map (useful when a service fronts a piece of infrastructure).
- `order`: every node and service that appears in an edge. The first entry sits at the top of the ring.
- `edges`: `[from, to, type, what, optional]`. `type` is `http` (requests, WebSockets) or `evt` (events, media streams, or coupling through a shared database). Parallel edges between the same pair are merged in the drawing and listed in the hover tooltip.

## Values

- Severity: `high`, `med`, `low`.
- Category: `reliability`, `observability`, `maintainability`, `security`, `bugs`, `scalability`. A risk may list several, for example `["security", "bugs"]`.
