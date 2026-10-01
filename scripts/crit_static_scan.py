#!/usr/bin/env python3
"""Reproducible, bounded CRIT-06/07/08/09 source and resolved-SBOM inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA_IMPORT = re.compile(r"\bimport\s+(javax\.(?:servlet|validation|annotation)|com\.alibaba\.fastjson)\b")
JPA_QUERY = re.compile(r'(?:@Query|createQuery|createNativeQuery)\s*\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"')
BARE_POSITIONAL = re.compile(r"\?(?!\d|[|&?])")


def scan(root: Path, bom_path: Path) -> dict:
    findings: list[dict[str, str]] = []
    java_files = sorted(root.glob("ruoyi-*/src/main/java/**/*.java"))
    xml_files = sorted(root.glob("ruoyi-*/src/main/resources/**/*.xml"))
    pom_files = [root / "pom.xml", *sorted(root.glob("ruoyi-*/pom.xml"))]
    if not java_files or not bom_path.is_file():
        raise ValueError("Main Java source or aggregate resolved SBOM is missing")
    digest = hashlib.sha256()

    def add(code: str, path: Path) -> None:
        findings.append({"code": code, "path": str(path.relative_to(root))})

    for path in [*java_files, *xml_files, *pom_files]:
        data = path.read_bytes()
        digest.update(str(path.relative_to(root)).encode() + b"\0" + hashlib.sha256(data).digest())
        source = data.decode("utf-8")
        if path.suffix == ".java":
            if re.search(r"\bWebSecurityConfigurerAdapter\b", source):
                add("LEGACY_SECURITY_ADAPTER", path)
            if JAVA_IMPORT.search(source):
                add("LEGACY_OR_UNSAFE_IMPORT", path)
            if "@ImportResource" in source:
                add("SPRING_XML_IMPORT", path)
            if "CookieCsrfTokenRepository" in source and "withHttpOnlyFalse()" in source:
                add("UNREVIEWED_CSRF_COOKIE", path)
            for match in JPA_QUERY.finditer(source):
                if BARE_POSITIONAL.search(match.group(1)):
                    add("UNINDEXED_JPA_PARAMETER", path)
        elif path.name == "pom.xml":
            document = ET.fromstring(source)
            for dep in document.iter():
                if dep.tag.rsplit("}", 1)[-1] != "dependency":
                    continue
                fields = {child.tag.rsplit("}", 1)[-1]: (child.text or "") for child in dep}
                group, artifact = fields.get("groupId", ""), fields.get("artifactId", "")
                if group.startswith("com.netflix.") or "spring-cloud-starter-netflix-" in artifact:
                    add("NETFLIX_DECLARED", path)
                if group == "com.alibaba" and artifact == "fastjson":
                    add("FASTJSON1_DECLARED", path)
        elif path.suffix == ".xml":
            if re.search(r"<\s*(?:beans:)?beans\b|http://www\.springframework\.org/schema/beans", source):
                add("SPRING_BEAN_XML", path)
            if "${params.dataScope}" in source:
                add("RAW_DATA_SCOPE_SQL", path)

    bom_bytes = bom_path.read_bytes()
    bom = json.loads(bom_bytes)
    if bom.get("bomFormat") != "CycloneDX" or not isinstance(bom.get("components"), list):
        raise ValueError("Invalid aggregate CycloneDX SBOM")
    for component in bom["components"]:
        group, artifact = component.get("group", ""), component.get("name", "")
        if group.startswith("com.netflix.") or "spring-cloud-starter-netflix-" in artifact:
            findings.append({"code": "NETFLIX_RESOLVED", "path": component.get("purl", artifact)})
        if group == "com.alibaba" and artifact == "fastjson":
            findings.append({"code": "FASTJSON1_RESOLVED", "path": component.get("purl", artifact)})

    return {
        "schema": "ruoyicrm.local-crit-static.v1",
        "source_sha256": digest.hexdigest(),
        "sbom_sha256": hashlib.sha256(bom_bytes).hexdigest(),
        "java_files": len(java_files),
        "xml_files": len(xml_files),
        "pom_files": len(pom_files),
        "resolved_components": len(bom["components"]),
        "findings": findings,
        "status": "LOCAL_STATIC_ZERO_FINDINGS" if not findings else "BLOCKED",
        "external_evidence": "NOT_RUN",
        "certification": "NOT_CERTIFIED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--bom", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    bom = args.bom or root / "target/bom.json"
    report = scan(root, bom)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "LOCAL_STATIC_ZERO_FINDINGS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
