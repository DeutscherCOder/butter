@echo off
REM Compile the small probe binary used to inspect decompiler output formatting.
setlocal
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cd /d "%~dp0" || exit /b 1
REM /Zi /DEBUG keeps probe.pdb next to the exe so rizin can resolve sym.main etc.
cl /nologo /O1 /Zi /DEBUG /Fe:probe.exe probe.c
if errorlevel 1 exit /b 1
echo [+] built tools\testprobe\probe.exe
endlocal
