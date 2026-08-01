# Packaging roadmap

## Objective

Provide a reproducible, CI-published TeX ecosystem that is useful without
`tlmgr install`, while keeping installations smaller than a complete TeX Live.
Linux (`linux-64`) and macOS (`osx-64`, `osx-arm64`) are the initial targets.

## Packaging model

TeX Live collections share generated state such as format files, language
configuration, font maps, and `tlpkg/texlive.tlpdb`. Splitting arbitrary tlnet
archives into independently installable conda packages would therefore create
file ownership conflicts or require post-link mutation.

Use **generated distribution profiles** for TeX trees instead:

- Every profile is a locked closure of one or more upstream schemes/collections.
- A profile owns and generates one coherent `texlive.tlpdb`, font-map set,
  language configuration, and format set.
- Profiles are alternatives, not layers; only one profile should be installed
  in an environment.
- Standalone tools and GUI applications remain separate conda packages and
  depend on an appropriate profile.

This model remains declarative and avoids unmanaged changes to conda prefixes.

## Proposed packages

### TeX Live profiles

| Package | Intended contents | Use case | Priority |
|---|---|---|---|
| `texlive-basic` | `scheme-basic` plus `collection-fontsrecommended` | Small functional LaTeX/LuaLaTeX installation | Available |
| `texlive-standard` | `scheme-small`, with bibliography, graphics, tables, hyperlinks, recommended fonts, and latexmk | Default desktop and CI installation | Implemented; CI pending |
| `texlive-science` | Standard profile plus `collection-mathscience` and `collection-pictures` | Scientific papers and reports | Implemented; CI pending |
| `texlive-publishing` | Science profile plus bibliography, glossary, indexing, and publisher-oriented collections | Larger authoring environment | P2 |
| `texlive-full` | Upstream `scheme-full`, subject to artifact-size and CI-time evaluation | Compatibility fallback | P3 |

The `texlive` metapackage should move from `texlive-basic` to
`texlive-standard` once the standard profile passes all acceptance tests.

### Standalone command-line tools

1. `latexmk` — default multi-pass document builder.
2. `biber` — modern BibLaTeX backend. **Implemented; CI pending.**
3. `chktex` — reuse the current conda-forge package.
4. `tectonic` — optional alternative engine with its own bundle model.
5. `ghostscript` — use conda-forge where possible rather than rebuilding it.
6. `pandoc` integration tests — consume conda-forge's package.

### Desktop applications

1. `texmaker` — available; continue cross-platform menuinst testing.
2. `texstudio` — second full-featured Qt editor.
3. `lyx` — structured document editor.
4. PDF viewers should normally use native OS applications; package one only if
   editor integration requires it.

## Implementation phases

### P0: profile infrastructure and standard distribution

- Generalize `generate_texlive_scheme.py` into a profile generator driven by a
  small checked-in manifest of roots, tests, and metadata.
- Pin one tlnet snapshot for all profiles so archives and `tlpdb` records cannot
  drift between concurrent downloads.
- Generate font maps, language files, and formats during the build.
- Add explicit mutual-exclusion metadata between profile packages.
- Build `texlive-standard` from `scheme-small`, then measure archive size and
  compare its closure with the current basic profile.
- Add `latexmk` and make Texmaker use it as the recommended quick-build path.

### P1: scientific authoring

- Build `texlive-science`.
- Package `biber` and `chktex` if suitable conda-forge packages cannot be reused.
- Add end-to-end tests for BibTeX, BibLaTeX/Biber, AMS math, graphics, tables,
  references, and TikZ.

### P2: publishing and additional editors

- Build `texlive-publishing` after gathering real document requirements.
- Package Texstudio and LyX with menuinst shortcuts and file associations.
- Test editor-to-engine discovery in isolated prefixes.

### P3: full distribution and Windows

- Evaluate `texlive-full` artifact size, prefix file count, solve time, and CI
  duration before publishing it.
- Restore Windows only after the Unix profiles and editors are stable.

## Acceptance tests

Every TeX Live profile must test:

- `latex`, `pdflatex`, `lualatex`, `bibtex`, `kpsewhich`, and `tlmgr info`.
- A PDFLaTeX document using Times/Courier or another packaged Type 1 font,
  proving that generated font maps work.
- A LuaLaTeX document using OpenType fonts.
- Multi-pass cross-references and bibliography generation.
- No writes outside the test working directory and no network access at test
  time.
- Relocation into a fresh prefix.

Larger profiles additionally test their advertised features. GUI packages must
verify package contents, menuinst metadata, executable startup in a headless
smoke test where practical, and discovery of TeX executables from the same
prefix.

## Immediate next work

1. Validate and publish `texlive-basic` and `texlive-standard` on all three
   Unix platforms.
2. Measure the standard profile's installed and compressed sizes and refine its
   end-to-end tests using representative documents.
3. Decide whether the `latexmk` copy in `scheme-small` is sufficient or merits
   a separately versioned conda package.
4. Prepare the publishing profile and evaluate Texstudio packaging.
5. Verify Texmaker's quick-build configuration against `latexmk` from the same
   prefix.
