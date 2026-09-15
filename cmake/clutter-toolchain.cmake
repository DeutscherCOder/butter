# Clutter (Clutter fork) portable build toolchain tweaks.
#
# This file is not a real cross-compilation toolchain. It only carries a couple of
# settings that must also reach the sub-projects that Clutter configures for us
# (most importantly rz-ghidra, the official Ghidra decompiler port, which is
# configured by dist/CMakeLists.txt during the install step).

# 1. Modern CMake (4.x) refuses cmake_minimum_required() version ranges that
#    start below 3.5. rz-ghidra still declares "3.0...3.5", so raise the floor
#    instead of patching third-party sources.
set(CMAKE_POLICY_VERSION_MINIMUM 3.5 CACHE STRING
    "Minimum CMake policy version accepted for legacy projects")

# 2. The Ghidra decompiler needs zlib to read compressed sleigh data. Use the
#    copy rz-ghidra fetches itself so that no system/vcpkg zlib is required.
set(USE_SYSTEM_ZLIB OFF CACHE BOOL
    "Use system zlib instead of the bundled one (rz-ghidra)")

# 3. Keep the decompiler's bundled third-party libs self-contained as well.
set(USE_SYSTEM_PUGIXML OFF CACHE BOOL
    "Use system pugixml instead of the bundled one (rz-ghidra)")
