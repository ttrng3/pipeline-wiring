# Spec: tj-wiki

**Approved:** 2026-10-08 (Ty, "approve all three", after the spec was written)

**Intent:** accepted 2026-10-08 · **Status:** approved

## Requirements
1. Section 5's heading counts three Mac-only jobs; an "Added 08/10" paragraph describes the collector: launchd, 10:30 Mac local time Tue–Sat, an allowlist of fields with no broker ids, rclone to Drive `Raw Records/Bots/` by path, read by the 11:00 routine; it lands first only while the Mac is UTC+6:30 or east; a late or missed collection compiles the day without bot rows ("bot bundle missing") and is not flagged here (Trade-Journal #15, #16, `docs/wiki.md`).
2. Section 7 gets a "Changed 08/10" entry: the wiki page address, how it runs (including that the wiki step runs every routine run and never blocks the data push), and Trade-Journal #14–#17 with merge commits.

## Design
`index.html` only: one heading word, one paragraph, one `<details>` block in the page's existing style.

## Conflicts
Loaded: repo `CLAUDE.md`, the artifact mirror contract (the preview shows `index.html`; refreshed by its routine), entity separation (Trade Journal is personal and is already on this page).

| Rule (by name) | What in the design touches it | Resolution |
|---|---|---|
| Status only, no business data | The entry describes a pipeline | Schedules, paths and PR numbers only; no trades or figures |
| Second copy of every schedule (`collect_status.py`) | No routine schedule changes | Untouched |
| Publish the preview with its companion files | The preview shows this page | Post-merge: the routine's next refresh, or a publish of `build/artifact.html` with `starter-story.html`, `learning-matrix.html` and `data/status.json` |

## Security
Pages serves `.pages-allow` only, unchanged. No ids or secrets added.

## Promise
`python3 tools/test_bands.py` prints ALL PASS; `python3 tools/build-fragment.py` builds; after merge the live page shows the "Added 08/10" paragraph in section 5 and the "Changed 08/10" entry in section 7 (verification/wiring.md).

## Out of scope
The live status cells, the routine prompts, any preview publish beyond the routine's normal refresh.
