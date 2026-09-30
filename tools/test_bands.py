#!/usr/bin/env python3
"""Offline check of the bands and the triage folder (no network, nothing in the repo is written).

    python3 tools/test_bands.py

Plants heartbeats for all nine pipelines through a fake fetch, in a temp folder:
  clean day      -> every band ok, no triage file
  one stale      -> exactly one triage intent.md; a second run adds none
  one missed run -> diagnose (missed-run); a run still inside the grace -> log only
"""
import datetime as dt, pathlib, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import collect_status as cs

NOW = dt.datetime(2026, 10, 7, 16, 0, tzinfo=dt.timezone.utc)  # a Wednesday, the daily run's minute


def fake_fetch(heartbeats):
    def fetch(url, timeout=20):
        repo = url.split("/")[4]
        if url.endswith("/data/.last-check"):
            return heartbeats[repo].strftime("%Y-%m-%dT%H:%M:%SZ") + " newest-source=test", 200
        return None, 404
    return fetch


def fresh_heartbeats():
    """Each pipeline's heartbeat five minutes after its latest run before NOW: a clean day. For Pipeline
    Wiring that is yesterday's run, as in real life (its own heartbeat is read from the remote repo)."""
    return at(NOW)


def at(now):
    return {repo: cs.prev_fire(cron, now - dt.timedelta(minutes=1)) + dt.timedelta(minutes=5)
            for _, _, repo, cron, _ in cs.PIPELINES}


def run(heartbeats, now=NOW):
    cs.fetch = fake_fetch(heartbeats)
    rows = cs.collect(now)
    return rows, cs.write_triage(rows, now)


def main():
    fails = 0

    def check(name, cond):
        nonlocal fails
        print(("PASS " if cond else "FAIL ") + name)
        fails += 0 if cond else 1

    with tempfile.TemporaryDirectory() as tmp:
        cs.TRIAGE = pathlib.Path(tmp) / "triage"
        cs.ROOT = pathlib.Path(tmp)

        rows, written = run(fresh_heartbeats())
        check("clean day: all nine bands ok", [r["band"] for r in rows] == ["ok"] * 9)
        check("clean day: no triage file", written == [] and not cs.TRIAGE.exists())

        hb = fresh_heartbeats(); hb["Omni-TMDV"] = NOW - dt.timedelta(days=12)  # watchdog 9d
        rows, written = run(hb)
        by = {r["key"]: r for r in rows}
        check("stale: tmdv diagnose/stale", (by["tmdv"]["band"], by["tmdv"]["bandKind"]) == ("diagnose", "stale"))
        check("stale: others ok", all(r["band"] == "ok" for r in rows if r["key"] != "tmdv"))
        files = sorted(cs.TRIAGE.glob("*/intent.md"))
        check("stale: exactly one triage intent.md", len(written) == 1 and len(files) == 1)
        body = files[0].read_text() if files else ""
        check("stale: intent is status only (no heartbeat note)", "newest-source" not in body and "TMDV" in body)
        _, again = run(hb)
        check("stale: second run writes none", again == [] and len(list(cs.TRIAGE.glob("*/intent.md"))) == 1)

        monday = dt.datetime(2026, 10, 5, 16, 0, tzinfo=dt.timezone.utc)  # 26h after ECP x ELA fired
        hb = at(monday)
        hb["ecp-ela-weekly"] = dt.datetime(2026, 9, 27, 14, 5, tzinfo=dt.timezone.utc)  # last week's run: 8.1d < watchdog 9d
        rows, _ = run(hb, monday)
        by = {r["key"]: r for r in rows}
        check("missed run: ecp-ela diagnose/missed-run", (by["ecp-ela"]["band"], by["ecp-ela"]["bandKind"]) == ("diagnose", "missed-run"))

        sunday = dt.datetime(2026, 10, 4, 17, 0, tzinfo=dt.timezone.utc)  # 3h after ECP x ELA fired
        hb = at(sunday)
        hb["ecp-ela-weekly"] = sunday - dt.timedelta(days=7)
        rows, _ = run(hb, sunday)
        by = {r["key"]: r for r in rows}
        check("late: ecp-ela log only, 3h after its fire", (by["ecp-ela"]["band"], by["ecp-ela"]["bandKind"]) == ("log", "late"))

        # Daily pipeline: Wednesday 04:05 heartbeat, Thursday's run missed, checked Friday 16:00
        friday = dt.datetime(2026, 10, 9, 16, 0, tzinfo=dt.timezone.utc)
        hb = at(friday)
        hb["Trade-Journal"] = dt.datetime(2026, 10, 7, 4, 5, tzinfo=dt.timezone.utc)
        rows, _ = run(hb, friday)
        by = {r["key"]: r for r in rows}
        check("missed run, daily: trade-journal diagnose on Friday", (by["trade-journal"]["band"], by["trade-journal"]["bandKind"]) == ("diagnose", "missed-run"))

        # This page's own daily run: yesterday's heartbeat is on time, whatever the start delay
        for delay in (0, 1, 3, 40):
            now = NOW + dt.timedelta(minutes=delay)
            rows, _ = run(at(NOW), now)
            by = {r["key"]: r for r in rows}
            check(f"self, start +{delay}min: pipeline-wiring ok", by["pipeline-wiring"]["band"] == "ok")
        hb = at(NOW); hb["pipeline-wiring"] -= dt.timedelta(days=1)  # yesterday's run left nothing
        rows, _ = run(hb, NOW + dt.timedelta(minutes=2))
        by = {r["key"]: r for r in rows}
        check("self, one daily run missing: pipeline-wiring diagnose", by["pipeline-wiring"]["bandKind"] == "missed-run")

        # One outage opens one item: missed-run open, then the same pipeline goes stale
        before = len(list(cs.TRIAGE.glob("*/intent.md")))
        hb = at(NOW); hb["Trade-Journal"] = NOW - dt.timedelta(days=6)  # watchdog 4d
        _, written = run(hb)
        check("one item per pipeline: stale after missed-run writes none", written == [] and len(list(cs.TRIAGE.glob("*/intent.md"))) == before)

    print(f"{'ALL PASS' if not fails else str(fails) + ' FAILED'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
