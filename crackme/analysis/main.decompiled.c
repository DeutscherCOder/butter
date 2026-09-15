// WARNING: Variable defined which should be unmapped: var_c8h
// WARNING: [rz-ghidra] Detected overlap for variable var_9h
// WARNING: [rz-ghidra] Detected overlap for variable var_ah
// WARNING: [rz-ghidra] Detected overlap for variable var_bh
// WARNING: [rz-ghidra] Removing arg arg_78dch because it doesn't fit into ProtoModel
// WARNING: [rz-ghidra] Removing arg arg_789ch because it doesn't fit into ProtoModel
// WARNING: [rz-ghidra] Removing arg arg_7860h because it doesn't fit into ProtoModel

undefined8 main(int argc, char **argv)
{
    bool bVar1;
    undefined auVar2 [32];
    undefined auVar3 [32];
    uint16_t uVar4;
    undefined uVar5;
    undefined uVar6;
    int64_t iVar7;
    int64_t iVar8;
    uint64_t uVar9;
    undefined8 uVar10;
    uint32_t *arg1;
    undefined uVar11;
    undefined uVar12;
    char *arg1_00;
    int32_t iVar13;
    uint64_t uVar14;
    int64_t *arg2;
    uint8_t *arg2_00;
    int64_t *arg1_01;
    uint8_t uVar15;
    char cVar16;
    uint32_t uVar17;
    int64_t in_R8;
    uint32_t *arg3;
    uint32_t uVar18;
    int64_t in_R9;
    uint64_t arg4;
    uint8_t *arg4_00;
    int64_t unaff_GS_OFFSET;
    undefined auVar19 [16];
    int64_t var_8h;
    PBOOL pbDebuggerPresent;
    LARGE_INTEGER *var_20h;
    int64_t var_c8h;
    int64_t var_c0h;
    LARGE_INTEGER *lpPerformanceCount;
    int64_t var_a8h;
    int64_t in_stack_ffffffffffffff80;
    int64_t in_stack_ffffffffffffffa0;
    
    bVar1 = true;
    if (argc < 2) {
        fcn.1400014a0(0x1400185c8, (int64_t)argv, in_R8, in_R9);
        iVar8 = fcn.140004de4(1);
        fcn.14000526c(iVar8);
        iVar8 = fcn.140004de4(0);
        iVar7 = fcn.14000543c((int64_t)&var_a8h, 0x80, iVar8, in_stack_ffffffffffffff80);
        if (iVar7 == 0) {
            return 1;
        }
        iVar8 = fcn.140007580((int64_t)&var_a8h, 0x1400185dc, iVar8, in_R9);
        arg1_01 = &var_a8h;
        *(undefined *)((int64_t)&var_a8h + iVar8) = 0;
    } else {
        arg1_01 = (int64_t *)argv[1];
    }
    var_8h._0_4_ = 0;
    iVar8 = fcn.140017790((int64_t)arg1_01);
    arg4 = 0;
    do {
        uVar14 = arg4 % (iVar8 + 1U);
        uVar18 = (int32_t)arg4 + 1;
        arg4 = (uint64_t)uVar18;
        var_8h._0_4_ = (uint32_t)*(uint8_t *)((int64_t)arg1_01 + uVar14) + (uint32_t)var_8h * -0x61c8864f;
        uVar14 = (uint64_t)(uint32_t)var_8h;
    } while (uVar18 < 0x40);
    iVar13 = 0;
    var_8h._0_4_ = 3;
    pbDebuggerPresent._0_4_ = 7;
    do {
        var_8h._0_4_ = (uint32_t)var_8h * 7 + iVar13;
        iVar13 = iVar13 + 1;
    } while (iVar13 < 4);
    if (-1 < (int32_t)((uint32_t)var_8h * (uint32_t)var_8h)) {
        iVar13 = (*_sym.imp.KERNEL32.dll_IsDebuggerPresent)();
        if (iVar13 == 0) {
            pbDebuggerPresent._0_4_ = 0;
            uVar10 = (*_sym.imp.KERNEL32.dll_GetCurrentProcess)();
            iVar13 = (*_sym.imp.KERNEL32.dll_CheckRemoteDebuggerPresent)(uVar10, &pbDebuggerPresent);
            if ((iVar13 == 0) || ((int32_t)pbDebuggerPresent == 0)) {
                if ((*(int64_t *)(unaff_GS_OFFSET + 0x60) == 0) ||
                   (*(char *)(*(int64_t *)(unaff_GS_OFFSET + 0x60) + 2) == '\0')) {
                    var_8h._0_4_ = 0;
                    (*_sym.imp.KERNEL32.dll_QueryPerformanceCounter)(&lpPerformanceCount);
                    uVar18 = 1;
                    do {
                        uVar17 = uVar18 * -0x61c8864f;
                        uVar18 = uVar18 + 1;
                        var_8h._0_4_ = (uVar17 >> 3) + (uint32_t)var_8h;
                    } while (uVar18 < 4000);
                    (*_sym.imp.KERNEL32.dll_QueryPerformanceCounter)(&var_20h);
                    bVar1 = 3000000 < (int64_t)var_20h - (int64_t)lpPerformanceCount;
                } else {
                    bVar1 = true;
                }
            } else {
                bVar1 = true;
            }
        } else {
            bVar1 = true;
        }
        arg1 = (uint32_t *)fcn.1400074c0(0x1a5);
        if (arg1 != (uint32_t *)0x0) {
            uVar11 = 0xda;
            if (!bVar1) {
                uVar11 = 0x35;
            }
            arg3 = (uint32_t *)0x5a;
            uVar12 = 0x7f;
            if (!bVar1) {
                uVar12 = 0xc1;
            }
            uVar5 = 0xf7;
            if (!bVar1) {
                uVar5 = 0x5a;
            }
            uVar6 = 0x56;
            if (!bVar1) {
                uVar6 = 0x88;
            }
            var_8h._0_4_ = CONCAT13(uVar6, CONCAT12(uVar5, CONCAT11(uVar12, uVar11)));
            arg4_00 = (uint8_t *)0x0;
            do {
                arg2_00 = arg4_00;
                uVar18 = (uint32_t)arg2_00 + 1;
                arg4_00 = (uint8_t *)(uint64_t)uVar18;
                uVar15 = ((arg2_00[0x140018320] >> 5 | arg2_00[0x140018320] << 3) + (char)arg3 * -3) - (char)arg2_00 ^
                         *(uint8_t *)((int64_t)&var_8h + (uint64_t)((uint32_t)arg2_00 & 3));
                arg3 = (uint32_t *)(uint64_t)uVar15;
                *(uint8_t *)((int64_t)arg1 + (int64_t)arg2_00) = uVar15;
            } while (uVar18 < 0x185);
            var_8h._0_4_ = 0x75616952;
            if (_data.140023050 < 6) {
                arg3 = (uint32_t *)0x0;
                do {
                    arg2_00 = (uint8_t *)((int64_t)&var_8h + (int64_t)arg3);
                    cVar16 = (char)arg3;
                    uVar17 = (int32_t)arg3 + 1;
                    arg3 = (uint32_t *)(uint64_t)uVar17;
                    *arg2_00 = *arg2_00 ^ cVar16 * '\x11' + 0x11U;
                    uVar18 = (uint32_t)var_8h;
                } while ((int32_t)uVar17 < 4);
            } else {
                auVar2 = vpmovzxbw_avx2(*(undefined (*) [16])0x140018670);
                auVar3 = vpmovzxbw_avx2(ZEXT416(0x3020100));
                auVar2 = vpmullw_avx2(auVar3, auVar2);
                auVar19 = vpmovwb_avx512vl(auVar2);
                uVar18 = CONCAT13(auVar19[3] + SUB161(*(undefined (*) [16])0x140018670, 3), 
                                  CONCAT12(auVar19[2] + SUB161(*(undefined (*) [16])0x140018670, 2), 
                                           CONCAT11(auVar19[1] + SUB161(*(undefined (*) [16])0x140018670, 1), 
                                                    auVar19[0] + SUB161(*(undefined (*) [16])0x140018670, 0)))) ^
                         0x75616952;
            }
            if (*arg1 == uVar18) {
                uVar18 = (uint32_t)(uint16_t)arg1[1];
                uVar4 = *(uint16_t *)((int64_t)arg1 + 6);
                if (uVar18 + 8 + (uint32_t)uVar4 < 0x186) {
                    fcn.140017790((int64_t)arg1_01);
                    arg3 = arg1 + 2;
                    arg4_00 = (uint8_t *)(uint64_t)uVar18;
                    arg2_00 = (uint8_t *)(uint64_t)(uint32_t)uVar4;
                    iVar13 = fcn.140001500((uint64_t)uVar18 + 8 + (int64_t)arg1, (int64_t)arg2_00, (int64_t)arg3, 
                                           (int64_t)arg4_00, (int64_t)arg1_01, in_stack_ffffffffffffffa0);
                    if (iVar13 != 0) {
                        fcn.1400014a0(0x140018620, (int64_t)arg2_00, (int64_t)arg3, (int64_t)arg4_00);
                        fcn.140016cc0((int64_t)arg1, 0, 0x185);
                        fcn.1400074b0((long long unsigned int)arg1);
                        return 0;
                    }
                }
            }
            fcn.1400014a0(0x140018610, (int64_t)arg2_00, (int64_t)arg3, (int64_t)arg4_00);
            fcn.140016cc0((int64_t)arg1, 0, 0x185);
            fcn.1400074b0((long long unsigned int)arg1);
        }
    // WARNING: Read-only address (ram,0x000140018670) is written
        return 1;
    }
    arg2 = _data.140023038;
    iVar13 = fcn.140017710((int64_t)arg1_01, (long long unsigned int)_data.140023038);
    if (((iVar13 != 0) &&
        (arg2 = _data.140023040, iVar13 = fcn.140017710((int64_t)arg1_01, (long long unsigned int)_data.140023040),
        iVar13 != 0)) &&
       (arg2 = _data.140023048, iVar13 = fcn.140017710((int64_t)arg1_01, (long long unsigned int)_data.140023048),
       iVar13 != 0)) {
        uVar18 = 0;
        do {
            arg2 = arg1_01;
            iVar8 = fcn.140002200(*(int64_t *)((uint64_t)uVar18 * 8 + 0x140023000), (int64_t)arg1_01);
            if ((iVar8 != 0) && (uVar9 = fcn.140017790((int64_t)arg1_01), 3 < uVar9)) break;
            uVar18 = uVar18 + 1;
        } while (uVar18 < 7);
        bVar1 = false;
    }
    arg1_00 = "Access granted. flag: BUTTER{h4rdc0d3d_ch3ck}\n";
    if (!bVar1) {
        arg1_00 = "Access denied.\n";
    }
    fcn.1400014a0((int64_t)arg1_00, (int64_t)arg2, uVar14, arg4);
    return 0;
}