@echo off
REM Build mcp\butter-mcp.exe - the launcher real MCP clients configure by path.
REM Usage: tools\build-mcp-exe.bat   (VS 2026 Build Tools required)
setlocal enableextensions
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "VCVARS=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VCVARS%" (
    echo [!] vcvars64.bat not found at "%VCVARS%"
    exit /b 1
)
call "%VCVARS%" >nul
if errorlevel 1 exit /b 1
cl /nologo /O2 /W3 "%ROOT%\mcp\butter-mcp-launcher.c" ^
   /Fe:"%ROOT%\mcp\butter-mcp.exe" /Fo:"%ROOT%\mcp\butter-mcp-launcher.obj" ^
   /link /SUBSYSTEM:CONSOLE
if errorlevel 1 exit /b 1
del "%ROOT%\mcp\butter-mcp-launcher.obj" >nul 2>&1
echo [+] built %ROOT%\mcp\butter-mcp.exe
echo     Configure MCP clients with:
echo       "command": "...\\mcp\\butter-mcp.exe"
echo       "args":    ["--ui"]        (optional: GUI mode)
exit /b 0
