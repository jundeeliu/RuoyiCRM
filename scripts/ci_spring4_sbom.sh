#!/usr/bin/env bash
set -euo pipefail

mvn -B -ntp org.cyclonedx:cyclonedx-maven-plugin:2.9.3:makeAggregateBom \
  -DoutputFormat=json -DoutputReactorProjects=false
python3 - <<'PY'
import json
from pathlib import Path

bom = json.loads(Path('target/bom.json').read_text(encoding='utf-8'))
if bom.get('bomFormat') != 'CycloneDX' or not bom.get('components'):
    raise SystemExit('Aggregate CycloneDX SBOM is missing components')
print(f"SBOM components: {len(bom['components'])}")
PY
python3 scripts/crit_static_scan.py --bom target/bom.json --output target/crit-static-scan.json
