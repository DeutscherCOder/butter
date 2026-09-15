/* Clutter crackme -- a deliberately hostile Windows target.
 *
 * Protections:
 *   - the real check is a bytecode VM whose program lives in an encrypted blob
 *   - the blob is only decryptable with a key folded out of scattered constants
 *   - anti-debug: IsDebuggerPresent, PEB.BeingDebugged, CheckRemoteDebuggerPresent
 *     and a timing check. None of them exit: they poison the key, so under a
 *     debugger the payload decrypts to garbage and the check just fails.
 *   - the payload magic is not present as a string, it is derived at runtime
 *   - decoy checker with fake passwords, opaque dead branch, junk strings
 *
 * Build: crackme/build.bat
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <intrin.h>
#include <windows.h>

#include "blob_data.h"

/* Must match JUNK in gen_blob.py. */
static const uint32_t g_junk[16] = {
    0x9E3779B9u, 0x85EBCA6Bu, 0xC2B2AE35u, 0x27D4EB2Fu,
    0x165667B1u, 0x2545F491u, 0x94D049BBu, 0xBF58476Du,
    0x9FB21C65u, 0x7FEB352Du, 0x846CA68Bu, 0xDB4F0B91u,
    0xA1E38F1Du, 0x3E9841A3u, 0x5BD1E995u, 0x1B873593u,
};

#define BLOB_INIT 0x5A

/* VM opcodes (mirrored in gen_blob.py). */
#define OP_NOP 0x00
#define OP_PUSH_ARG 0x11
#define OP_PUSH_IMM 0x2A
#define OP_XOR 0x37
#define OP_ROTL 0x4C
#define OP_SECRET 0x55
#define OP_CMPNE 0x68
#define OP_LEN 0x73
#define OP_ACCEPT 0x8E
#define OP_HALT 0xF0

#define VM_STACK 8

static unsigned char rotl8(unsigned char v, unsigned char n)
{
    n &= 7;
    if (n == 0)
        return v;
    return (unsigned char)((v << n) | (v >> (8 - n)));
}

static uint32_t derive_key(void)
{
    uint32_t k = 0x9E3779B9u;
    for (int i = 0; i < 16; i++) {
        k = k * 1103515245u + 12345u;
        k ^= g_junk[i];
        k ^= k >> 7;
    }
    return k;
}

/* Returns 1 when something looks like it is watching us. */
static int is_debugged(void)
{
    if (IsDebuggerPresent())
        return 1;

    BOOL remote = FALSE;
    if (CheckRemoteDebuggerPresent(GetCurrentProcess(), &remote) && remote)
        return 1;

#ifdef _M_X64
    {
        unsigned long long peb = __readgsqword(0x60);
        if (peb) {
            unsigned char being_debugged = *(unsigned char *)(peb + 2);
            if (being_debugged)
                return 1;
        }
    }
#endif

    {
        LARGE_INTEGER t0, t1;
        volatile uint32_t sink = 0;
        QueryPerformanceCounter(&t0);
        for (uint32_t i = 1; i < 4000; i++)
            sink += (i * 2654435761u) >> 3;
        QueryPerformanceCounter(&t1);
        (void)sink;
        if (t1.QuadPart - t0.QuadPart > 3000000)
            return 1;
    }

    return 0;
}

static void decrypt_blob(const unsigned char *src, unsigned char *dst, unsigned int n, uint32_t key)
{
    unsigned char kb[4];
    unsigned char prev = BLOB_INIT;

    kb[0] = (unsigned char)(key);
    kb[1] = (unsigned char)(key >> 8);
    kb[2] = (unsigned char)(key >> 16);
    kb[3] = (unsigned char)(key >> 24);

    for (unsigned int i = 0; i < n; i++) {
        unsigned char c = rotl8(src[i], 3);
        c = (unsigned char)(c - (unsigned char)(prev * 3 + (unsigned char)i));
        c ^= kb[i & 3];
        dst[i] = c;
        prev = c;
    }
}

/* The real password check. Returns 1 only for the accepted input. */
static int vm_run(const unsigned char *code, unsigned int clen,
                  const unsigned char *secret, unsigned int slen,
                  const unsigned char *input, unsigned int ilen)
{
    int stack[VM_STACK];
    int sp = 0;
    unsigned int pc = 0;
    int accepted = 0;

    while (pc < clen) {
        unsigned char op = code[pc++];

        if (op == OP_NOP) {
            continue;
        } else if (op == OP_LEN) {
            if (pc >= clen || ilen != code[pc++])
                return 0;
        } else if (op == OP_PUSH_ARG) {
            if (pc >= clen || sp >= VM_STACK)
                return 0;
            stack[sp++] = (code[pc] < ilen) ? input[code[pc]] : -1;
            pc++;
        } else if (op == OP_SECRET) {
            if (pc >= clen || sp >= VM_STACK)
                return 0;
            stack[sp++] = (code[pc] < slen) ? secret[code[pc]] : -1;
            pc++;
        } else if (op == OP_PUSH_IMM) {
            if (pc >= clen || sp >= VM_STACK)
                return 0;
            stack[sp++] = code[pc++];
        } else if (op == OP_XOR) {
            int b, a;
            if (sp < 2)
                return 0;
            b = stack[--sp];
            a = stack[--sp];
            stack[sp++] = (a ^ b) & 0xFF;
        } else if (op == OP_ROTL) {
            int b, a;
            if (sp < 2)
                return 0;
            b = stack[--sp];
            a = stack[--sp];
            stack[sp++] = rotl8((unsigned char)a, (unsigned char)b);
        } else if (op == OP_CMPNE) {
            int b, a;
            if (sp < 2)
                return 0;
            b = stack[--sp];
            a = stack[--sp];
            if (a != b)
                return 0;
        } else if (op == OP_ACCEPT) {
            accepted = 1;
        } else if (op == OP_HALT) {
            break;
        } else {
            return 0; /* payload was tampered with */
        }
    }

    return accepted;
}

/* Always false, but not provable at compile time. */
static int opaque_false(void)
{
    volatile int x = 3;
    volatile int y = 7;
    for (int i = 0; i < 4; i++)
        x = x * y + i;
    return (x * x) < 0;
}

/* Decoy: looks like a password checker, is never reached. */
static const char *decoy_strings[] = {
    "Password: hunter2",
    "s3cr3t_k3y_do_not_sh4re",
    "correct horse battery staple",
    "VM_SALT_9f8e7d6c",
    "CLUTTER{str1ngs_ar3_f0r_b3g1nn3rs}",
    "admin:admin",
    "Access granted. flag: CLUTTER{h4rdc0d3d_ch3ck}",
};

static int decoy_check(const char *in)
{
    static const char *fake[] = {
        "hunter2",
        "s3cr3t_k3y_do_not_sh4re",
        "CLUTTER{str1ngs_ar3_f0r_b3g1nn3rs}",
    };

    for (unsigned i = 0; i < 3; i++) {
        if (strcmp(in, fake[i]) == 0)
            return 1;
    }
    for (unsigned i = 0; i < sizeof(decoy_strings) / sizeof(decoy_strings[0]); i++) {
        if (strstr(decoy_strings[i], in) != NULL && strlen(in) > 3)
            return 0;
    }
    return 0;
}

int main(int argc, char **argv)
{
    char buf[128];
    const char *input;
    unsigned char *payload;
    unsigned char magic[4];
    unsigned int slen, clen;
    uint32_t key;
    int ok;

    if (argc > 1) {
        input = argv[1];
    } else {
        printf("Enter password: ");
        fflush(stdout);
        if (fgets(buf, sizeof(buf), stdin) == NULL)
            return 1;
        buf[strcspn(buf, "\r\n")] = '\0';
        input = buf;
    }

    /* Junk work, so the interesting branch is not the first thing you see. */
    {
        volatile uint32_t noise = 0;
        size_t n = strlen(input) + 1;
        for (uint32_t i = 0; i < 64; i++)
            noise = noise * 2654435761u + (uint32_t)(unsigned char)input[i % n];
        (void)noise;
    }

    if (opaque_false()) {
        /* Dead code that looks like the real check. */
        if (decoy_check(input))
            printf("Access granted. flag: CLUTTER{h4rdc0d3d_ch3ck}\n");
        else
            printf("Access denied.\n");
        return 0;
    }

    key = derive_key();
    if (is_debugged())
        key ^= 0xDEADBEEFu; /* silently corrupt the payload instead of exiting */

    payload = (unsigned char *)malloc(G_BLOB_LEN + 32);
    if (payload == NULL)
        return 1;

    decrypt_blob(g_blob, payload, G_BLOB_LEN, key);

    /* The magic is not stored as a string anywhere. */
    magic[0] = (unsigned char)('C' ^ 0x11);
    magic[1] = (unsigned char)('K' ^ 0x22);
    magic[2] = (unsigned char)('R' ^ 0x33);
    magic[3] = (unsigned char)('1' ^ 0x44);
    for (int i = 0; i < 4; i++)
        magic[i] ^= (unsigned char)(0x11 * (i + 1));

    if (memcmp(payload, magic, 4) != 0)
        goto denied;

    slen = (unsigned int)payload[4] | ((unsigned int)payload[5] << 8);
    clen = (unsigned int)payload[6] | ((unsigned int)payload[7] << 8);
    if (8 + slen + clen > G_BLOB_LEN)
        goto denied;

    ok = vm_run(payload + 8 + slen, clen, payload + 8, slen,
                (const unsigned char *)input, (unsigned int)strlen(input));

    if (ok) {
        printf("Access granted. flag: CLUTTER{v1rtu4l_m4ch1n3s_4nd_p4ck3rs}\n");
        memset(payload, 0, G_BLOB_LEN);
        free(payload);
        return 0;
    }

denied:
    printf("Access denied.\n");
    memset(payload, 0, G_BLOB_LEN);
    free(payload);
    return 1;
}
