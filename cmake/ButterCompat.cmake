# SPDX-License-Identifier: GPL-3.0-or-later
#
# Forwarding CMake package for out-of-tree plugins written against upstream
# Butter. Installed as lib/cmake/Butter/ButterConfig.cmake, it loads the
# Butter package and re-exposes it under the old name:
#
#     find_package(Butter REQUIRED)      # works
#     target_link_libraries(mine Butter::Butter)
#
# The target is an interface wrapper around Butter::Butter, so plugins keep
# getting the same include directories and link libraries. See the "Rebrand and
# compatibility" section of README.md.

include("${CMAKE_CURRENT_LIST_DIR}/../Butter/ButterConfig.cmake")

if(NOT TARGET Butter::Butter)
    add_library(Butter::Butter INTERFACE IMPORTED GLOBAL)
    set_target_properties(Butter::Butter PROPERTIES
        INTERFACE_LINK_LIBRARIES Butter::Butter)
endif()

# rz-frida's butter plugin reads the rizin include dirs off Butter::Rizin
# (upstream exported Rizin as Butter::Rizin; the rebrand exports it as
# Butter::Rizin). Forward it the same way so find_package(Butter) keeps
# working for that plugin without patching its CMakeLists.
if(NOT TARGET Butter::Rizin)
    if(TARGET Butter::Rizin)
        add_library(Butter::Rizin INTERFACE IMPORTED GLOBAL)
        set_target_properties(Butter::Rizin PROPERTIES
            INTERFACE_LINK_LIBRARIES Butter::Rizin)
    elseif(TARGET Rizin)
        add_library(Butter::Rizin INTERFACE IMPORTED GLOBAL)
        set_target_properties(Butter::Rizin PROPERTIES
            INTERFACE_LINK_LIBRARIES Rizin)
    endif()
endif()

set(Butter_RIZIN_BUNDLED "${Butter_RIZIN_BUNDLED}")
set(Butter_USER_PLUGINDIR "${Butter_USER_PLUGINDIR}")
