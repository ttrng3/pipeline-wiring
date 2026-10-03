#!/usr/bin/env python3
"""Machine half of verification/wiring.md: is the live page what main says, and is main sound?

Run from an up-to-date checkout of main, outside the daily run (16:00 UTC):
  git pull --ff-only && python3 tools/verify_live.py --forbid WORD [WORD ...]

--forbid takes the nine preview ids (from the status routine's prompt) and any person's handle that
must never appear. The runner supplies them at run time so the repo never holds them. Without them
the forbidden-word check fails rather than passing unchecked.

Prints one JSON object of verdicts and exits 0 only when every verdict is true.
Matches are reported by count and file, never by value.
"""
import argparse, ast, datetime as dt, glob, hashlib, json, pathlib, re, subprocess, sys, time, unicodedata, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = "https://ttrng3.github.io/pipeline-wiring/"
SERVED = ["index.html", "starter-story.html", "learning-matrix.html", "data/status.json"]
# Tracked but never served (.pages-allow); each must exist on main and answer 404 live.
PRIVATE = ["README.md", "CLAUDE.md", "REVIEW.md", "bands.yaml", "data/.last-check", "tools/collect_status.py",
           "tools/build-fragment.py", "tools/test_bands.py", "tools/verify_live.py", "verification/wiring.md",
           ".pages-allow"]
# Storage links, full email addresses, bare handles ("name@"), and routine trigger ids.
TRACES = re.compile(r"/personal/|sharepoint\.com|1drv\.ms|[\w.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|\b[a-z][a-z0-9._-]{2,}@(?![\w-])|\btrig_[A-Za-z0-9]{8,}", re.I)
MAX_HOURS = 26  # the on-call's limit for the daily check (.github/workflows/on-call.yml)


def get(path, tries=2):
    """One retry on a network error or a 5xx: a blip must not read as a mismatch."""
    url = f"{LIVE}{path}?v={int(time.time())}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "verify-live"}), timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return get(path, tries - 1) if e.code >= 500 and tries > 1 else (e.code, b"")
    except Exception as e:
        return get(path, tries - 1) if tries > 1 else (str(e), b"")


def age_hours(stamp):
    """Hours since an ISO stamp; None if unreadable."""
    try:
        t = dt.datetime.fromisoformat(stamp.strip().replace("Z", "+00:00"))
        t = t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
        return round((dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 3600, 1)
    except (ValueError, AttributeError):
        return None


def collector_keys():
    """Keys of PIPELINES in tools/collect_status.py, read without importing it."""
    tree = ast.parse((ROOT / "tools/collect_status.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "PIPELINES" for t in node.targets):
            return [row[0] for row in ast.literal_eval(node.value)]
    return []


def norm(t):
    return unicodedata.normalize("NFC", str(t or "")).casefold()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forbid", nargs="*", default=[])
    forbid = [norm(w) for w in ap.parse_args().forbid if w.strip()]

    v, info, live = {}, {}, {}

    for p in SERVED:
        st, body = get(p)
        live[p] = body
        info[p] = {"status": st, "live": hashlib.sha256(body).hexdigest()[:12],
                   "main": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:12] if (ROOT / p).exists() else None}
    v["served_equals_main"] = all(info[p]["status"] == 200 and info[p]["live"] == info[p]["main"] for p in SERVED)
    info["served_mismatch"] = [p for p in SERVED if info[p]["status"] != 200 or info[p]["live"] != info[p]["main"]]
    for p in SERVED:
        del info[p]

    # One work file and, when any exist, one triage file, found at run time.
    found = sorted(glob.glob(str(ROOT / "work/*/intent.md")))[:1] + sorted(glob.glob(str(ROOT / "triage/*/intent.md")))[:1]
    private = PRIVATE + [str(pathlib.Path(f).relative_to(ROOT)) for f in found]
    info["private_status"] = {p: get(p)[0] for p in private}
    info["private_missing_on_main"] = [p for p in private if not (ROOT / p).exists()] + \
        ([] if glob.glob(str(ROOT / "work/*/intent.md")) else ["work/*/intent.md"])
    v["private_not_served"] = all(s == 404 for s in info["private_status"].values()) and not info["private_missing_on_main"]

    try:
        st = json.loads((ROOT / "data/status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        st = {}
        info["status_error"] = str(e)
    st = st if isinstance(st, dict) else {}
    rows = st.get("pipelines") if isinstance(st.get("pipelines"), list) else []
    summ = st.get("summary") if isinstance(st.get("summary"), dict) else {}
    keys = [r.get("key") for r in rows if isinstance(r, dict)]
    v["status_consistent"] = (bool(rows) and len(keys) == len(rows) and summ.get("pipelines") == len(rows) and
                              summ.get("fresh") == sum(1 for r in rows if r.get("fresh") is True) and
                              all(r.get("key") and r.get("band") and isinstance(r.get("preview"), dict) and
                                  r["preview"].get("state") for r in rows))
    try:
        info["collector_keys"] = collector_keys()
    except (OSError, SyntaxError, ValueError) as e:
        info["collector_keys"], info["collector_error"] = [], str(e)
    v["rows_match_collector"] = bool(keys) and keys == info["collector_keys"]

    page = (ROOT / "index.html").read_text(encoding="utf-8")
    info["cells_missing"] = [f"{a}:{k}" for k in keys for a in ("data-next", "data-hb", "data-preview")
                             if page.count(f'{a}="{k}"') != 1]
    v["page_has_every_cell"] = bool(keys) and not info["cells_missing"]

    beat = ((ROOT / "data/.last-check").read_text(encoding="utf-8").split() or [""])[0] if (ROOT / "data/.last-check").exists() else ""
    info["heartbeat_age_hours"], info["status_age_hours"] = age_hours(beat), age_hours(str(st.get("generatedUtc", "")))
    # -1 allows clock skew; a stamp in the future (a wrong year) would otherwise pass forever.
    v["heartbeat_fresh"] = info["heartbeat_age_hours"] is not None and -1 <= info["heartbeat_age_hours"] <= MAX_HOURS
    v["status_fresh"] = info["status_age_hours"] is not None and -1 <= info["status_age_hours"] <= MAX_HOURS

    r = subprocess.run([sys.executable, str(ROOT / "tools/test_bands.py")], cwd=ROOT, capture_output=True, text=True)
    v["bands_tests_pass"] = r.returncode == 0 and "ALL PASS" in r.stdout
    info["bands_tail"] = (r.stdout + r.stderr).strip().splitlines()[-2:]

    # Every served path, live and on main, plus every other tracked text file on main. Only this script
    # is left out of the trace check, because it spells out the patterns; the forbidden words are
    # checked everywhere.
    texts = {f"live:{p}": b.decode("utf-8", "replace") for p, b in live.items()}
    tracked = [p for p in subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True).stdout.split("\0") if p]
    info["unreadable"] = []
    for p in tracked:
        try:
            texts[f"main:{p}"] = (ROOT / p).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass  # binary file
        except OSError:
            info["unreadable"].append(p)
    v["all_tracked_read"] = not info["unreadable"]
    hits = {p: len(TRACES.findall(t)) for p, t in texts.items() if p != "main:tools/verify_live.py"}
    info["traces"] = {p: n for p, n in hits.items() if n}
    v["no_personal_traces"] = not info["traces"]
    info["forbid_checked"] = len(forbid)
    info["forbidden_in"] = sorted({k for k, t in texts.items() for w in forbid if w in norm(t)})
    v["no_forbidden_words"] = bool(forbid) and not info["forbidden_in"]

    print(json.dumps({"pass": all(v.values()), "verdicts": v, "info": info}, ensure_ascii=False, indent=1))
    sys.exit(0 if all(v.values()) else 1)


if __name__ == "__main__":
    main()
