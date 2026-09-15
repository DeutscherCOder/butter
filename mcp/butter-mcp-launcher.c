/*
 * butter-mcp.exe - launcher for the Butter MCP server.
 *
 * Real MCP clients (Claude Desktop, Cline, ...) want an executable path, not a
 * "python script.py" argument list. This wrapper finds the user's Python,
 * locates butter_mcp.py next to itself and runs it, forwarding the exit code.
 * Any command-line arguments are passed through untouched (e.g. --ui, --http,
 * --rizin, --file).
 *
 * Build:  tools\build-mcp-exe.bat
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

static char self_dir[MAX_PATH];
static char py_exe[MAX_PATH];
static char script[MAX_PATH];
static char cmdline[32768];

static int file_exists(const char *p)
{
    DWORD a = GetFileAttributesA(p);
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

/* Prefer the machine-wide py launcher to resolve the newest 3.x, then the
 * standard per-user install, then PATH. */
static int find_python(void)
{
    char buf[MAX_PATH];
    DWORD n;
    SHELLEXECUTEINFOA si;
    HANDLE h;
    DWORD exit_code = (DWORD)-1;

    FILE *pf = _popen("py -3.12 -c \"import sys;print(sys.executable)\" 2>nul",
                      "r");
    if (pf) {
        if (fgets(buf, sizeof(buf), pf) && strlen(buf) > 4) {
            buf[strcspn(buf, "\r\n")] = 0;
            if (file_exists(buf)) {
                lstrcpynA(py_exe, buf, MAX_PATH);
                _pclose(pf);
                return 1;
            }
        }
        _pclose(pf);
    }
    n = GetEnvironmentVariableA("LOCALAPPDATA", buf, MAX_PATH);
    if (n && n < MAX_PATH - 64) {
        lstrcpynA(py_exe, buf, MAX_PATH);
        lstrcatA(py_exe, "\\Programs\\Python\\Python312\\pythonw.exe");
        if (file_exists(py_exe))
            return 1;
    }
    /* last resort: bare pythonw on PATH */
    lstrcpynA(py_exe, "pythonw.exe", MAX_PATH);
    return file_exists(py_exe) || SearchPathA(NULL, "pythonw.exe", NULL,
                                              MAX_PATH, py_exe, NULL) != 0;
}

int main(int argc, char **argv)
{
    int i;
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    DWORD exit_code = 1;

    if (!GetModuleFileNameA(NULL, self_dir, MAX_PATH)) {
        fprintf(stderr, "butter-mcp: cannot resolve own path\n");
        return 2;
    }
    {
        char *slash = strrchr(self_dir, '\\');
        if (slash)
            *slash = 0;
    }
    if (!find_python()) {
        fprintf(stderr,
                "butter-mcp: python 3.12 not found; install it or add it to PATH\n");
        return 2;
    }
    lstrcpyA(script, self_dir);
    lstrcatA(script, "\\butter_mcp.py");
    if (!file_exists(script)) {
        fprintf(stderr, "butter-mcp: missing %s\n", script);
        return 2;
    }

    lstrcpyA(cmdline, "\"");
    lstrcatA(cmdline, py_exe);
    lstrcatA(cmdline, "\" \"");
    lstrcatA(cmdline, script);
    lstrcatA(cmdline, "\"");
    for (i = 1; i < argc; i++) {
        lstrcatA(cmdline, " \"");
        lstrcatA(cmdline, argv[i]);
        lstrcatA(cmdline, "\"");
    }

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    if (!CreateProcessA(NULL, cmdline, NULL, NULL, TRUE, 0, NULL, NULL,
                        &si, &pi)) {
        fprintf(stderr, "butter-mcp: CreateProcess failed (%lu)\n",
                GetLastError());
        return 2;
    }
    WaitForSingleObject(pi.hProcess, INFINITE);
    GetExitCodeProcess(pi.hProcess, &exit_code);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return (int)exit_code;
}
