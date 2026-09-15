@echo off
REM Rebuild rz-ghidra (the Ghidra decompiler + its rizin bridge).
REM
REM The rz-ghidra source tree lives inside the build directory, created by the
REM install step. Re-run this after changing the Ghidra sources it uses
REM (see tools\upgrade-ghidra.sh) to avoid a full Clutter rebuild.
REM
REM Usage:  tools\build-ghidra.bat [jobs]
setlocal
IF "%~1"=="" (set JOBS=8) ELSE (set JOBS=%~1)

for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RZG=%ROOT%\build-clutter\dist\rz-ghidra-prefix\src\rz-ghidra-build"

if not exist "%RZG%" (
    echo [!] rz-ghidra build directory not found: %RZG%
    echo     Run build-clutter.bat install first.
    exit /b 1
)

call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1

if exist "%ROOT%\.tools\venv\Scripts" set "PATH=%ROOT%\.tools\venv\Scripts;%PATH%"
if exist "%ROOT%\cutter-deps\qt\bin" set "PATH=%ROOT%\cutter-deps\qt\bin;%PATH%"

cd /d "%RZG%" || exit /b 1

echo [*] Building rz-ghidra with -j %JOBS% ...
ninja -j %JOBS%
if errorlevel 1 (
    echo [!] rz-ghidra build failed
    exit /b 1
)

echo [*] Installing rz-ghidra into the portable dist ...
ninja install
if errorlevel 1 exit /b 1
echo [+] rz-ghidra rebuilt and installed
endlocal
