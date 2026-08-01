#!/usr/bin/env bash
set -euxo pipefail

cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DCMAKE_PREFIX_PATH="$PREFIX"
cmake --build build --parallel "$CPU_COUNT"
cmake --install build

mkdir -p "$PREFIX/Menu"
cp "$RECIPE_DIR/menu/menu.json" "$PREFIX/Menu/texmaker.json"
cp datas/distrib/linux/texmaker.png "$PREFIX/Menu/texmaker.png"
cp datas/distrib/mac/texmaker.icns "$PREFIX/Menu/texmaker.icns"
