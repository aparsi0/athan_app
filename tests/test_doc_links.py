# -*- coding: utf-8 -*-
"""Every #anchor link must point at a heading that exists.

This has broken twice, both times silently. The website's Install tab links to
README headings by anchor, and GitHub does not 404 on a missing anchor — it
drops you at the top of the page, so a visitor clicking "Windows" just lands
nowhere in particular and nobody hears about it. Renaming a heading is a normal
edit; noticing that it orphaned a link in a different file is not.

Run: python3 tests/test_doc_links.py
"""

import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(REPO, "README.md")
SITE = os.path.join(REPO, "docs", "index.html")

# GitHub's slug rule, which is not the obvious one:
#   lowercase, drop everything that is not alphanumeric / space / hyphen /
#   underscore, then replace EACH space with one hyphen.
# It does not collapse runs, so "Windows 10 / 11" -> windows-10--11 (the
# slash vanishes and both its spaces become hyphens), and it keeps the hyphen
# left behind by a stripped leading emoji, so "## 🚀 Installation" is
# "#-installation". Both of those cost a debugging round the first time.
def slug(heading: str) -> str:
    text = re.sub(r"^#+\s+", "", heading).rstrip().lower()
    text = "".join(c for c in text if c.isalnum() or c in " -_")
    return text.replace(" ", "-")


def main() -> int:
    readme = io.open(README, encoding="utf-8").read()
    anchors = {slug(line) for line in readme.split("\n") if line.startswith("#")}

    checks = []
    if os.path.isfile(SITE):
        site = io.open(SITE, encoding="utf-8").read()
        for target in re.findall(r"athan_app#([\w\-]+)", site):
            checks.append(("docs/index.html", target))
    for target in re.findall(r"\]\(#([\w\-]+)\)", readme):
        checks.append(("README.md", target))

    if not checks:
        print("  no anchor links found — nothing to check")
        return 0

    broken = []
    for source, target in checks:
        ok = target in anchors
        print(("  ok   " if ok else "  FAIL ") + "%-16s -> #%s" % (source, target))
        if not ok:
            broken.append((source, target))

    print()
    if broken:
        print("%d broken link(s). README headings currently available:" % len(broken))
        for anchor in sorted(a for a in anchors if a):
            print("    #" + anchor)
        return 1
    print("ALL PASS (%d links)" % len(checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
