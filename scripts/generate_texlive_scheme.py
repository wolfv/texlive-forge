#!/usr/bin/env python3
"""Generate a locked rattler-build recipe from TeX Live's rolling tlpdb."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import pathlib
import urllib.request
from collections import defaultdict

# Use one well-maintained mirror so the database and all archives come from the
# same repository snapshot. mirror.ctan.org may redirect concurrent requests to
# different, temporarily out-of-sync mirrors.
TLNET = "https://ftp.fau.de/ctan/systems/texlive/tlnet"
ROOT = pathlib.Path(__file__).resolve().parents[1]


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "texlive-forge recipe generator"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def parse_tlpdb(raw: bytes) -> dict[str, dict[str, list[str]]]:
    records = {}
    for record in raw.decode("utf-8", errors="replace").split("\n\n"):
        fields: dict[str, list[str]] = defaultdict(list)
        for line in record.splitlines():
            if " " in line and not line.startswith(" "):
                key, value = line.split(" ", 1)
                fields[key].append(value)
        if fields.get("name"):
            records[fields["name"][0]] = dict(fields)
    return records


def dependency_closure(records: dict[str, dict[str, list[str]]], root: str) -> list[str]:
    result: set[str] = set()
    pending = [root]
    while pending:
        name = pending.pop()
        if name in result:
            continue
        if name not in records:
            raise RuntimeError(f"TeX Live dependency {name!r} is absent from tlpdb")
        result.add(name)
        for dependency in records[name].get("depend", []):
            # Architecture-specific binaries are provided by texlive-core.
            if dependency.endswith(".ARCH") or dependency.startswith("setting_available_architectures:"):
                continue
            if dependency.startswith("00texlive"):
                continue
            pending.append(dependency)
    return sorted(result)


def package_hash(name: str) -> tuple[str, str]:
    url = f"{TLNET}/archive/{name}.tar.xz"
    return name, hashlib.sha256(fetch(url)).hexdigest()


def generate(root_package: str, output: pathlib.Path) -> None:
    tlpdb_raw = fetch(f"{TLNET}/tlpkg/texlive.tlpdb")
    records = parse_tlpdb(tlpdb_raw)
    packages = dependency_closure(records, root_package)

    # Date the generated package after the repository snapshot and retain every
    # upstream revision in the lock file for reviewability.
    version = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        hashes = dict(executor.map(package_hash, packages))

    output.mkdir(parents=True, exist_ok=True)
    lock = output / "packages.lock"
    lock.write_text(
        "# package revision sha256\n"
        + "".join(
            f"{name} {records[name].get('revision', ['0'])[0]} {hashes[name]}\n"
            for name in packages
        )
    )

    source_lines = []
    for name in packages:
        source_lines.extend(
            [
                f"  - url: {TLNET}/archive/{name}.tar.xz",
                f"    sha256: {hashes[name]}",
                f"    target_directory: packages/{name}",
            ]
        )

    recipe = f'''schema_version: 1

context:
  version: "{version}"
  texlive_version: "20260301"

package:
  name: texlive-basic
  version: ${{{{ version }}}}

source:
{chr(10).join(source_lines)}

build:
  number: 0
  script: build.sh

requirements:
  host:
    - texlive-core ==${{{{ texlive_version }}}}
  run:
    - texlive-core ==${{{{ texlive_version }}}}

 tests:
  - script:
      - lualatex --version
      - pdflatex --version
      - tlmgr info --only-installed scheme-basic
      - echo "\\\\documentclass{{article}}\\\\begin{{document}}LuaLaTeX works.\\\\end{{document}}" > smoke.tex
      - lualatex -interaction=nonstopmode -halt-on-error smoke.tex
      - test -s smoke.pdf

about:
  homepage: https://www.tug.org/texlive/
  license: GPL-2.0-or-later AND LPPL-1.3c AND OFL-1.1
  summary: TeX Live basic scheme with working LaTeX and LuaLaTeX formats
  description: |
    The transitive contents of TeX Live's scheme-basic, locked from the tlnet
    package database. It adds the macro files, fonts, configuration, and formats
    needed for a functional basic TeX installation to texlive-core.

extra:
  recipe-maintainers:
    - wolfv
  texlive-root-package: {root_package}
'''
    # Keep generated YAML syntactically aligned despite the readable template.
    recipe = recipe.replace("\n tests:\n", "\ntests:\n")
    (output / "recipe.yaml").write_text(recipe)
    print(f"Generated {output / 'recipe.yaml'} with {len(packages)} archives")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="scheme-basic")
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "texlive-basic")
    args = parser.parse_args()
    generate(args.root, args.output)


if __name__ == "__main__":
    main()
