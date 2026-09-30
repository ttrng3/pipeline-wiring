#!/usr/bin/env python3
"""Offline check of the bands and the triage folder (no network, nothing in the repo is written).

    python3 tools/test_bands.py

Plants heartbeats for all nine pipelines through a fake fetch, in a temp folder:
  clean day      -> every band ok, no triage file
  one stale      -> exactly one triage intent.md; a second run adds none
  one missed run -> diagnose (missed-run); a run still inside the grace -> log only
"""
import contextlib, datetime as dt, io, json, pathlib, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import collect_status as cs

NOW = dt.datetime(2026, 10, 7, 16, 0, tzinfo=dt.timezone.utc)  # a Wednesday, the daily run's minute


def fake_fetch(heartbeats):
    """A heartbeat value may also be an int (HTTP status) or a str (network error) to plant a failed fetch."""
    def fetch(url, timeout=20):
        repo = url.split("/")[4]
        if url.endswith("/data/.last-check"):
            v = heartbeats[repo]
            if isinstance(v, bytes):  # a raw file body, e.g. blank or a bad timestamp
                return v.decode(), 200
            if isinstance(v, (int, str)):
                return None, v
            return v.strftime("%Y-%m-%dT%H:%M:%SZ") + " newest-source=test", 200
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
        cs.BANDS = pathlib.Path(tmp) / "bands.yaml"  # fixed 2 h / 24 h, whatever the real file is tuned to
        cs.BANDS.write_text('{"lateGraceHours": 2, "missedAfterHours": 24}')

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

        # A failed fetch: a network error is log only and writes nothing; a 404 is diagnose
        hb = at(NOW); hb["Omni-Audit"] = "timed out"
        rows, written = run(hb)
        by = {r["key"]: r for r in rows}
        check("network error: omni-audit log/unreadable, no triage", (by["omni-audit"]["band"], by["omni-audit"]["bandKind"]) == ("log", "unreadable") and written == [])
        hb = at(NOW); hb["Omni-Audit"] = 404
        rows, written = run(hb)
        by = {r["key"]: r for r in rows}
        check("404: omni-audit diagnose/no-heartbeat, one triage", by["omni-audit"]["bandKind"] == "no-heartbeat" and len(written) == 1)
        for code in (429, 503):
            hb = at(NOW); hb["gdsh-report"] = code
            rows, written = run(hb)
            by = {r["key"]: r for r in rows}
            check(f"HTTP {code}: gdsh log/unreadable, no triage", by["gdsh"]["bandKind"] == "unreadable" and written == [])

        for raw in (b"\n", b"not-a-time newest-source=x\n"):
            hb = at(NOW); hb["Ecopm-Sitecheck"] = raw
            rows, _ = run(hb)
            by = {r["key"]: r for r in rows}
            check(f"body {raw!r}: ecopm diagnose/no-heartbeat, run completes", len(rows) == 9 and by["ecopm-sitecheck"]["bandKind"] == "no-heartbeat")

        # A bad hand edit of bands.yaml falls back to the defaults instead of failing the run
        cs.BANDS.write_text("lateGraceHours: 3  # a YAML edit\n")
        rows, _ = run(at(NOW))
        check("bad bands.yaml: run completes, nine rows banded", len(rows) == 9 and all(r["band"] == "ok" for r in rows))

        # The routine commits what main() prints as "triage written:"; check that line and the summary
        cs.BANDS.write_text('{"lateGraceHours": 2, "missedAfterHours": 24}')
        cs.OUT, cs.HEARTBEAT = pathlib.Path(tmp) / "status.json", pathlib.Path(tmp) / ".last-check"
        for d in cs.TRIAGE.glob("*"):
            for f in d.glob("*"):
                f.unlink()
            d.rmdir()
        hb = at(NOW); hb["Omni-TMDV"] = NOW - dt.timedelta(days=12)
        cs.fetch = fake_fetch(hb)
        real_dt, argv = cs.dt, sys.argv
        class _dt(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return NOW
        cs.dt = type("m", (), {"datetime": _dt, "timedelta": dt.timedelta, "timezone": dt.timezone})
        sys.argv = ["collect_status.py"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cs.main()
        cs.dt, sys.argv = real_dt, argv
        s = json.loads(cs.OUT.read_text())["summary"]
        check("main(): prints 'triage written: triage/…-tmdv-stale/intent.md'", "triage written: triage/261007-tmdv-stale/intent.md" in out.getvalue())
        check("main(): summary.diagnose lists tmdv, logOnly empty", s["diagnose"] == ["tmdv"] and s["logOnly"] == [])

    print(f"{'ALL PASS' if not fails else str(fails) + ' FAILED'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
