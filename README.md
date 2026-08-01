# texlive-forge

Rattler-build recipes for an easy-to-install TeX distribution, derived from
conda-forge recipes.

## Packages

- `texlive-core`: TeX Live's compiled engines and command-line tools. The
  recipe tracks [conda-forge/texlive-core-feedstock](https://github.com/conda-forge/texlive-core-feedstock).
- `texlive-basic`: the locked transitive closure of upstream `scheme-basic`
  and `collection-fontsrecommended` (149 tlnet archives), including macro
  files, recommended fonts, generated font maps and formats, and a working
  `tlmgr` package database. It provides tested `latex`, `pdflatex`, `bibtex`,
  and `lualatex` commands.
- `texlive-standard`: the locked `scheme-small` profile with recommended fonts
  (416 tlnet archives),
  including commonly expected LaTeX packages, recommended fonts, graphics,
  bibliography support, and `latexmk`.
- `texlive-science`: the standard profile plus the TeX Live math/science and
  graphics collections, including Mathtools, SIunitx, chemistry packages, and
  TikZ.
- `biber`: the Unicode-aware BibLaTeX bibliography backend, packaged from TeX
  Live's self-contained Linux and universal macOS binaries.
- `texlive`: a V3 profile-selector metapackage. Extras select the basic,
  standard, or science profile and optionally add a desktop toolchain.
- `texmaker`: the current Qt 6 LaTeX editor for Linux and macOS,
  updated from [conda-forge/texmaker-feedstock](https://github.com/conda-forge/texmaker-feedstock).
  It includes menuinst shortcuts and TeX file associations on both platforms.
  It depends only on the compiled core so it can accompany any profile; install
  it through a desktop extra to get a complete environment.

## Local build

Install [pixi](https://pixi.sh), then run:

```bash
pixi run build-core
pixi run build-basic
pixi run build-biber
pixi run build-standard
pixi run build-science
pixi run build-texlive
# On Unix, the TeX packages must finish before the editor.
pixi run build-texmaker
```

Artifacts are written below `output/`.

Select a profile through the V3 `texlive` metapackage:

```bash
pixi add -c https://prefix.dev/wolfv/texlive 'texlive[extras=[basic]]'
pixi add -c https://prefix.dev/wolfv/texlive 'texlive[extras=[standard]]'
pixi add -c https://prefix.dev/wolfv/texlive 'texlive[extras=[science]]'
pixi add -c https://prefix.dev/wolfv/texlive 'texlive[extras=[standard-desktop]]'
pixi add -c https://prefix.dev/wolfv/texlive 'texlive[extras=[science-desktop]]'
```

The desktop groups add Texmaker, Pandoc, and Ghostscript. Installing `texlive`
without an extra installs only `texlive-core`; the profile packages can also be
installed directly.

## Publishing to prefix.dev

`.github/workflows/build.yml` builds and tests Linux and macOS on
pushes and pull requests without publishing. `.github/workflows/release.yml`
publishes signed packages to [`wolfv/texlive`](https://prefix.dev/wolfv/texlive)
on a GitHub release or manual dispatch.

Publishing uses GitHub OIDC trusted publishing, so no API-key secret is needed.
Configure the channel's trusted publisher with:

```text
repository: wolfv/texlive-forge
workflow:   release.yml
```

## Scope

`texlive-basic` is intentionally much smaller than full TeX Live. Its recipe
is generated from TeX Live's dependency metadata and locks every source
archive by SHA-256. To refresh it from the current tlnet snapshot, run:

```bash
python scripts/generate_texlive_scheme.py
```

The same generator can produce larger schemes or collections without forcing
all installations to download the multi-gigabyte full distribution. See
[`ROADMAP.md`](ROADMAP.md) for the planned standard, science, and publishing
profiles and additional tools and editors.
