#!/usr/bin/env python3
"""Collect the live state of every pipeline into data/status.json, daily.

The page (index.html) renders the "Next" and "Last heartbeat" cells and the
preview pills from this file, so the daily routine writes DATA, never the
page. Two passes:

  python3 tools/collect_status.py            # repo side: heartbeats, manifest stamps, next fire
  python3 tools/collect_status.py --preview trade-journal=in-sync ...   # artifact side, after the Artifact checks

Every fetch failure is recorded as a value ("unreachable"), never raised, so a
single bad request cannot blank the whole status. The only source is
raw.githubusercontent.com (public repos, no token). api.github.com is NOT
used: inside a cloud routine it answers 403 for every repo except the one
attached to the session (verified on the first run, 2026-09-26), and the
heartbeat file is the signal anyway.

Each pipeline also gets a band from bands.yaml (plain thresholds): "log" for one
late heartbeat, "diagnose" for a missed run or a heartbeat older than its
watchdog. A diagnose finding writes triage/<yymmdd>-<key>-<kind>/intent.md for
Ty to triage, once: nothing more is written while a folder for that pipeline is open.
"Late" and "missed" are measured from the first scheduled run after the heartbeat.
"""
import argparse, datetime as dt, json, pathlib, sys, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "status.json"
HEARTBEAT = ROOT / "data" / ".last-check"
BANDS = ROOT / "bands.yaml"   # JSON syntax, which is valid YAML: no PyYAML needed
TRIAGE = ROOT / "triage"

# key, name, repo, cron (UTC), max heartbeat age in days before it is stale.
# Preview ids are not kept in this public repo: the routine prompt holds them (Ty, 2026-09-29).
PIPELINES = [
    ("tmdv",            "TMDV",            "Omni-TMDV",       "0 11 * * 0",    9),
    ("omni-sitecheck",  "OMNI Sitecheck",  "Omni-sitecheck",  "45 15 * * 1",   9),
    ("ecopm-sitecheck", "ECOPM Sitecheck", "Ecopm-Sitecheck", "0 14 * * 1",    9),
    ("ecp-ela",         "ECP × ELA",       "ecp-ela-weekly",  "0 14 * * 0",    9),
    ("trade-journal",   "Trade Journal",   "Trade-Journal",   "0 4 * * 2-6",   4),
    ("gdsh",            "GDSH",            "gdsh-report",     "0 1 * * 1",     9),
    ("ops-dashboard",   "Ops-Dashboard",   "Ops-Dashboard",   "0 6 1,15 * *",  20),
    ("omni-audit",      "Omni-Audit",      "Omni-Audit",      "0 3 1 * *",     35),
    ("pipeline-wiring", "Pipeline Wiring", "pipeline-wiring", "0 16 * * *",    9),
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


def fires_at(cron):
    """Predicate: does a 5-field cron fire at this UTC minute?
    Standard semantics: when both day-of-month and day-of-week are restricted, either may match."""
    m, h, dom, mon, dow = cron.split()
    M, H, DOM, MON = cron_field(m, 0, 59), cron_field(h, 0, 23), cron_field(dom, 1, 31), cron_field(mon, 1, 12)
    DOW = {d % 7 for d in cron_field(dow, 0, 7)}  # 7 == Sunday == 0
    dom_any, dow_any = dom == "*", dow == "*"

    def ok(t):
        if not (t.month in MON and t.hour in H and t.minute in M):
            return False
        wd = (t.weekday() + 1) % 7  # python Mon=0 -> cron Sun=0
        dom_ok, dow_ok = t.day in DOM, wd in DOW
        if dom_any and dow_any: return True
        if dom_any: return dow_ok
        if dow_any: return dom_ok
        return dom_ok or dow_ok
    return ok


def next_fire(cron, now):
    """Next UTC fire time, scanning forward minute by minute (bounded to 62 days)."""
    ok = fires_at(cron)
    t = now.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)
    end = t + dt.timedelta(days=62)
    while t < end:
        if ok(t):
            return t
        t += dt.timedelta(minutes=1)
    return None


def prev_fire(cron, now):
    """Latest UTC fire time at or before now, scanning back minute by minute (bounded to 62 days)."""
    ok = fires_at(cron)
    t = now.replace(second=0, microsecond=0)
    end = t - dt.timedelta(days=62)
    while t > end:
        if ok(t):
            return t
        t -= dt.timedelta(minutes=1)
    return None


def parse_ts(s):
    s = s.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return dt.datetime.strptime(s, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            pass
    return None


def band(row, ts, st, now, bands):
    """(band, kind, reason) for one pipeline: ok, log (late heartbeat or a network error) or diagnose.
    st is the heartbeat fetch's HTTP status (int) or the network error (str)."""
    if ts is None and (isinstance(st, str) or st == 429 or st >= 500):
        return "log", "unreadable", f"heartbeat could not be fetched ({'network error' if isinstance(st, str) else 'HTTP ' + str(st)}; retried tomorrow)"
    if ts is None:
        return "diagnose", "no-heartbeat", f"no readable heartbeat (HTTP {st}, or a timestamp that does not parse)"
    if row["heartbeatAgeDays"] > row["maxHeartbeatAgeDays"]:
        return ("diagnose", "stale", f"heartbeat is {row['heartbeatAgeDays']}d old; "
                f"its watchdog is {row['maxHeartbeatAgeDays']}d")
    pf = next_fire(row["cron"], ts)  # the first scheduled run after the heartbeat
    if pf and pf < now - dt.timedelta(hours=bands["lateGraceHours"]):
        hours = (now - pf).total_seconds() / 3600
        if hours > bands["missedAfterHours"]:
            return ("diagnose", "missed-run", f"scheduled run {pf:%Y-%m-%dT%H:%MZ} left no heartbeat "
                    f"after {hours:.1f}h (limit {bands['missedAfterHours']}h)")
        return "log", "late", f"scheduled run {pf:%Y-%m-%dT%H:%MZ} has no heartbeat yet ({hours:.1f}h)"
    return "ok", "", ""


def write_triage(rows, now):
    """One triage/<yymmdd>-<key>-<kind>/intent.md per diagnose finding. Nothing is written while any
    triage folder for the same pipeline is open, so one outage (missed run, then stale) is one item.
    Status only: names, times and thresholds, never a heartbeat note or any pipeline's data."""
    written = []
    for r in rows:
        if r["band"] != "diagnose":
            continue
        slug = f"{r['key']}-{r['bandKind']}"
        if any(any(TRIAGE.glob(f"*-{r['key']}-{k}/intent.md")) for k in ("stale", "missed-run", "no-heartbeat")):
            continue
        d = TRIAGE / f"{now:%y%m%d}-{slug}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "intent.md").write_text(
            f"# Intent (open, from the daily check)\n\n"
            f"Status: open. Written by `tools/collect_status.py` at {now:%Y-%m-%dT%H:%M:%SZ}. "
            f"Ty triages: accept (it becomes a work item) or dismiss with a reason, which tunes `bands.yaml`.\n\n"
            f"**{r['name']}** (`{r['repo']}`): {r['bandReason']}.\n\n"
            f"- Heartbeat: {r['heartbeat'] + ' (' + str(r['heartbeatAgeDays']) + 'd old)' if r['heartbeat'] else 'none readable'}\n"
            f"- Cron (UTC): `{r['cron']}`; watchdog {r['maxHeartbeatAgeDays']}d\n\n"
            f"The check only reports. It changed nothing; the fix, if any, comes as a PR.\n")
        written.append(str(d.relative_to(ROOT) / "intent.md"))
    return written


def collect(now):
    try:
        bands = json.loads(BANDS.read_text())
        bands["lateGraceHours"], bands["missedAfterHours"]
    except Exception as e:  # a bad hand edit must not blank the whole status
        print(f"WARNING bands.yaml unreadable ({e}); using 2 h / 24 h")
        bands = {"lateGraceHours": 2, "missedAfterHours": 24}
    out = []
    for key, name, repo, cron, max_age in PIPELINES:
        row = {"key": key, "name": name, "repo": f"{OWNER}/{repo}", "cron": cron, "maxHeartbeatAgeDays": max_age,
               "preview": {"state": "not checked"}}
        # heartbeat: first line of data/.last-check, timestamp is the first token
        body, st = fetch(f"https://raw.githubusercontent.com/{OWNER}/{repo}/main/data/.last-check")
        hb_st = st
        if body:
            lines = body.strip().splitlines()
            first = lines[0] if lines else ""
            ts = parse_ts(first.split(" ", 1)[0])
            row["heartbeat"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None
            row["heartbeatAgeDays"] = round((now - ts).total_seconds() / 86400, 1) if ts else None
            row["fresh"] = (row["heartbeatAgeDays"] is not None and row["heartbeatAgeDays"] <= max_age)
        else:
            ts = None
            row.update(heartbeat=None, heartbeatAgeDays=None, fresh=False)
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
        row["band"], row["bandKind"], row["bandReason"] = band(row, ts, hb_st, now, bands)
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="append", default=[], metavar="KEY=STATE[:note]",
                    help="record the artifact-side check for a pipeline (in-sync | behind | unreachable | not-checked)")
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    triage = []
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
        triage = write_triage(data["pipelines"], now)
        HEARTBEAT.write_text(f"{data['generatedUtc']} newest-source=daily status check, "
                             f"{sum(1 for p in data['pipelines'] if p['fresh'])}/{len(data['pipelines'])} heartbeats fresh\n")
    data["summary"] = {
        "pipelines": len(data["pipelines"]),
        "fresh": sum(1 for p in data["pipelines"] if p.get("fresh")),
        "stale": [p["key"] for p in data["pipelines"] if not p.get("fresh")],
        "previewsInSync": sum(1 for p in data["pipelines"] if p["preview"].get("state") == "in-sync"),
        "previewsBehind": [p["key"] for p in data["pipelines"] if p["preview"].get("state") == "behind"],
        "logOnly": [p["key"] for p in data["pipelines"] if p.get("band") == "log"],
        "diagnose": [p["key"] for p in data["pipelines"] if p.get("band") == "diagnose"],
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    if a.print or not a.preview:
        for p in data["pipelines"]:
            print(f"{p['name']:<16} hb={str(p.get('heartbeat'))[:10]} age={p.get('heartbeatAgeDays')}d "
                  f"{'fresh' if p.get('fresh') else 'STALE'}  next={str(p.get('nextFireUtc'))[:16]}  preview={p['preview'].get('state')}"
                  f"  band={p.get('band')}{' (' + p['bandReason'] + ')' if p.get('bandReason') else ''}")
        print(json.dumps(data["summary"], ensure_ascii=False))
        for f in triage:
            print("triage written:", f)


if __name__ == "__main__":
    main()
