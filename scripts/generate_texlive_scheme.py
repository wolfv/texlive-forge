#!/usr/bin/env python3
"""Generate locked rattler-build recipes for configured TeX Live profiles."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import pathlib
import tomllib
import urllib.request
from collections import defaultdict
from typing import Any

# Use one well-maintained mirror so the database and all archives come from the
# same repository snapshot. mirror.ctan.org may redirect concurrent requests to
# different, temporarily out-of-sync mirrors.
TLNET = "https://ftp.fau.de/ctan/systems/texlive/tlnet"
ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILES = ROOT / "texlive-profiles.toml"


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


def test_commands(kind: str) -> list[str]:
    commands = [
        "export LANG=C",
        "export LC_ALL=C",
        "lualatex --version",
        "pdflatex --version",
        "tlmgr info --only-installed scheme-basic",
        'echo "\\\\documentclass{article}\\\\begin{document}LuaLaTeX works.\\\\end{document}" > smoke.tex',
        "lualatex -interaction=nonstopmode -halt-on-error smoke.tex",
        "test -s smoke.pdf",
        'echo "\\\\documentclass{article}\\\\usepackage{times}\\\\begin{document}Times and \\\\texttt{Courier}.\\\\end{document}" > fonts.tex',
        "pdflatex -interaction=nonstopmode -halt-on-error fonts.tex",
        "test -s fonts.pdf",
    ]
    if kind == "basic":
        commands.insert(5, "tlmgr info --only-installed collection-fontsrecommended")
    elif kind == "standard":
        commands.insert(5, "tlmgr info --only-installed scheme-small")
        commands.extend(
            [
                "xelatex --version",
                'echo "\\\\documentclass{article}\\\\usepackage{booktabs,microtype,xcolor}\\\\begin{document}Standard profile.\\\\end{document}" > standard.tex',
                "latexmk -pdf -interaction=nonstopmode -halt-on-error standard.tex",
                "test -s standard.pdf",
                'echo "\\\\documentclass{article}\\\\begin{document}XeLaTeX works.\\\\end{document}" > xetex.tex',
                "xelatex -interaction=nonstopmode -halt-on-error xetex.tex",
                "test -s xetex.pdf",
            ]
        )
    else:
        raise ValueError(f"unknown test kind: {kind}")
    return commands


def yaml_script(commands: list[str]) -> str:
    return "\n".join(f"      - {command}" for command in commands)


def generate(profile_name: str, profile: dict[str, Any], output: pathlib.Path) -> None:
    tlpdb_raw = fetch(f"{TLNET}/tlpkg/texlive.tlpdb")
    records = parse_tlpdb(tlpdb_raw)
    roots = profile["roots"]
    packages = sorted(set().union(*(dependency_closure(records, root) for root in roots)))

    version = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        hashes = dict(executor.map(package_hash, packages))

    output.mkdir(parents=True, exist_ok=True)
    (output / "packages.lock").write_text(
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

    constraints = ""
    if profile.get("conflicts"):
        constraints = "  run_constraints:\n" + "".join(
            f"    - {name} <0a0\n" for name in profile["conflicts"]
        )

    description = "\n".join(f"    {line}" for line in profile["description"].strip().splitlines())
    recipe = f'''schema_version: 1

context:
  version: "{version}"
  texlive_version: "20260301"

package:
  name: {profile["package"]}
  version: ${{{{ version }}}}

source:
{chr(10).join(source_lines)}

build:
  number: {profile["build_number"]}
  script: build.sh

requirements:
  build:
    - python
  host:
    - texlive-core ==${{{{ texlive_version }}}}
  run:
    - texlive-core ==${{{{ texlive_version }}}}
{constraints}
tests:
  - script:
{yaml_script(test_commands(profile["test_kind"]))}

about:
  homepage: https://www.tug.org/texlive/
  license: GPL-2.0-or-later AND LPPL-1.3c AND OFL-1.1
  summary: {profile["summary"]}
  description: |
{description}

extra:
  recipe-maintainers:
    - wolfv
  texlive-profile: {profile_name}
  texlive-root-packages: {' '.join(roots)}
'''
    (output / "recipe.yaml").write_text(recipe)
    print(f"Generated {output / 'recipe.yaml'} with {len(packages)} archives")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("basic", "standard"), default="basic")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    profiles = tomllib.loads(PROFILES.read_text())["profiles"]
    profile = profiles[args.profile]
    output = args.output or ROOT / profile["package"]
    generate(args.profile, profile, output)


if __name__ == "__main__":
    main()
