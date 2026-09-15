@echo off
REM Build the project-local pkg-config.exe launcher (see pkgconfig-wrapper.c).
REM Called by build-butter.bat when the launcher is missing; MSVC must be on PATH.
setlocal
set "BINDIR=%~dp0bin"
if not exist "%BINDIR%" mkdir "%BINDIR%"
cd /d "%BINDIR%" || exit /b 1
cl /nologo /O2 /Fe:pkg-config.exe "%~dp0pkgconfig-wrapper.c" >nul
if errorlevel 1 (
    echo [!] Failed to build tools\bin\pkg-config.exe
    exit /b 1
)
del /q *.obj >nul 2>&1
echo [+] built tools\bin\pkg-config.exe
endlocal
