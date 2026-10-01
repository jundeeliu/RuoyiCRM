#!/usr/bin/env python3
"""Conservative Istio canary rollback; dry-run unless --apply is explicit."""

import argparse
import json
import math
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


PLAN_ID = "ruoyicrm-master-tenant-20261002"
HOST = "ruoyicrm-web.ruoyicrm.svc.cluster.local"
NAME = "ruoyicrm-web-cutover"
NAMESPACE = "ruoyicrm"
STAGES = {1, 10, 50, 100}


class UnsafeState(Exception):
    pass


def validate_endpoint(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise UnsafeState("Prometheus endpoint must be an origin URL")
    if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
        return url.rstrip("/")
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"} and not parsed.username and not parsed.password:
        return url.rstrip("/")
    raise UnsafeState("Prometheus endpoint must be HTTPS or loopback HTTP")


def sample(payload, now, max_age=30):
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise UnsafeState("Prometheus response is malformed")
    if payload.get("status") != "success" or payload.get("data", {}).get("resultType") != "vector":
        raise UnsafeState("Prometheus query did not return a vector")
    result = payload["data"].get("result")
    if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict) or result[0].get("metric") != {}:
        raise UnsafeState("Prometheus query must return one unlabelled aggregate")
    value = result[0].get("value")
    if not isinstance(value, list) or len(value) != 2:
        raise UnsafeState("Prometheus sample missing")
    timestamp, number = float(value[0]), float(value[1])
    if not all(map(math.isfinite, (timestamp, number))) or timestamp > now + 5 or now - timestamp > max_age:
        raise UnsafeState("Prometheus sample is stale or nonfinite")
    if number < 0:
        raise UnsafeState("Prometheus sample is negative")
    return number


def query(base_url, expression, now):
    url = base_url + "/api/v1/query?" + urllib.parse.urlencode({"query": expression})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            raise UnsafeState("Prometheus redirect refused")

    with urllib.request.build_opener(NoRedirect()).open(url, timeout=5) as response:
        if response.status != 200:
            raise UnsafeState("Prometheus returned a non-200 status")
        body = response.read(1_000_001)
        if len(body) > 1_000_000:
            raise UnsafeState("Prometheus response too large")
        payload = json.loads(body)
    return sample(payload, now)


def decision(values, minimum_requests=30):
    requests = values["new_requests_per_minute"]
    errors = values["new_5xx_per_minute"]
    new_p95 = values["new_p95_ms"]
    old_p95 = values["old_p95_ms"]
    if requests < minimum_requests or old_p95 <= 0 or errors > requests:
        return "ROLLBACK", "insufficient or inconsistent telemetry"
    if errors / requests >= 0.05:
        return "ROLLBACK", "new version 5xx ratio >= 5%"
    if new_p95 >= 2 * old_p95:
        return "ROLLBACK", "new version p95 >= 2x legacy"
    return "HOLD", "sampled thresholds below rollback boundary"


def validate_route(route):
    meta = route.get("metadata", {})
    if route.get("kind") != "VirtualService" or route.get("apiVersion") != "networking.istio.io/v1":
        raise UnsafeState("unexpected route kind or API version")
    if meta.get("name") != NAME or meta.get("namespace") != NAMESPACE or meta.get("annotations", {}).get("cutover.ruoyicrm.io/plan-id") != PLAN_ID:
        raise UnsafeState("route identity/ownership mismatch")
    if not meta.get("resourceVersion"):
        raise UnsafeState("route has no resourceVersion")
    spec = route.get("spec", {})
    if spec.get("hosts") != [HOST] or len(spec.get("http", [])) != 1 or set(spec["http"][0]) != {"route"}:
        raise UnsafeState("route has unexpected host or match rules")
    destinations = spec["http"][0]["route"]
    if len(destinations) != 2 or any(set(item) != {"destination", "weight"} for item in destinations):
        raise UnsafeState("route has unexpected destinations")
    for item, subset in zip(destinations, ("legacy", "boot4")):
        if item["destination"] != {"host": HOST, "subset": subset}:
            raise UnsafeState("route destination mismatch")
    old, new = (item["weight"] for item in destinations)
    if type(old) is not int or type(new) is not int or new not in STAGES or old + new != 100:
        raise UnsafeState("route is not at an approved canary stage")
    return destinations


def kubectl(*args, input_text=None):
    result = subprocess.run(["kubectl", *args], input=input_text, text=True,
                            capture_output=True, timeout=10, check=False)
    if result.returncode:
        raise UnsafeState("kubectl verification or replace failed")
    return result.stdout.strip()


def apply_rollback(context, namespace_uid):
    if not context or not namespace_uid:
        raise UnsafeState("exact context and namespace UID are required")
    if kubectl("config", "current-context") != context:
        raise UnsafeState("Kubernetes context mismatch")
    namespace = json.loads(kubectl("--context", context, "get", "namespace", NAMESPACE, "-o", "json"))
    if namespace.get("metadata", {}).get("uid") != namespace_uid:
        raise UnsafeState("Kubernetes namespace UID mismatch")
    route = json.loads(kubectl("--context", context, "-n", NAMESPACE, "get", "virtualservice", NAME, "-o", "json"))
    destinations = validate_route(route)
    destinations[0]["weight"] = 100
    destinations[1]["weight"] = 0
    # resourceVersion is retained: a concurrent change makes replace fail, avoiding stale overwrite.
    kubectl("--context", context, "-n", NAMESPACE, "replace", "-f", "-",
            input_text=json.dumps(route))


def run(config, endpoint, apply, context, namespace_uid, fetch=query, now=None):
    base_url = validate_endpoint(endpoint)
    expressions = config.get("queries", {})
    keys = {"new_requests_per_minute", "new_5xx_per_minute", "new_p95_ms", "old_p95_ms"}
    if set(expressions) != keys or any(not isinstance(value, str) or not value.strip() for value in expressions.values()):
        raise UnsafeState("four exact nonempty PromQL queries are required")
    now = time.time() if now is None else now
    try:
        values = {key: fetch(base_url, expressions[key], now) for key in sorted(keys)}
        verdict, reason = decision(values)
    except (UnsafeState, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        verdict, reason = "ROLLBACK", "telemetry unavailable or invalid: " + type(exc).__name__
    if verdict == "ROLLBACK" and apply:
        apply_rollback(context, namespace_uid)
    return {"decision": verdict, "reason": reason, "applied": verdict == "ROLLBACK" and apply}


def monitor(config, endpoint, apply, context, namespace_uid, interval_seconds=5, evaluate=run, sleep=time.sleep):
    if not 1 <= interval_seconds <= 60:
        raise UnsafeState("watch interval must be 1..60 seconds")
    while True:
        result = evaluate(config, endpoint, apply, context, namespace_uid)
        if result["decision"] != "HOLD":
            return result
        sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("prometheus-queries.json"))
    parser.add_argument("--prometheus-url", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--watch", action="store_true", help="poll until rollback decision; requires supervisor restart policy")
    parser.add_argument("--interval-seconds", type=int, default=5)
    parser.add_argument("--context")
    parser.add_argument("--namespace-uid")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text())
        if args.watch:
            result = monitor(config, args.prometheus_url, args.apply, args.context,
                             args.namespace_uid, args.interval_seconds)
        else:
            result = run(config, args.prometheus_url, args.apply, args.context, args.namespace_uid)
    except (UnsafeState, OSError, ValueError) as exc:
        print(json.dumps({"decision": "BLOCKED", "reason": str(exc), "applied": False}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "HOLD" else 1


if __name__ == "__main__":
    sys.exit(main())
