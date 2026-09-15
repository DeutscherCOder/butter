@echo off
REM Build the Clutter crackme.
REM   step 1: gen_blob.py writes blob_data.h (the encrypted payload)
REM   step 2: cl compiles crackme.exe, statically linked, no PDB
REM Note: gen_blob.py contains the password, so only crackme.exe is distributable.
setlocal
cd /d "%~dp0" || exit /b 1

where python >nul 2>&1 || (echo [!] python not found & exit /b 1)
python gen_blob.py || exit /b 1
if not exist blob_data.h (echo [!] gen_blob.py did not produce blob_data.h & exit /b 1)

call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 (echo [!] vcvars64.bat failed & exit /b 1)

cl /nologo /O2 /MT /GS- /Fe:crackme.exe crackme.c
if errorlevel 1 exit /b 1

del /q *.obj >nul 2>&1
echo [+] built crackme.exe
endlocal
