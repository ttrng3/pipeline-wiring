# pipeline-wiring

**The address is https://ttrng3.github.io/pipeline-wiring/** — that is what goes in a
document or a message. The Cowork artifact is a *mirror*: a preview of this page inside
Claude, published only after the repo is correct, and never authoritative. If the two
disagree, the repo wins and the artifact is what gets corrected.

One page describing the whole system: every repo, every artifact, every routine, which
of them are copies of each other, and what is currently broken. It **describes** the
eight pipelines; it is not one of them. Nothing refreshes it on a schedule — it is
updated by hand when the system changes.

## Layout

| File | What it is |
|---|---|
| `index.html` | The page. Three tabs; tab 1 is the wiring map itself. |
| `starter-story.html` | Tab 2, loaded in an iframe. |
| `learning-matrix.html` | Tab 3, loaded in an iframe. The **only** Learning Matrix — see below. |
| `tools/build-fragment.py` | Builds `build/artifact.html` for the mirror. |

`build/` is generated. Do not edit it and do not commit a hand-edited copy.

## Publishing

Pages serves this repo directly, so a push is the publish. The mirror is separate:

```
python3 tools/build-fragment.py
# then publish build/artifact.html as index.html to the artifact url,
# together with starter-story.html and learning-matrix.html
```

Two failure modes, both silent:

- **Never publish `index.html` itself to the artifact.** The service wraps what it is
  given, so a complete document nests inside another, the inner `<head>` is discarded,
  and the page renders blank with no console error. To check a publish, read the
  artifact's `index.html` back and count `<html>` tags: one is correct, two means it
  nested.
- **The two iframe files must exist in the artifact too.** The tabs load them by
  relative path; an absolute fallback to the Pages URL is blocked by CSP inside an
  artifact.

The builder here strips document wrappers because this page keeps `<title>` inside
`<head>`. The `Omni-TMDV` and `Ecopm-Sitecheck` builders cut at `<title>` instead,
because those pages put the title after the wrapper. **The builders are not
interchangeable.**

## The Learning Matrix lives here and nowhere else

On 2026-09-24 the Starter Story and Learning Matrix were folded into this page as tabs,
and their standalone artifacts were deleted. On 2026-09-25 a repair read the 14/09
Learning Matrix record, found the artifact id in it dead, and rebuilt a standalone copy —
not knowing it had been consolidated. That standalone was deleted the same day.

**Before recreating anything named here, check this file and
`93 Knowledge Base/_tools/artifact-registry.md` first.** A dead artifact id means "this
was retired", not "this is missing".

## Related

- Registry of every artifact and its owner: `93 Knowledge Base/_tools/artifact-registry.md` on Drive.
- All routines: https://claude.ai/code/routines
