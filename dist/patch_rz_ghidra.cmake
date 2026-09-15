# SPDX-License-Identifier: GPL-3.0-or-later
#
# Butter patch for rz-ghidra, applied to the freshly downloaded checkout by the
# install step (see dist/CMakeLists.txt, BUTTER_PACKAGE_RZ_GHIDRA).
#
# Why: rizin marks some stack slots as *arguments*, and for functions that
# address their frame through the stack pointer (no frame pointer, big local
# buffers) those "arguments" sit far outside anything an x86-64 ProtoModel can
# accept as an input parameter. rz-ghidra detects that and drops the variable
# entirely:
#
#     // WARNING: [rz-ghidra] Removing arg arg_78dch because it doesn't fit into ProtoModel
#
# The variable then disappears from the decompiled function, taking its data
# flow with it. Reproduced on the workspace crackme, where main loses three
# variables this way.
#
# What: a stack-stored "argument" that the input map rejects is emitted as a
# local variable instead of being skipped. Arguments that fail for any other
# reason (register storage, unusable address) keep the upstream behaviour, whose
# early return exists to avoid decompiler segfaults with typelock=false params.
#
# The edit is idempotent and leaves the checkout in a compiling state; it is not
# intended to be sent upstream as-is.
#
# Run standalone with:
#   cmake -DSRC=<rz-ghidra checkout> -P butter/dist/patch_rz_ghidra.cmake

if(NOT DEFINED SRC)
    message(FATAL_ERROR "patch_rz_ghidra: SRC is not set")
endif()

set(_file "${SRC}/src/RizinScope.cpp")
if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "patch_rz_ghidra: ${_file} not found")
endif()

file(READ "${_file}" _text)

if(_text MATCHES "butter: stack arg demotion")
    message(STATUS "rz-ghidra: Butter stack-arg patch already applied")
    return()
endif()

# Normalise line endings so the snippets below match regardless of git's
# autocrlf setting on the machine that cloned the tree.
string(REPLACE "\r\n" "\n" _text "${_text}")

string(REPLACE
"\t\tint4 paramIndex = -1;\n\t\tif(rz_analysis_var_is_arg(var))\n\t\t{\n\t\t\tif(proto && !proto->possibleInputParam(addr, type->getSize()))\n\t\t\t{\n\t\t\t\t// Prevent segfaults in the Decompiler\n\t\t\t\tarch->addWarning(\"Removing arg \" + to_string(var->name) + \" because it doesn't fit into ProtoModel\");\n\t\t\t\treturn true;\n\t\t\t}\n"
"\t\tint4 paramIndex = -1;\n\t\tbool isArg = rz_analysis_var_is_arg(var);\n\t\tif(isArg && proto && !proto->possibleInputParam(addr, type->getSize()))\n\t\t{\n\t\t\tif(var->storage.type == RZ_ANALYSIS_VAR_STORAGE_STACK)\n\t\t\t{\n\t\t\t\t// butter: stack arg demotion. No input map accepts this address, and on a\n\t\t\t\t// frame that is addressed through the stack pointer the slot is really a local.\n\t\t\t\t// Emitting it as one keeps the variable instead of dropping it.\n\t\t\t\tarch->addWarning(\"Treating stack arg \" + to_string(var->name) + \" as a local variable because it doesn't fit into ProtoModel\");\n\t\t\t\tisArg = false;\n\t\t\t}\n\t\t\telse\n\t\t\t{\n\t\t\t\t// Prevent segfaults in the Decompiler\n\t\t\t\tarch->addWarning(\"Removing arg \" + to_string(var->name) + \" because it doesn't fit into ProtoModel\");\n\t\t\t\treturn true;\n\t\t\t}\n\t\t}\n\n\t\tif(isArg)\n\t\t{\n"
_text "${_text}")

string(REPLACE
"\t\t\t\t{ \"cat\", rz_analysis_var_is_arg(var) ? \"0\" : \"-1\" }"
"\t\t\t\t{ \"cat\", isArg ? \"0\" : \"-1\" }"
_text "${_text}")

string(REPLACE
"\t\tif(rz_analysis_var_is_arg(var))\n\t\t{\n\t\t\tif(argsByIndex.size() < paramIndex + 1)"
"\t\tif(isArg)\n\t\t{\n\t\t\tif(argsByIndex.size() < paramIndex + 1)"
_text "${_text}")

string(REPLACE
"\t\tif(rz_analysis_var_is_arg(var) && var->storage.type == RZ_ANALYSIS_VAR_STORAGE_REG)"
"\t\tif(isArg && var->storage.type == RZ_ANALYSIS_VAR_STORAGE_REG)"
_text "${_text}")

if(NOT _text MATCHES "butter: stack arg demotion")
    message(FATAL_ERROR "patch_rz_ghidra: patch did not apply, RizinScope.cpp changed upstream?")
endif()

file(WRITE "${_file}" "${_text}")
message(STATUS "rz-ghidra: applied the Butter stack-arg patch")
