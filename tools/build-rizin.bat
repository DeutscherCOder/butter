@echo off
REM Build the bundled rizin tree directly.
REM
REM Why this exists: the bundled-rizin ExternalProject calls plain `ninja`
REM (all cores) and meson's MSVC symbolextractor step is flaky on Windows --
REM it intermittently dies with 0xC000070A, which aborts the whole build.
REM Running ninja here with bounded parallelism and retrying gets through it;
REM the Clutter build afterwards finds rizin up to date and simply continues.
REM
REM Usage:  tools\build-rizin.bat [jobs]
setlocal
IF "%~1"=="" (set JOBS=8) ELSE (set JOBS=%~1)

REM Repo root = two levels up from this script (tools\..).
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RZB=%ROOT%\build-clutter\Rizin-Bundled-prefix\src\Rizin-Bundled-build"

if not exist "%RZB%" (
    echo [!] rizin build directory not found: %RZB%
    echo     Run build-clutter.bat configure first.
    exit /b 1
)

call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1

REM meson/ninja live in the project-local virtualenv.
if exist "%ROOT%\.tools\venv\Scripts" set "PATH=%ROOT%\.tools\venv\Scripts;%PATH%"

cd /d "%RZB%" || exit /b 1

set /a tries=0
:retry
echo ============================================================
echo [*] rizin build attempt %tries% with -j %JOBS%
echo ============================================================
ninja -j %JOBS%
if not errorlevel 1 goto installed
set /a tries+=1
if %tries% lss 12 goto retry
echo [!] rizin build failed after %tries% attempts
exit /b 1

:installed
echo [*] Installing rizin ...
ninja install
if errorlevel 1 exit /b 1
echo [+] rizin build + install complete
endlocal
