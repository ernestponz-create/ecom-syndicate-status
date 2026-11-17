#!/usr/bin/env python3
"""Free status checks for The Ecom Syndicate. Writes data/status.json and data/alerts.json.
Private URLs and keys come only from environment secrets and are never written out or printed."""
import json, os, time, urllib.request, urllib.error, datetime, ssl

FAILS_BEFORE_ALERT = 2
now = datetime.datetime.now(datetime.timezone.utc)
mons = json.load(open("monitors.json"))
try:
    prev = json.load(open("data/status.json"))
except Exception:
    prev = {"monitors": {}}
out = {"checked_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "monitors": {}}
alerts = []

def check(m):
    url = m.get("url") or os.environ.get(m.get("url_secret", ""), "")
    if not url:
        return "not configured", None, None
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ecom-syndicate-status"})
    for h, sec in (m.get("header_secret") or {}).items():
        v = os.environ.get(sec, "")
        if v:
            req.add_header(h, v)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=m.get("timeout", 30), context=ssl.create_default_context()) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:  # never record the message: it can contain the address
        return "down", None, type(e).__name__
    ms = int((time.time() - t0) * 1000)
    return ("up" if code in m["expect"] else "down"), ms, f"HTTP {code}"

for m in mons:
    p = prev.get("monitors", {}).get(m["id"], {})
    if "daily_utc_hour" in m and now.hour != m["daily_utc_hour"] and p.get("last_checked"):
        out["monitors"][m["id"]] = p  # not due; keep the last result
        continue
    state, ms, detail = check(m)
    fails = (p.get("fails", 0) + 1) if state == "down" else 0
    rec = {"name": m["name"], "state": state, "response_ms": ms, "detail": detail, "fails": fails,
           "last_checked": out["checked_at"], "note": m.get("note", ""),
           "alerting": p.get("alerting", False),
           "since": p.get("since") if p.get("state") == state else out["checked_at"]}
    if state == "down" and fails >= FAILS_BEFORE_ALERT and not rec["alerting"]:
        rec["alerting"] = True; alerts.append({"id": m["id"], "name": m["name"], "event": "down", "detail": detail})
    if state == "up" and rec["alerting"]:
        rec["alerting"] = False; alerts.append({"id": m["id"], "name": m["name"], "event": "recovered", "detail": detail})
    out["monitors"][m["id"]] = rec
    print(f'{m["name"]}: {state} ({detail})')

os.makedirs("data", exist_ok=True)
json.dump(out, open("data/status.json", "w"), indent=1)
json.dump(alerts, open("data/alerts.json", "w"))
