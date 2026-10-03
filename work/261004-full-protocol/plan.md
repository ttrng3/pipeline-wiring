# Plan: full-protocol

1. `tools/verify_live.py`: the verdicts in spec "Design", modelled on Omni-TMDV's script. It reads `PIPELINES` from `tools/collect_status.py` with `ast` (no import, so no network) and runs `tools/test_bands.py` as a subprocess.
2. `verification/wiring.md`: steps 1–4, the invariants, adversary, substitutes, evidence, not covered and traps, in the 7 protocols' shape.
3. Test on the branch: step 1 against live (expect pass, since main and the branch differ only in these new files, which Pages doesn't serve). Then both drills in a scratch copy.
4. PR → reviewer → fixes → Ty's ship phrase → step 1–4 on `main` → evidence on the PR.
