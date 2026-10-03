#!/usr/bin/env python3
"""Step 4 of verification/wiring.md: does a saved copy of the Cowork preview carry this build?

  python3 tools/preview_matches.py <saved-preview.html> [build/artifact.html]

The publisher wraps the fragment in a skeleton: a head ending in "<body>\\n" and the tail
"\\n</body></html>". This removes exactly that skeleton and nothing else: the head must hash to one of
KNOWN_HEADS and the tail must be exact. Then the fragment must equal the build byte for byte. Two
skeletons were seen on 2026-10-04 and both are pinned (Ty, 2026-10-04); a new one fails until it is
pinned on purpose. Modelled on gdsh-report's script (2026-10-02). Prints JSON; exit 0 only on a match.
"""
import hashlib, json, pathlib, sys

# sha256 of each known head, <!doctype html> through "<body>\\n", by its length in bytes.
KNOWN_HEADS = {"65aeed0fe57327ab5aa05983225a4a29182a3b56007728748fc02df09a0df9b3": 537,  # seen 2026-10-02 and 2026-10-04
               "e31337138497e60f14bd7cf04bac72f75eec8a64666fcbee2b21afb15bc08f02": 355}  # seen 2026-10-04
ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAD_END = b"<body>\n"
TAIL = b"\n</body></html>"


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    paths = {"preview": pathlib.Path(sys.argv[1]),
             "build": pathlib.Path(sys.argv[2] if len(sys.argv) == 3 else ROOT / "build/artifact.html")}
    try:
        preview, build = paths["preview"].read_bytes(), paths["build"].read_bytes()
    except OSError as e:
        # Still one JSON object, so the step's evidence is a verdict, not a traceback.
        print(json.dumps({"match": False, "error": f"unreadable: {e.filename}"}, indent=1))
        sys.exit(1)
    cut = preview.find(HEAD_END)
    head = preview[:cut + len(HEAD_END)] if cut >= 0 else b""
    known = KNOWN_HEADS.get(hashlib.sha256(head).hexdigest()) if head else None
    out = {"skeleton_head_pinned": known is not None, "skeleton_head": known,
           "skeleton_tail_exact": preview.endswith(TAIL)}
    # Head and tail must not overlap, and an empty build proves nothing.
    whole = out["skeleton_head_pinned"] and out["skeleton_tail_exact"] and len(preview) >= len(head) + len(TAIL)
    frag = preview[len(head):len(preview) - len(TAIL)] if whole and build else None
    if frag is not None:
        out.update(fragment_bytes=len(frag), build_bytes=len(build),
                   fragment_sha256=hashlib.sha256(frag).hexdigest(), build_sha256=hashlib.sha256(build).hexdigest())
    out["match"] = frag is not None and frag == build
    print(json.dumps(out, indent=1))
    sys.exit(0 if out["match"] else 1)


if __name__ == "__main__":
    main()
