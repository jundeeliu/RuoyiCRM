#!/usr/bin/env python3
"""Source-located Spring injection graph audit for RuoyiCRM.

This static graph covers @Autowired/@Resource fields and explicit autowired
constructor parameters. A zero-SCC result is not an ApplicationContext startup
result and never authorizes circular-reference compatibility settings.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASS = re.compile(r"\bclass\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+([\w\s,<>]+))?")
FIELD = re.compile(r"@(?:Autowired|Resource)(?:\([^)]*\))?\s+(?:private|protected|public)?\s+(?:final\s+)?([A-Z]\w+)\s+\w+\s*;", re.MULTILINE)
AUTOWIRED_CONSTRUCTOR = re.compile(r"@Autowired\s+(?:public|protected)?\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE)


def tarjan(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = low[node] = index
        index += 1
        stack.append(node)
        active.add(node)
        for neighbor in sorted(graph[node]):
            if neighbor not in indices:
                visit(neighbor)
                low[node] = min(low[node], low[neighbor])
            elif neighbor in active:
                low[node] = min(low[node], indices[neighbor])
        if low[node] == indices[node]:
            component = []
            while True:
                current = stack.pop()
                active.remove(current)
                component.append(current)
                if current == node:
                    break
            if len(component) > 1 or node in graph[node]:
                cycles.append(sorted(component))

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(cycles)


def audit(root: Path = ROOT) -> dict:
    classes = {}
    simple_to_fqcn: dict[str, list[str]] = {}
    interface_impl: dict[str, list[str]] = {}
    for path in sorted(root.glob("ruoyi-*/src/main/java/**/*.java")):
        source = path.read_text(encoding="utf-8", errors="replace")
        match = CLASS.search(source)
        if not match:
            continue
        package = re.search(r"\bpackage\s+([\w.]+)\s*;", source)
        if not package:
            continue
        fqcn = package.group(1) + "." + match.group(1)
        classes[fqcn] = (path, source, match.group(1))
        simple_to_fqcn.setdefault(match.group(1), []).append(fqcn)
        if match.group(2):
            for interface in re.findall(r"\bI\w+Service\b", match.group(2)):
                interface_impl.setdefault(interface, []).append(fqcn)
    graph = {name: set() for name in classes}
    edges = []
    unresolved = []
    for source_name, (path, text, class_name) in classes.items():
        candidates = [(hit.group(1), hit.start()) for hit in FIELD.finditer(text)]
        for constructor in AUTOWIRED_CONSTRUCTOR.finditer(text):
            if constructor.group(1) == class_name:
                for parameter in constructor.group(2).split(","):
                    found = re.match(r"\s*([A-Z]\w+)\s+\w+", parameter)
                    if found:
                        candidates.append((found.group(1), constructor.start()))
        imports = dict(re.findall(r"\bimport\s+(com\.ruoyi\.[\w.]+\.(\w+))\s*;", text))
        imports = {short: full for full, short in imports.items()}
        for dependency, offset in candidates:
            targets = interface_impl.get(dependency)
            if not targets:
                direct = imports.get(dependency)
                targets = [direct] if direct in classes else simple_to_fqcn.get(dependency, [])
            if len(targets) != 1 or targets[0] not in graph:
                unresolved.append({"source": source_name, "dependency": dependency,
                                   "file": str(path.relative_to(root)), "line": text.count("\n", 0, offset) + 1})
                continue
            target = targets[0]
            graph[source_name].add(target)
            edges.append({"source": source_name, "target": target,
                          "file": str(path.relative_to(root)), "line": text.count("\n", 0, offset) + 1})
    cycles = tarjan(graph)
    return {
        "schema": "ruoyicrm.crit02.static-scc.v1",
        "status": "STATIC_SCC_FOUND" if cycles else "ZERO_STATIC_SCC",
        "runtime_startup": "NOT_RUN",
        "certification": "NOT_CERTIFIED",
        "scope": "Resolved @Autowired/@Resource field and explicit @Autowired constructor edges between concrete repository classes",
        "classes": len(classes), "resolved_edges": len(edges),
        "unresolved_edges": unresolved,
        "cycles": cycles,
        "cycle_edges": [edge for edge in edges if any(edge["source"] in c and edge["target"] in c for c in cycles)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    else:
        print(payload)
    return 1 if result["cycles"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
