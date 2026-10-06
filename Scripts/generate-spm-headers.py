#!/usr/bin/env python3
"""Regenerate Source/include/ for Swift Package Manager builds.

SwiftPM builds the AsyncDisplayKit module from Source/include/ (the
publicHeadersPath), which contains a single AsyncDisplayKit/ directory: a
flat copy of the umbrella header plus every header it reaches through its
quoted imports. SwiftPM resolves quoted imports sibling-first when building
the module and does not know Source/'s subdirectory layout, so the copies
must sit next to each other.

The copies must never resolve by flat basename during the target's own
compilation — SwiftPM passes -I Source/include there too, and mixing
originals and copies of one header within a translation unit fails with
redefinition errors. Keeping the copies one directory deep (include/AsyncDisplayKit/)
guarantees that: target sources import "Header.h", the copies live at
<AsyncDisplayKit/Header.h>.

The directory is committed; rerun this script whenever the umbrella header or
the headers it pulls in change:

    python3 Scripts/generate-spm-headers.py
"""

import re
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "Source"
INCLUDE = SOURCE / "include"
COPIES = INCLUDE / "AsyncDisplayKit"
UMBRELLA = "AsyncDisplayKit.h"
IMPORT_RE = re.compile(r'^\s*#(?:import|include)\s*"([^"]+)"', re.MULTILINE)


def header_index():
    return {
        path.name: path
        for path in SOURCE.rglob("*.h")
        if INCLUDE not in path.parents
    }


def closure(index):
    seen, queue, missing = set(), [UMBRELLA], []
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        path = index.get(name)
        if path is None:
            missing.append(name)
            continue
        seen.add(name)
        queue.extend(IMPORT_RE.findall(path.read_text()))
    return seen, missing


def main():
    index = header_index()
    seen, missing = closure(index)
    for name in sorted(set(missing)):
        print(f"warning: quoted import not found under Source/: {name}", file=sys.stderr)

    shutil.rmtree(INCLUDE, ignore_errors=True)
    COPIES.mkdir(parents=True)
    for name in sorted(seen):
        shutil.copy2(index[name], COPIES / name)

    print(f"Generated {COPIES}: {len(seen)} headers")


if __name__ == "__main__":
    main()
