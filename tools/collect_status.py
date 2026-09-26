#!/usr/bin/env python3
"""Collect the live state of every pipeline into data/status.json.

The page (index.html) renders the "Next" and "Last heartbeat" cells and the
preview pills from this file, so the weekly routine writes DATA, never the
page. Two passes:

  python3 tools/collect_status.py            # repo side: heartbeats, commits, next fire
  python3 tools/collect_status.py --preview trade-journal=in-sync ...   # artifact side, after the Artifact checks

Every fetch failure is recorded as a value ("unreachable"), never raised, so a
single bad request cannot blank the whole status. Sources are the public
repos only: raw.githubusercontent.com for files, api.github.com for commit
dates (unauthenticated, 60/h — this script uses 9).
"""
import argparse, datetime as dt, json, pathlib, sys, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "status.json"
HEARTBEAT = ROOT / "data" / ".last-check"

# key, name, repo, cron (UTC), max heartbeat age in days before it is stale, preview id
PIPELINES = [
    ("tmdv",            "TMDV",            "Omni-TMDV",       "0 11 * * 0",    9,  "3hNqXDiwsssZBe34b6mK73"),
    ("omni-sitecheck",  "OMNI Sitecheck",  "Omni-sitecheck",  "45 15 * * 1",   9,  "KR1dnH91u1qdzhoop4Dqkr"),
    ("ecopm-sitecheck", "ECOPM Sitecheck", "Ecopm-Sitecheck", "0 14 * * 1",    9,  "Gxr48hVPm7YGEuE2947eoZ"),
    ("ecp-ela",         "ECP × ELA",       "ecp-ela-weekly",  "0 14 * * 0",    9,  "22fboAK5NyitZHc4iiVgTx"),
    ("trade-journal",   "Trade Journal",   "Trade-Journal",   "0 4 * * 2-6",   4,  "LgPF5yVUG2J1bfV3M72FQ1"),
    ("gdsh",            "GDSH",            "gdsh-report",     "0 1 * * 1",     9,  "A5DNPFCcerdjgoBk2c5vVd"),
    ("ops-dashboard",   "Ops-Dashboard",   "Ops-Dashboard",   "0 6 1,15 * *",  20, "Ny2dknmJCxADa95gJn6DMx"),
    ("omni-audit",      "Omni-Audit",      "Omni-Audit",      "0 3 1 * *",     35, "BeTHcWt6A7zKN66j51Jr81"),
    ("pipeline-wiring", "Pipeline Wiring", "pipeline-wiring", "0 16 * * 0",    9,  "1jJocxY9ehSu9DJigt9ZmW"),
]
OWNER = "ttrng3"
UA = {"User-Agent": "pipeline-wiring-status/1.0"}


def fetch(url, timeout=20):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read().decode("utf-8", "replace"), r.status
    except urllib.error.HTTPError as e:
        return None, e.code
    except Exception as e:  # DNS, timeout, refused
        return None, str(e)


def cron_field(spec, lo, hi):
    vals = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, step = part.split("/"); step = int(step)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = map(int, part.split("-"))
        else:
            a = b = int(part)
        vals.update(range(a, b + 1, step))
    return vals


def next_fire(cron, now):
    """Next UTC fire time for a 5-field cron, scanning forward minute by minute (bounded to 62 days).
    Standard semantics: when both day-of-month and day-of-week are restricted, either may match."""
    m, h, dom, mon, dow = cron.split()
    M, H, DOM, MON = cron_field(m, 0, 59), cron_field(h, 0, 23), cron_field(dom, 1, 31), cron_field(mon, 1, 12)
    DOW = {d % 7 for d in cron_field(dow, 0, 7)}  # 7 == Sunday == 0
    dom_any, dow_any = dom == "*", dow == "*"
    t = now.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)
    end = t + dt.timedelta(days=62)
    while t < end:
        if t.month in MON and t.hour in H and t.minute in M:
            wd = (t.weekday() + 1) % 7  # python Mon=0 -> cron Sun=0
            dom_ok, dow_ok = t.day in DOM, wd in DOW
            if dom_any and dow_any: ok = True
            elif dom_any: ok = dow_ok
            elif dow_any: ok = dom_ok
            else: ok = dom_ok or dow_ok
            if ok:
                return t
        t += dt.timedelta(minutes=1)
    return None


def parse_ts(s):
    s = s.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return dt.datetime.strptime(s, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            pass
    return None


def collect(now):
    out = []
    for key, name, repo, cron, max_age, preview in PIPELINES:
        row = {"key": key, "name": name, "repo": f"{OWNER}/{repo}", "cron": cron, "maxHeartbeatAgeDays": max_age,
               "preview": {"id": preview, "state": "not checked"}}
        # heartbeat: first line of data/.last-check, timestamp is the first token
        body, st = fetch(f"https://raw.githubusercontent.com/{OWNER}/{repo}/main/data/.last-check")
        if body:
            first = body.strip().splitlines()[0]
            ts = parse_ts(first.split(" ", 1)[0])
            row["heartbeat"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None
            row["heartbeatNote"] = first.split(" ", 1)[1][:160] if " " in first else ""
            row["heartbeatAgeDays"] = round((now - ts).total_seconds() / 86400, 1) if ts else None
            row["fresh"] = (row["heartbeatAgeDays"] is not None and row["heartbeatAgeDays"] <= max_age)
        else:
            row.update(heartbeat=None, heartbeatNote=f"no data/.last-check ({st})", heartbeatAgeDays=None, fresh=False)
        # last commit on main
        body, st = fetch(f"https://api.github.com/repos/{OWNER}/{repo}/commits?per_page=1")
        try:
            c = json.loads(body)[0]["commit"]
            row["lastCommit"] = c["committer"]["date"]
            row["lastCommitMessage"] = c["message"].splitlines()[0][:120]
        except Exception:
            row["lastCommit"] = None; row["lastCommitMessage"] = f"unreachable ({st})"
        # manifest stamp, if the repo has one (used by the preview comparison)
        body, st = fetch(f"https://raw.githubusercontent.com/{OWNER}/{repo}/main/data/index.json")
        stamp = None
        if body:
            try:
                idx = json.loads(body)
                stamp = idx.get("snapshotAt") or idx.get("generatedUtc") or idx.get("generated") or idx.get("asof")
            except Exception:
                stamp = "unparseable"
        row["manifestStamp"] = stamp
        nf = next_fire(cron, now)
        row["nextFireUtc"] = nf.strftime("%Y-%m-%dT%H:%M:%SZ") if nf else None
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="append", default=[], metavar="KEY=STATE[:note]",
                    help="record the artifact-side check for a pipeline (in-sync | behind | unreachable | not-checked)")
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    if a.preview:
        data = json.loads(OUT.read_text()) if OUT.exists() else None
        if not data:
            sys.exit("run the collector first, then record previews")
        by = {p["key"]: p for p in data["pipelines"]}
        for spec in a.preview:
            key, _, rest = spec.partition("=")
            state, _, note = rest.partition(":")
            if key not in by:
                sys.exit(f"unknown pipeline key {key!r}; known: {', '.join(by)}")
            by[key]["preview"].update(state=state.strip(), note=note.strip(), checkedAt=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        data["previewsCheckedAt"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        data = {"generatedUtc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "pipelines": collect(now)}
        HEARTBEAT.write_text(f"{data['generatedUtc']} newest-source=weekly status check, "
                             f"{sum(1 for p in data['pipelines'] if p['fresh'])}/{len(data['pipelines'])} heartbeats fresh\n")
    data["summary"] = {
        "pipelines": len(data["pipelines"]),
        "fresh": sum(1 for p in data["pipelines"] if p.get("fresh")),
        "stale": [p["key"] for p in data["pipelines"] if not p.get("fresh")],
        "previewsInSync": sum(1 for p in data["pipelines"] if p["preview"].get("state") == "in-sync"),
        "previewsBehind": [p["key"] for p in data["pipelines"] if p["preview"].get("state") == "behind"],
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    if a.print or not a.preview:
        for p in data["pipelines"]:
            print(f"{p['name']:<16} hb={str(p.get('heartbeat'))[:10]} age={p.get('heartbeatAgeDays')}d "
                  f"{'fresh' if p.get('fresh') else 'STALE'}  next={str(p.get('nextFireUtc'))[:16]}  preview={p['preview'].get('state')}")
        print(json.dumps(data["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
