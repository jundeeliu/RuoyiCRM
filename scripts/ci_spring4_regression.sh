#!/usr/bin/env bash
set -euo pipefail

java_version=$(java -version 2>&1)
if [[ ! $java_version =~ version\ \"21\. && ! $java_version =~ openjdk\ 21\. ]]; then
  echo "Spring Boot 4 pipeline requires JDK 21" >&2
  exit 2
fi

mvn -B -ntp clean package
python3 scripts/check_java_parameter_metadata.py
python3 scripts/crit04_replay.py check
python3 scripts/crit02_scc_audit.py --output /tmp/ruoyicrm-scc-audit.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
