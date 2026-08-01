#!/usr/bin/env bash
set -euxo pipefail

mkdir -p "$PREFIX/bin"
if [[ "$(uname)" == Darwin ]]; then
  install -m755 bin/universal-darwin/biber "$PREFIX/bin/biber"
else
  install -m755 bin/x86_64-linux/biber "$PREFIX/bin/biber-real"
  cat > "$PREFIX/bin/biber" <<'SH'
#!/usr/bin/env bash
# TeX Live's self-contained Linux binary still uses the libcrypt.so.1 ABI.
prefix="$(cd "$(dirname "$0")/.." && pwd)"
export LD_LIBRARY_PATH="$prefix/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$prefix/bin/biber-real" "$@"
SH
  chmod +x "$PREFIX/bin/biber"
fi
