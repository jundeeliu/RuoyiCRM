#!/usr/bin/env bash
set -euo pipefail

state=$(python3 scripts/crit10_stack.py prepare)
cleanup() {
  python3 scripts/crit10_stack.py down --state "$state"
}
trap cleanup EXIT
python3 scripts/crit10_stack.py up --state "$state"
export RUOYICRM_CRIT10_STATE="$state"
mvn -B -ntp -pl ruoyi-framework -am \
  -Dtest=DisposableMySqlTenantRoutingTest \
  -Dsurefire.failIfNoSpecifiedTests=false test
