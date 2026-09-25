#!/usr/bin/env python3
"""Build build/artifact.html - the fragment the Cowork mirror is published from.

The artifact service wraps whatever it is given in its own document. A complete
document handed to it therefore nests inside another one, the inner <head> is
discarded, and the page renders BLANK with no console error. So the mirror gets
a fragment: no doctype, no <html>, no <head>, no <body>.

index.html keeps its <title> INSIDE <head>, so this builder strips the document
wrappers rather than cutting at <title>. Do not swap it with the Omni-TMDV or
Ecopm-Sitecheck builder, which cut at <title> because those pages put the title
after the wrapper.

The wrapper regex is deliberately anchored: a naive </?head[^>]*> also matches
<header> and silently deletes every header element on the page.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = (ROOT / "index.html").read_text(encoding="utf-8")

frag = re.sub(r"<!doctype html>\s*", "", src, flags=re.I)
frag = re.sub(r"</?(?:html|head|body)(?:\s[^>]*)?>", "", frag, flags=re.I)
frag = frag.strip() + "\n"

for tag in ("<html", "<head", "<body", "<!doctype"):
    assert tag not in frag.lower(), f"{tag} survived the strip"
assert "<title>" in frag, "title was lost"
assert "<header" not in frag.lower() or "<header" in src.lower(), "header eaten"

out = ROOT / "build"
out.mkdir(exist_ok=True)
(out / "artifact.html").write_text(frag, encoding="utf-8")
print(f"build/artifact.html  {len(frag):,} bytes  (from {len(src):,})")
