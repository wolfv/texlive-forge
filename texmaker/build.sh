#!/usr/bin/env bash
set -euxo pipefail

cmake_args=()
if [[ "$(uname)" == Linux ]]; then
  # GNU ld rejects bundled PDFium's hidden FreeType symbols when Qt also links
  # the system FreeType DSO. lld correctly keeps the hidden executable symbols
  # local while resolving Qt against its shared FreeType dependency.
  cmake_args+=("-DCMAKE_EXE_LINKER_FLAGS=-fuse-ld=lld")
fi

cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DCMAKE_PREFIX_PATH="$PREFIX" \
  "${cmake_args[@]}"
cmake --build build --parallel "$CPU_COUNT"
cmake --install build

mkdir -p "$PREFIX/Menu"
cp "$RECIPE_DIR/menu/menu.json" "$PREFIX/Menu/texmaker.json"
cp datas/distrib/linux/texmaker.png "$PREFIX/Menu/texmaker.png"
cp datas/distrib/mac/texmaker.icns "$PREFIX/Menu/texmaker.icns"
