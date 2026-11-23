#!/usr/bin/env python3
"""Build a self-contained architecture map page from a JSON data file.

Usage:
    python3 build.py <data.json> <out.html>

The data file is validated against the format in references/data-format.md,
then injected into assets/template.html. Exits non-zero with a list of
problems when the data is invalid.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")

SEVERITIES = {"high", "med", "low"}
CATEGORIES = {"reliability", "observability", "maintainability", "security", "bugs", "scalability"}
BOX_KINDS = {"in", "evt", "out", "store"}
DIRS = {"to", "from", "both"}
EDGE_TYPES = {"http", "evt"}
NODE_KINDS = {"actor", "ext"}


def validate(data):
    errs = []
    project = data.get("project")
    if not isinstance(project, dict) or not project.get("name"):
        errs.append("project.name is required")
    services = data.get("services")
    if not isinstance(services, list) or not services:
        errs.append("services must be a non-empty list")
        return errs
    ids = [s.get("id") for s in services]
    if len(set(ids)) != len(ids):
        errs.append("service ids must be unique")
    graph = data.get("graph", {})
    node_ids = set(ids) | set((graph.get("nodes") or {}).keys())

    for s in services:
        sid = s.get("id", "?")
        if not s.get("summary"):
            errs.append(f"{sid}: summary is required")
        for sec in s.get("core", []):
            if "h" not in sec or not isinstance(sec.get("lines"), list):
                errs.append(f"{sid}: core sections need h and lines")
        for side in ("inbound", "outbound", "storage"):
            for b in s.get(side, []):
                if b.get("kind") not in BOX_KINDS:
                    errs.append(f"{sid}.{side}: kind must be one of {sorted(BOX_KINDS)} ({b.get('title')})")
                if not b.get("title"):
                    errs.append(f"{sid}.{side}: every box needs a title")
                if "dir" in b and b["dir"] not in DIRS:
                    errs.append(f"{sid}.{side}: dir must be one of {sorted(DIRS)}")
                if b.get("link") and b["link"] not in ids:
                    errs.append(f"{sid}.{side}: link '{b['link']}' is not a service id")
        for key in ("tablesIn", "tablesOut", "jobs"):
            for r in s.get(key, []):
                if not (isinstance(r, list) and len(r) == 3):
                    errs.append(f"{sid}.{key}: rows must be [a, b, c]")
        for n in s.get("notes", []):
            if not (isinstance(n, list) and len(n) == 3):
                errs.append(f"{sid}.notes: rows must be [severity, category, text]")
                continue
            if n[0] not in SEVERITIES:
                errs.append(f"{sid}.notes: severity '{n[0]}' not in {sorted(SEVERITIES)}")
            if n[1] not in CATEGORIES:
                errs.append(f"{sid}.notes: category '{n[1]}' not in {sorted(CATEGORIES)}")

    for nid, node in (graph.get("nodes") or {}).items():
        if node.get("kind") and node["kind"] not in NODE_KINDS:
            errs.append(f"graph.nodes.{nid}: kind must be one of {sorted(NODE_KINDS)}")
        if node.get("link") and node["link"] not in ids:
            errs.append(f"graph.nodes.{nid}: link '{node['link']}' is not a service id")
    order = graph.get("order") or []
    for o in order:
        if o not in node_ids:
            errs.append(f"graph.order: '{o}' is neither a service id nor a graph node")
    for e in graph.get("edges", []):
        if not (isinstance(e, list) and 4 <= len(e) <= 5):
            errs.append(f"graph.edges: rows must be [from, to, type, what, optional?]: {e}")
            continue
        if e[0] not in order or e[1] not in order:
            errs.append(f"graph.edges: both ends must appear in graph.order: {e[0]} -> {e[1]}")
        if e[2] not in EDGE_TYPES:
            errs.append(f"graph.edges: type must be one of {sorted(EDGE_TYPES)}: {e}")
    if data.get("defaultId") and data["defaultId"] not in ids:
        errs.append("defaultId must be a service id")
    return errs


def js(value):
    # JSON is valid JS; escape "</" so text can never close the <script> tag.
    return json.dumps(value, ensure_ascii=False, indent=1).replace("</", "<\\/")


def build(data):
    services = data["services"]
    graph = data.get("graph", {})
    order = graph.get("order") or [s["id"] for s in services]
    project = {
        "name": data["project"]["name"],
        "reviewMeta": data["project"].get("reviewMeta", ""),
        "notShown": data["project"].get("notShown", ""),
        "themes": data["project"].get("themes", []),
    }
    block = "\n".join([
        f"const PROJECT = {js(project)};",
        f"const SERVICES = {js(services)};",
        f"const ALL_IDS = {js(data.get('allIds') or [s['id'] for s in services])};",
        f"const DEFAULT_ID = {js(data.get('defaultId') or services[0]['id'])};",
        f"const GRAPH_ORDER = {js(order)};",
        f"const GRAPH_NODES = {js(graph.get('nodes') or {})};",
        f"const GRAPH_EDGES = {js(graph.get('edges') or [])};",
    ])
    template = open(TEMPLATE, encoding="utf-8").read()
    if template.count("/*DATA*/") != 1:
        raise SystemExit("template is missing the /*DATA*/ marker")
    return template.replace("/*DATA*/", block)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    errs = validate(data)
    if errs:
        print("Invalid data:", file=sys.stderr)
        for e in errs:
            print("  - " + e, file=sys.stderr)
        raise SystemExit(1)
    html = build(data)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(html)
    notes = [n for s in data["services"] for n in s.get("notes", [])]
    print(f"Wrote {sys.argv[2]}: {len(data['services'])} services, "
          f"{len(notes)} risks ({sum(n[0] == 'high' for n in notes)} high)")


if __name__ == "__main__":
    main()
