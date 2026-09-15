@echo off
REM ---------------------------------------------------------------
REM  Clutter (Cutter fork) portable Windows build
REM
REM  Uses only project-local tools, nothing is installed system wide:
REM    .tools\venv            -> meson + ninja (python venv)
REM    cutter\cutter-deps\qt  -> portable Qt 6   (scripts\fetch_deps.sh)
REM    cutter\cutter-deps\pyside -> portable PySide6 + shiboken (same script)
REM    (the dependency folder keeps its upstream `cutter-deps` name: it is
REM     published by the Cutter project and is downloaded as-is)
REM
REM  Builds the *full* feature set that Cutter's own Windows CI builds, so the
REM  result is a complete Clutter rather than a stripped one:
REM
REM    Python console + Python plugins     (CLUTTER_ENABLE_PYTHON)
REM    Python bindings                     (CLUTTER_ENABLE_PYTHON_BINDINGS)
REM    FLIRT signature database            (CLUTTER_ENABLE_SIGDB)
REM    Ghidra decompiler                   (CLUTTER_PACKAGE_RZ_GHIDRA)
REM    jsdec JS decompiler                 (CLUTTER_PACKAGE_JSDEC)
REM    Swift demangler                     (CLUTTER_PACKAGE_RZ_LIBSWIFT)
REM    YARA scanning                       (CLUTTER_PACKAGE_RZ_LIBYARA)
REM    Silhouette function detection       (CLUTTER_PACKAGE_RZ_SILHOUETTE)
REM    Frida dynamic instrumentation       (CLUTTER_PACKAGE_RZ_FRIDA)
REM
REM  The optional plugins are cloned and built at install time by Cutter's own
REM  PowerShell bundling scripts; each is skipped automatically if it fails, so
REM  a flaky one cannot take the whole build down.
REM
REM  Usage:  build-clutter.bat              configure (once) + build
REM          build-clutter.bat configure    only run the CMake configure step
REM          build-clutter.bat reconfigure  wipe the CMake cache and configure again
REM          build-clutter.bat install      also install the portable app to clutter-dist\
REM          build-clutter.bat full         configure + build + install in one go
REM ---------------------------------------------------------------
setlocal enableextensions

REM Repo root = one level up from tools\, fully resolved (no trailing backslash).
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "CUTTER_DIR=%ROOT%"
set "DEPS=%ROOT%\cutter-deps"
set "BUILD=%CUTTER_DIR%\build-clutter"
set "DIST=%ROOT%\clutter-dist"
set "VCVARS=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"

REM --- feature switches (set to OFF to build a leaner Clutter) ---
set "CLUTTER_PYTHON=ON"
set "CLUTTER_PYTHON_BINDINGS=ON"
set "CLUTTER_SIGDB=ON"
set "CLUTTER_PLUGINS=ON"

if not exist "%VCVARS%" (
    echo [!] Visual Studio 2026 vcvars64.bat not found at "%VCVARS%"
    exit /b 1
)

if not exist "%DEPS%\qt\bin\qmake.exe" (
    echo [!] Portable Qt not found. Run:  bash scripts/fetch_deps.sh
    exit /b 1
)
if not exist "%ROOT%\.tools\venv\Scripts\meson.exe" (        echo [!] meson/ninja missing. Run:
    echo     python -m venv .tools\venv
    echo     .tools\venv\Scripts\python -m pip install meson ninja
    exit /b 1
)

REM rz-ghidra pulls its own fork of Ghidra as a submodule and some Java sources
REM live deeper than the legacy 260 character Windows limit. Enable long paths
REM for git through the environment only, so the machine's git config stays untouched.
set "GIT_CONFIG_COUNT=1"
set "GIT_CONFIG_KEY_0=core.longpaths"
set "GIT_CONFIG_VALUE_0=true"

REM PySide6's CMake package computes its relocatable paths as PACKAGE_PREFIX/typesystems
REM and PACKAGE_PREFIX/glue, but the portable bundle keeps them under share/PySide6.
REM Without this the Python binding configure step dies on set_and_check(), and the
REM typesystem XMLs reference ../doc/*.rst relative to themselves, so doc comes too.
if /i "%CLUTTER_PYTHON_BINDINGS%"=="ON" (
    if not exist "%DEPS%\pyside\typesystems" (
        echo [*] Provisioning PySide6 typesystems/glue/doc for the binding build ...
        xcopy /E /I /Q /Y "%DEPS%\pyside\share\PySide6\typesystems" "%DEPS%\pyside\typesystems" >nul
        xcopy /E /I /Q /Y "%DEPS%\pyside\share\PySide6\glue" "%DEPS%\pyside\glue" >nul
        xcopy /E /I /Q /Y "%DEPS%\pyside\share\PySide6\doc" "%DEPS%\pyside\doc" >nul
    )
)

REM The optional plugin scripts call meson/ninja/python/cmake directly, and the
REM rz-frida cutter-plugin step reads CUTTER_DEPS to find Qt. Cutter's CI sets it
REM (third-party convention, kept verbatim on purpose);
REM without it that plugin's cmake configure cannot find Qt and the install aborts.
set "CUTTER_DEPS=%DEPS%"
REM .tools\bin is legacy; tools\bin holds the project-local pkg-config shim
REM (see tools\pkgconfig-shim.py); plugin builds that call pkg_check_modules use
REM it instead of a system install.
set "PKG_CONFIG_PATH=%DIST%\lib\pkgconfig"
set "PATH=%ROOT%\tools\bin;%ROOT%\.tools\venv\Scripts;%DEPS%\qt\bin;%PATH%"
call "%VCVARS%" >nul
if errorlevel 1 (
    echo [!] Failed to initialize the MSVC environment.
    exit /b 1
)

REM CMake's FindPkgConfig only accepts a real executable, so the Python shim gets a
REM small C launcher built from tools\pkgconfig-wrapper.c (see tools\build-pkgconfig.bat).
if not exist "%ROOT%\tools\bin\pkg-config.exe" (
    echo [*] Building the project-local pkg-config launcher ...
    call "%~dp0build-pkgconfig.bat"
    if errorlevel 1 exit /b 1
)

if /i "%~1"=="reconfigure" (
    echo [*] Removing the CMake cache to pick up option changes ...
    del /q "%BUILD%\CMakeCache.txt" >nul 2>&1
    del /q "%BUILD%\CMakeFiles\cmake.check_cache" >nul 2>&1
)

if not exist "%BUILD%\CMakeCache.txt" (
    echo [*] Configuring Clutter ^(VS 2026 + portable Qt 6 + PySide6^) ...
    cmake -S "%CUTTER_DIR%" -B "%BUILD%" -G Ninja ^
        -DCMAKE_BUILD_TYPE=Release ^
        -DCMAKE_INSTALL_PREFIX="%DIST%" ^
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ^
        -DCMAKE_TOOLCHAIN_FILE="%CUTTER_DIR%\cmake\clutter-toolchain.cmake" ^
        -DCMAKE_PREFIX_PATH="%DEPS%\qt;%DEPS%\pyside" ^
        -DCLUTTER_USE_BUNDLED_RIZIN=ON ^
        -DCLUTTER_ENABLE_PYTHON=%CLUTTER_PYTHON% ^
        -DCLUTTER_ENABLE_PYTHON_BINDINGS=%CLUTTER_PYTHON_BINDINGS% ^
        -DPython3_FIND_REGISTRY=NEVER ^
        -DPython3_FIND_STRATEGY=LOCATION ^
        -DPython_FIND_REGISTRY=NEVER ^
        -DPython_FIND_STRATEGY=LOCATION ^
        -DCLUTTER_ENABLE_SIGDB=%CLUTTER_SIGDB% ^
        -DCLUTTER_ENABLE_PACKAGING=ON ^
        -DCLUTTER_PACKAGE_DEPENDENCIES=ON ^
        -DCLUTTER_PACKAGE_RZ_GHIDRA=ON ^
        -DCLUTTER_PACKAGE_JSDEC=%CLUTTER_PLUGINS% ^
        -DCLUTTER_PACKAGE_RZ_LIBSWIFT=%CLUTTER_PLUGINS% ^
        -DCLUTTER_PACKAGE_RZ_LIBYARA=%CLUTTER_PLUGINS% ^
        -DCLUTTER_PACKAGE_RZ_SILHOUETTE=%CLUTTER_PLUGINS% ^
        -DCLUTTER_PACKAGE_RZ_FRIDA=%CLUTTER_PLUGINS% ^
        -DCLUTTER_ENABLE_DEPENDENCY_DOWNLOADS=ON
    if errorlevel 1 exit /b 1
) else (
    echo [*] Reusing the existing CMake configuration in "%BUILD%".
)

if /i "%~1"=="configure" exit /b 0

echo [*] Building ...
cmake --build "%BUILD%" --parallel
if errorlevel 1 (
    echo [!] Build failed. If the failure is in the bundled rizin step, run
    echo     tools\build-rizin.bat
    echo     and then re-run this script.
    exit /b 1
)

if /i "%~1"=="install" goto install
if /i "%~1"=="full" goto install
exit /b 0

:install
echo [*] Installing portable build to "%DIST%" ...
echo     (first run also clones and builds jsdec, libswift, libyara,
echo      silhouette and rz-frida into "%DIST%"; this takes a while)
cmake --install "%BUILD%"
if errorlevel 1 (
    echo [!] Install step failed. Re-run "build-clutter.bat install" to retry the
    echo     optional plugin bundling; the core app is already installed.
    exit /b 1
)

REM Cutter only bundles a Python *runtime* when building a ZIP package, so a plain
REM install leaves python3xx\ with site-packages but no interpreter. Run Cutter's own
REM bundler to fetch the matching embeddable Python into the portable folder.
if /i "%CLUTTER_PYTHON%"=="ON" (
    if not exist "%DIST%\python312._pth" (
        echo [*] Bundling the portable Python runtime ...
        pushd "%BUILD%"
        powershell -NoProfile -ExecutionPolicy Bypass -File "%CUTTER_DIR%\dist\bundle_python.ps1" x64 "%DIST%"
        if errorlevel 1 echo [!] Python bundling failed; the GUI will fall back to a system Python.
        popd
    )
)

echo [+] Done. Run "%DIST%\clutter.exe"
endlocal
