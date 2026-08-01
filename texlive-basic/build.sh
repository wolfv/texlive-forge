#!/usr/bin/env bash
set -euxo pipefail

texmf_dist="$PREFIX/share/texmf-dist"
tlpkg="$PREFIX/share/tlpkg"
mkdir -p "$texmf_dist" "$tlpkg" "$PREFIX/share/texmf-var/web2c"

# texlive-core patches this file with relocatable conda-prefix paths. The
# upstream kpathsea data archive also carries a stock copy, so preserve the
# conda-specific configuration while merging package data.
cp "$texmf_dist/web2c/texmf.cnf" "$SRC_DIR/texmf.cnf.conda"

# TeX Live package archives are rooted at TEXMFDIST, except for their tlpkg
# metadata. Merge the locked scheme-basic closure into the core installation.
for package_dir in "$SRC_DIR"/packages/*; do
  if [[ -d "$package_dir/tlpkg" ]]; then
    cp -a "$package_dir/tlpkg/." "$tlpkg/"
  fi
  for entry in "$package_dir"/*; do
    entry_name="$(basename "$entry")"
    case "$entry_name" in
      tlpkg)
        ;;
      tlpobj)
        mkdir -p "$tlpkg/tlpobj"
        cp -a "$entry/." "$tlpkg/tlpobj/"
        ;;
      texmf-dist)
        # Non-relocated TLCore archives retain the texmf-dist prefix.
        cp -a "$entry/." "$texmf_dist/"
        ;;
      *)
        # Relocated package archives are rooted inside TEXMFDIST.
        cp -a "$entry" "$texmf_dist/"
        ;;
    esac
  done
done

cp "$SRC_DIR/texmf.cnf.conda" "$texmf_dist/web2c/texmf.cnf"

# Build the installed-package database omitted from individual tlnet archives.
# This completes the tlmgr support proposed in conda-forge PR #78: the Perl
# modules come from texlive.infra, while these locked tlpobj records describe
# exactly the files owned by this scheme.
cat > "$tlpkg/texlive.tlpdb" <<'TLPDB'
name 00texlive.config
category TLCore
revision 79836
depend container_format/xz
depend container_split_doc_files/1
depend container_split_src_files/1
depend frozen/0
depend minrelease/2026
depend release/2026

name 00texlive.installation
category TLCore
revision 79836
depend opt_autobackup:1
depend opt_backupdir:tlpkg/backups
depend opt_create_formats:1
depend opt_generate_updmap:0
depend opt_install_docfiles:0
depend opt_install_srcfiles:0
depend opt_location:https://ftp.fau.de/ctan/systems/texlive/tlnet
depend opt_post_code:1
depend setting_available_architectures:aarch64-linux universal-darwin x86_64-darwinlegacy x86_64-linux

TLPDB
while IFS= read -r tlpobj; do
  cat "$tlpobj" >> "$tlpkg/texlive.tlpdb"
  printf '\n' >> "$tlpkg/texlive.tlpdb"
done < <(find "$tlpkg/tlpobj" -type f -name '*.tlpobj' | sort)

# texlive-core ships the release-wide generated language files, which refer to
# language packs outside scheme-basic. Start from TeX Live's deliberately
# minimal English configuration instead; additional collection recipes can
# regenerate these files when they add languages.
config_dir="$texmf_dist/tex/generic/config"
cp "$config_dir/language.us" "$config_dir/language.dat"
cp "$config_dir/language.us.def" "$config_dir/language.def"
printf '\\uselanguage {USenglish}\n' >> "$config_dir/language.def"
cp "$config_dir/language.us.lua" "$config_dir/language.dat.lua"
printf '}\n' >> "$config_dir/language.dat.lua"

mktexlsr

# texlive-core supplies engines; the scheme supplies initialization files.
# Generate the principal formats now so every installed environment works
# immediately and does not write format files into a user's home directory.
fmtutil-sys --byfmt latex
fmtutil-sys --byfmt pdflatex
fmtutil-sys --byfmt lualatex

ln -sfn pdftex "$PREFIX/bin/latex"
ln -sfn pdftex "$PREFIX/bin/pdflatex"
ln -sfn luahbtex "$PREFIX/bin/lualatex"
