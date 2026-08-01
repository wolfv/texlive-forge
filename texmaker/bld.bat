@echo on

cmake -S . -B build -G Ninja ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DCMAKE_INSTALL_PREFIX="%LIBRARY_PREFIX%" ^
  -DCMAKE_PREFIX_PATH="%LIBRARY_PREFIX%"
if errorlevel 1 exit /B 1

cmake --build build --parallel %CPU_COUNT%
if errorlevel 1 exit /B 1
cmake --install build
if errorlevel 1 exit /B 1

if not exist "%PREFIX%\Menu" mkdir "%PREFIX%\Menu"
copy "%RECIPE_DIR%\menu\menu.json" "%PREFIX%\Menu\texmaker.json"
copy "datas\distrib\win\texmaker.ico" "%PREFIX%\Menu\texmaker.ico"
if errorlevel 1 exit /B 1
