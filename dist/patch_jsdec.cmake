# SPDX-License-Identifier: GPL-3.0-or-later
#
# Clutter patch for jsdec, applied to the freshly cloned checkout by the
# install step (see dist/bundle_jsdec.ps1).
#
# Why: jsdec's cutter-plugin/JSDecDecompiler.h uses `CutterCore *` but only
# includes "Decompiler.h" and "RizinTask.h". Upstream those headers
# forward-declared `class CutterCore`, so it compiled. After the rebrand the
# core class is `ClutterCore` and `CutterCore` only exists as an alias in
# <Cutter.h> (see src/compat/core/CutterCompat.h), which the header does not
# include - the .cpp includes it too late. So the build dies with:
#
#     error C2061: syntax error: identifier 'CutterCore'
#
# What: include <Cutter.h> from the header so the alias is visible wherever
# the header is used. The edit is idempotent.
#
# Run standalone with:
#   cmake -DSRC=<jsdec checkout> -P cutter/dist/patch_jsdec.cmake

if(NOT DEFINED SRC)
    message(FATAL_ERROR "patch_jsdec: SRC is not set")
endif()

set(_file "${SRC}/cutter-plugin/JSDecDecompiler.h")
if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "patch_jsdec: ${_file} not found")
endif()

file(READ "${_file}" _text)

if(_text MATCHES "clutter: include Cutter.h for CutterCore")
    message(STATUS "jsdec: Clutter CutterCore patch already applied")
    return()
endif()

string(REPLACE "\r\n" "\n" _text "${_text}")

string(REPLACE
"#include \"Decompiler.h\"\n#include \"RizinTask.h\""
"#include \"Decompiler.h\"\n#include \"RizinTask.h\"\n#include <Cutter.h> // clutter: include Cutter.h for CutterCore"
_text "${_text}")

if(NOT _text MATCHES "clutter: include Cutter.h for CutterCore")
    message(FATAL_ERROR "patch_jsdec: patch did not apply, JSDecDecompiler.h changed upstream?")
endif()

file(WRITE "${_file}" "${_text}")
message(STATUS "jsdec: applied the Clutter CutterCore patch")
