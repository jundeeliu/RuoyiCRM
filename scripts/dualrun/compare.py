"""Strict HTTP/JSON differential comparison with explicit dynamic JSON pointers."""

from __future__ import annotations

import base64
import copy
import datetime as dt
import json
import re
import uuid


MAX_BODY = 2 * 1024 * 1024
KINDS = frozenset({"timestamp", "uuid", "token", "trace_id"})
TRACE = re.compile(r"(?:[0-9a-fA-F]{16}|[0-9a-fA-F]{32})\Z")
JWT_PART = re.compile(r"[A-Za-z0-9_-]+\Z")
TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\d[Tt]\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)\Z")


class ComparisonError(ValueError):
    pass


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ComparisonError("duplicate JSON object key")
        obj[key] = value
    return obj


def parse_body(raw):
    if not isinstance(raw, (bytes, bytearray)) or len(raw) > MAX_BODY:
        raise ComparisonError("body must be bytes within 2 MiB")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(ComparisonError("nonfinite JSON number")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComparisonError("body is not valid UTF-8 JSON") from exc


def pointer_tokens(pointer):
    if not isinstance(pointer, str) or not pointer.startswith("/") or pointer == "/":
        raise ComparisonError("rule needs a non-root JSON pointer")
    tokens = pointer[1:].split("/")
    for token in tokens:
        if token in {"", "*", "-"} or re.search(r"~(?![01])", token):
            raise ComparisonError("ambiguous or wildcard JSON pointer")
    return [token.replace("~1", "/").replace("~0", "~") for token in tokens]


def slot(document, pointer):
    node = document
    tokens = pointer_tokens(pointer)
    for token in tokens[:-1]:
        if type(node) is dict and token in node:
            node = node[token]
        elif type(node) is list and token.isdecimal() and str(int(token)) == token and int(token) < len(node):
            node = node[int(token)]
        else:
            raise ComparisonError("allowlisted path is missing or has wrong container type")
    key = tokens[-1]
    if type(node) is dict and key in node:
        return node, key
    if type(node) is list and key.isdecimal() and str(int(key)) == key and int(key) < len(node):
        return node, int(key)
    raise ComparisonError("allowlisted path is missing or has wrong container type")


def valid_uuid(value):
    if type(value) is not str:
        raise ComparisonError("UUID field must be a string")
    try:
        parsed = uuid.UUID(value)
    except ValueError as exc:
        raise ComparisonError("UUID field has invalid format") from exc
    if value.lower() not in {parsed.hex, str(parsed)}:
        raise ComparisonError("UUID field has invalid format")
    return "<dynamic:uuid>"


def valid_timestamp(value):
    if type(value) is not str or not TIMESTAMP.fullmatch(value):
        raise ComparisonError("timestamp must be ISO 8601 with timezone")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ComparisonError("timestamp has invalid calendar value") from exc
    if parsed.tzinfo is None:
        raise ComparisonError("timestamp lacks timezone")
    return "<dynamic:timestamp>"


def decode_jwt_part(part):
    if not JWT_PART.fullmatch(part):
        raise ComparisonError("JWT has invalid base64url segment")
    try:
        return base64.b64decode(part + "=" * (-len(part) % 4), altchars=b"-_", validate=True)
    except ValueError as exc:
        raise ComparisonError("JWT segment cannot be decoded") from exc


def valid_token(value):
    if type(value) is not str or len(value) > 8192:
        raise ComparisonError("token must be a bounded JWT string")
    parts = value.split(".")
    if len(parts) != 3:
        raise ComparisonError("token is not a signed JWT")
    try:
        header = json.loads(decode_jwt_part(parts[0]), object_pairs_hook=unique_object)
        claims = json.loads(decode_jwt_part(parts[1]), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComparisonError("JWT header/payload malformed") from exc
    if type(header) is not dict or header.get("alg") != "HS512" or type(claims) is not dict:
        raise ComparisonError("JWT algorithm or claims mismatch")
    if len(decode_jwt_part(parts[2])) != 64:
        raise ComparisonError("JWT HS512 signature has wrong size")
    if type(claims.get("tenant")) is not str or not claims["tenant"]:
        raise ComparisonError("RuoyiCRM tenant claim missing")
    claims["login_user_key"] = valid_uuid(claims.get("login_user_key"))
    return {"header": header, "claims": claims, "signature": "<dynamic:hs512-signature>"}


def canonical(value, kind):
    if kind == "uuid":
        return valid_uuid(value)
    if kind == "timestamp":
        return valid_timestamp(value)
    if kind == "trace_id":
        if type(value) is not str or not TRACE.fullmatch(value):
            raise ComparisonError("trace ID must be 16 or 32 hex characters")
        return "<dynamic:trace_id>"
    if kind == "token":
        return valid_token(value)
    raise ComparisonError("unsupported dynamic field kind")


def canonicalize(document, rules):
    if type(rules) is not list:
        raise ComparisonError("rules must be a list")
    result = copy.deepcopy(document)
    seen = set()
    for rule in rules:
        if type(rule) is not dict or set(rule) != {"path", "kind"} or rule["kind"] not in KINDS:
            raise ComparisonError("rule must contain exact path and supported kind")
        if rule["path"] in seen:
            raise ComparisonError("duplicate allowlisted path")
        if any(rule["path"].startswith(old + "/") or old.startswith(rule["path"] + "/") for old in seen):
            raise ComparisonError("overlapping allowlisted paths")
        seen.add(rule["path"])
        parent, key = slot(result, rule["path"])
        parent[key] = canonical(parent[key], rule["kind"])
    return result


def same_typed_value(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(same_typed_value(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(same_typed_value(a, b) for a, b in zip(left, right))
    return left == right


def compare_http(left, right, rules):
    """Return a bounded result; malformed or overbroad rules raise ComparisonError."""
    for response in (left, right):
        if type(response) is not dict or set(response) != {"status", "content_type", "body"}:
            raise ComparisonError("response requires exact status, content_type, body")
        if type(response["status"]) is not int or not 100 <= response["status"] <= 599:
            raise ComparisonError("HTTP status invalid")
        if type(response["content_type"]) is not str or response["content_type"].split(";", 1)[0].strip().lower() != "application/json":
            raise ComparisonError("only application/json responses can be canonicalized")
    if left["status"] != right["status"]:
        return {"equal": False, "reason": "HTTP_STATUS"}
    if left["content_type"].lower() != right["content_type"].lower():
        return {"equal": False, "reason": "CONTENT_TYPE"}
    a = canonicalize(parse_body(left["body"]), rules)
    b = canonicalize(parse_body(right["body"]), rules)
    equal = same_typed_value(a, b)
    return {"equal": equal, "reason": None if equal else "JSON_BEHAVIOR_DRIFT"}
