/* Launcher that makes the Python pkg-config shim look like a real pkg-config.exe.
 *
 * CMake's FindPkgConfig only accepts an executable file (it will not run a .bat),
 * so this forwards every argument to "python ../pkgconfig-shim.py" and passes the
 * exit code straight back. No system installation is involved: it is built by
 * build-clutter.bat into .tools\bin next to the batch wrapper.
 *
 * Build:  cl /nologo /O2 /Fe:pkg-config.exe pkgconfig-wrapper.c
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>

#define MAX_CMD 32768

static void quote_arg(char *dst, size_t dstsz, const char *arg)
{
    size_t len = strlen(dst);
    if (len + strlen(arg) * 2 + 8 > dstsz)
        return;
    /* Everything the shim receives is a plain option, module name or path
     * fragment, so simple quoting is enough. */
    dst[len++] = '"';
    dst[len] = '\0';
    while (*arg) {
        if (*arg == '"')
            dst[len++] = '\\';
        dst[len++] = *arg++;
    }
    dst[len++] = '"';
    dst[len++] = ' ';
    dst[len] = '\0';
}

int main(void)
{
    char exe[MAX_PATH];
    char shim[MAX_PATH];
    char cmd[MAX_CMD];
    char *args, *p;
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    DWORD rc = 1;

    if (!GetModuleFileNameA(NULL, exe, MAX_PATH))
        return 1;

    /* <bin>\pkg-config.exe  ->  <bin>\..\pkgconfig-shim.py */
    strcpy(shim, exe);
    p = strrchr(shim, '\\');
    if (!p)
        return 1;
    strcpy(p + 1, "..\\pkgconfig-shim.py");

    snprintf(cmd, sizeof(cmd), "python \"%s\" ", shim);
    args = GetCommandLineA();
    if (args) {
        /* skip argv[0] */
        char *q = args;
        if (*q == '"') {
            q++;
            while (*q && *q != '"')
                q++;
            if (*q)
                q++;
        } else {
            while (*q && *q != ' ')
                q++;
        }
        while (*q == ' ')
            q++;
        while (*q) {
            char token[4096];
            size_t n = 0;
            if (*q == '"') {
                q++;
                while (*q && *q != '"' && n < sizeof(token) - 1)
                    token[n++] = *q++;
                if (*q == '"')
                    q++;
            } else {
                while (*q && *q != ' ' && n < sizeof(token) - 1)
                    token[n++] = *q++;
            }
            token[n] = '\0';
            if (n)
                quote_arg(cmd, sizeof(cmd), token);
            while (*q == ' ')
                q++;
        }
    }

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    if (!CreateProcessA(NULL, cmd, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi))
        return 1;

    WaitForSingleObject(pi.hProcess, INFINITE);
    GetExitCodeProcess(pi.hProcess, &rc);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return (int)rc;
}
