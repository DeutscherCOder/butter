# SPDX-License-Identifier: GPL-3.0-or-later
#
# Forwarding CMake package for out-of-tree plugins written against upstream
# Cutter. Installed as lib/cmake/Cutter/CutterConfig.cmake, it loads the
# Clutter package and re-exposes it under the old name:
#
#     find_package(Cutter REQUIRED)      # works
#     target_link_libraries(mine Cutter::Cutter)
#
# The target is an interface wrapper around Clutter::Clutter, so plugins keep
# getting the same include directories and link libraries. See the "Rebrand and
# compatibility" section of README.md.

include("${CMAKE_CURRENT_LIST_DIR}/../Clutter/ClutterConfig.cmake")

if(NOT TARGET Cutter::Cutter)
    add_library(Cutter::Cutter INTERFACE IMPORTED GLOBAL)
    set_target_properties(Cutter::Cutter PROPERTIES
        INTERFACE_LINK_LIBRARIES Clutter::Clutter)
endif()

# rz-frida's cutter plugin reads the rizin include dirs off Cutter::Rizin
# (upstream exported Rizin as Cutter::Rizin; the rebrand exports it as
# Clutter::Rizin). Forward it the same way so find_package(Cutter) keeps
# working for that plugin without patching its CMakeLists.
if(NOT TARGET Cutter::Rizin)
    if(TARGET Clutter::Rizin)
        add_library(Cutter::Rizin INTERFACE IMPORTED GLOBAL)
        set_target_properties(Cutter::Rizin PROPERTIES
            INTERFACE_LINK_LIBRARIES Clutter::Rizin)
    elseif(TARGET Rizin)
        add_library(Cutter::Rizin INTERFACE IMPORTED GLOBAL)
        set_target_properties(Cutter::Rizin PROPERTIES
            INTERFACE_LINK_LIBRARIES Rizin)
    endif()
endif()

set(Cutter_RIZIN_BUNDLED "${Clutter_RIZIN_BUNDLED}")
set(Cutter_USER_PLUGINDIR "${Clutter_USER_PLUGINDIR}")
