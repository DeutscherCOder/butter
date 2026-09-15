cmake_minimum_required(VERSION 3.12)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(DisallowInSource)
include(Utils)

set(CLUTTER_PYTHON_MIN 3.5)

option(CLUTTER_USE_BUNDLED_RIZIN "Use rizin from ./rizin submodule instead of searching for it on the system" ON)
option(CLUTTER_USE_ADDITIONAL_RIZIN_PATHS "Search rizin in additional paths which are not part of default system library paths.\
 Disable this option if you are linking against rizin pacakged as proper system library or in a custom path and additional are paths causing problems." ON)
option(CLUTTER_ENABLE_PYTHON "Enable Python integration. Requires Python >= ${CLUTTER_PYTHON_MIN}." OFF)
option(CLUTTER_ENABLE_PYTHON_BINDINGS "Enable generating Python bindings with Shiboken. Unused if CLUTTER_ENABLE_PYTHON=OFF." OFF)
option(CLUTTER_APPIMAGE_BUILD "Enable Appimage specific changes. Doesn't cause building of Appimage itself." OFF)
tri_option(CLUTTER_ENABLE_KSYNTAXHIGHLIGHTING "Use KSyntaxHighlighting" AUTO)
tri_option(CLUTTER_ENABLE_GRAPHVIZ "Enable use of graphviz for graph layout" AUTO)
set(SHIBOKEN_EXTRA_OPTIONS "" CACHE STRING "Extra options for shiboken generator")
set(CLUTTER_EXTRA_PLUGIN_DIRS "" CACHE STRING "List of addition plugin locations")
option(CLUTTER_ENABLE_DEPENDENCY_DOWNLOADS "Enable downloading of dependencies. Setting to OFF doesn't affect any downloads done by rizin build." OFF)
option(CLUTTER_ENABLE_PACKAGING "Enable building platform-specific packages for distributing" OFF)
option(CLUTTER_ENABLE_SIGDB "Downloads and installs sigdb (only available when CLUTTER_USE_BUNDLED_RIZIN=ON)." OFF)
option(CLUTTER_ENABLE_TRANSLATIONS "Build and install translation files" ON)
option(CLUTTER_PACKAGE_DEPENDENCIES "During install step include the third party dependencies." OFF)
option(CLUTTER_PACKAGE_RZ_GHIDRA "Compile and install rz-ghidra during install step." OFF)
option(CLUTTER_PACKAGE_RZ_LIBSWIFT "Compile and install rz-libswift demangler during the install step." OFF)
option(CLUTTER_PACKAGE_RZ_LIBYARA "Compile and install rz-libyara during the install step." OFF)
option(CLUTTER_PACKAGE_RZ_SILHOUETTE "Compile and install rz-silhouette during the install step." OFF)
option(CLUTTER_PACKAGE_RZ_FRIDA "Compile and install rz-frida during the install step." OFF)
option(CLUTTER_PACKAGE_JSDEC "Compile and install jsdec during install step." OFF)
set("CLUTTER_QT" 6 CACHE STRING "Major QT version to use 5|6")
set_property(CACHE "CLUTTER_QT" PROPERTY STRINGS 5 6)
option(CLUTTER_INCLUDE_GIT_HASH "Include git hash in full version" ON)
set(CLUTTER_VERSION_SUFFIX "" CACHE STRING "Can be used by packagers to differentiate multiple packages using same source, for example build number or presence of additional patches.")

if(NOT CLUTTER_ENABLE_PYTHON)
    set(CLUTTER_ENABLE_PYTHON_BINDINGS OFF)
endif()

set(CLUTTER_VERSION_MAJOR 2)
set(CLUTTER_VERSION_MINOR 5)
set(CLUTTER_VERSION_PATCH 0)

set(CLUTTER_VERSION "${CLUTTER_VERSION_MAJOR}.${CLUTTER_VERSION_MINOR}.${CLUTTER_VERSION_PATCH}")


if (CLUTTER_INCLUDE_GIT_HASH)
    execute_process(COMMAND git  -C "${CMAKE_CURRENT_SOURCE_DIR}" --git-dir=.git log --pretty=format:'%h' -n 1
                    OUTPUT_VARIABLE GIT_REV
                    ERROR_QUIET)
endif()

# Check whether we got any revision (which isn't
# always the case, e.g. when someone downloaded a zip file
if (NOT CLUTTER_INCLUDE_GIT_HASH OR "${GIT_REV}" STREQUAL "")
    set(CLUTTER_VERSION_FULL "${CLUTTER_VERSION}${CLUTTER_VERSION_SUFFIX}")
else()
    execute_process(
        COMMAND git -C "${CMAKE_CURRENT_SOURCE_DIR}" --git-dir=.git rev-parse --abbrev-ref HEAD
        OUTPUT_VARIABLE GIT_BRANCH)
    string(STRIP "${GIT_REV}" GIT_REV)
    string(SUBSTRING "${GIT_REV}" 1 7 GIT_REV)
    string(STRIP "${GIT_BRANCH}" GIT_BRANCH)
    set(CLUTTER_VERSION_FULL "${CLUTTER_VERSION}${CLUTTER_VERSION_SUFFIX}-${GIT_BRANCH}-${GIT_REV}")
endif()

project(Clutter VERSION "${CLUTTER_VERSION}")

# Enable solution folder support
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# Put Qt files in a separate folder
set_property(GLOBAL PROPERTY AUTOGEN_SOURCE_GROUP "Generated Files")

set(CMAKE_CXX_STANDARD 20)

include(ClutterInstallDirs)

if(CLUTTER_USE_BUNDLED_RIZIN)
    include(BundledRizin)
    set(RIZIN_TARGET Rizin)
else()
    find_package(Rizin COMPONENTS Core REQUIRED)
    set(RIZIN_TARGET Rizin::Core)
endif()

set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)
set(QT_COMPONENTS Core Widgets Gui Svg Network)
if (CLUTTER_QT GREATER_EQUAL 6)
    list(APPEND QT_COMPONENTS Core5Compat SvgWidgets OpenGLWidgets)
endif()
set(QT_PREFIX "Qt${CLUTTER_QT}")
find_package(${QT_PREFIX} REQUIRED COMPONENTS ${QT_COMPONENTS})

if(CLUTTER_ENABLE_PYTHON)
    find_package (Python3 ${CLUTTER_PYTHON_MIN} REQUIRED COMPONENTS Interpreter Development)
    set (PYTHON_EXECUTABLE ${Python3_EXECUTABLE})

    add_definitions(-DCLUTTER_ENABLE_PYTHON)

    if(CLUTTER_ENABLE_PYTHON_BINDINGS)
        if (CLUTTER_QT GREATER_EQUAL 6)
            # 6.12.3 => 6.12
            if("${Qt6_VERSION}" MATCHES "^([0-9]+\\.[0-9]+)\\.[0-9]+")
                set(Shiboken6_VERSION_REQUIRED "${CMAKE_MATCH_1}")
            else()
                message(FATAL_ERROR "Failed to recognize Qt version")
            endif()
            find_package(Shiboken6 "${Shiboken6_VERSION_REQUIRED}" REQUIRED)
            find_package(Shiboken6Tools "${Shiboken6_VERSION_REQUIRED}" REQUIRED)
            find_package(PySide6 "${Shiboken6_VERSION_REQUIRED}" REQUIRED)
            get_target_property(LIBSHIBOKEN_INCLUDE_DIRS Shiboken6::libshiboken INTERFACE_INCLUDE_DIRECTORIES)
            get_target_property(PYSIDE_INCLUDE_DIRS PySide6::pyside6 INTERFACE_INCLUDE_DIRECTORIES)
            # Check the presence of "pysidecleanup.h"
            include(CheckIncludeFileCXX)
            set(CMAKE_REQUIRED_INCLUDES "${PYSIDE_INCLUDE_DIRS};${LIBSHIBOKEN_INCLUDE_DIRS}")
            CHECK_INCLUDE_FILE_CXX("pysidecleanup.h" HAVE_PYSIDECLEANUP)
            add_compile_definitions("HAVE_PYSIDECLEANUP=${HAVE_PYSIDECLEANUP}")
        elseif(CLUTTER_QT EQUAL 5)
            # 5.12.3 => 5.12
            if("${Qt5_VERSION}" MATCHES "^([0-9]+\\.[0-9]+)\\.[0-9]+")
                set(Shiboken2_VERSION_REQUIRED "${CMAKE_MATCH_1}")
            else()
                message(FATAL_ERROR "Failed to recognize Qt version")
            endif()
            find_package(Shiboken2 "${Shiboken2_VERSION_REQUIRED}" REQUIRED)
            find_package(PySide2 "${Shiboken2_VERSION_REQUIRED}" REQUIRED)
            get_target_property(PYSIDE_INCLUDE_DIRS PySide2::pyside2 INTERFACE_INCLUDE_DIRECTORIES)
        else()
            message(FATAL_ERROR "Unsupported QT version ${CLUTTER_QT}")
        endif()

        foreach(_dir IN LISTS PYSIDE_INCLUDE_DIRS)
            include_directories(${_dir}
                ${_dir}/QtCore
                ${_dir}/QtGui
                ${_dir}/QtWidgets)
        endforeach()

        add_definitions(-DCLUTTER_ENABLE_PYTHON_BINDINGS)
    endif()
endif()

if(CLUTTER_ENABLE_KSYNTAXHIGHLIGHTING)
    if(CLUTTER_ENABLE_KSYNTAXHIGHLIGHTING STREQUAL AUTO)
        find_package(KF${CLUTTER_QT}SyntaxHighlighting)
        if(KF${CLUTTER_QT}SyntaxHighlighting_FOUND)
            set(KSYNTAXHIGHLIGHTING_STATUS ON)
        else()
            set(KSYNTAXHIGHLIGHTING_STATUS "OFF (KSyntaxHighlighting not found)")
        endif()
    else()
        find_package(KF${CLUTTER_QT}SyntaxHighlighting REQUIRED)
        set(KSYNTAXHIGHLIGHTING_STATUS ON)
    endif()
endif()

if (CLUTTER_ENABLE_GRAPHVIZ)
    if (CLUTTER_ENABLE_GRAPHVIZ STREQUAL AUTO)
        find_package(Graphviz)
    else()
        find_package(Graphviz REQUIRED)
    endif()
    set (CLUTTER_ENABLE_GRAPHVIZ ${Graphviz_FOUND})
endif()

message(STATUS "")
message(STATUS "Building Clutter version ${CLUTTER_VERSION_FULL}")
message(STATUS "Options:")
message(STATUS "- Bundled rizin: ${CLUTTER_USE_BUNDLED_RIZIN}")
if(CLUTTER_USE_BUNDLED_RIZIN)
    message(STATUS "- Bundled sigdb: ${CLUTTER_ENABLE_SIGDB}")
endif()
message(STATUS "- Python: ${CLUTTER_ENABLE_PYTHON}")
message(STATUS "- Python Bindings: ${CLUTTER_ENABLE_PYTHON_BINDINGS}")
message(STATUS "- KSyntaxHighlighting: ${KSYNTAXHIGHLIGHTING_STATUS}")
message(STATUS "- Graphviz: ${CLUTTER_ENABLE_GRAPHVIZ}")
message(STATUS "- Downloads dependencies: ${CLUTTER_ENABLE_DEPENDENCY_DOWNLOADS}")
message(STATUS "- Enable Packaging: ${CLUTTER_ENABLE_PACKAGING}")
message(STATUS "- Package Dependencies: ${CLUTTER_PACKAGE_DEPENDENCIES}")
message(STATUS "- Package RzGhidra: ${CLUTTER_PACKAGE_RZ_GHIDRA}")
message(STATUS "- Package RzLibSwift: ${CLUTTER_PACKAGE_RZ_LIBSWIFT}")
message(STATUS "- Package RzLibYara: ${CLUTTER_PACKAGE_RZ_LIBYARA}")
message(STATUS "- Package RzSilhouette: ${CLUTTER_PACKAGE_RZ_SILHOUETTE}")
message(STATUS "- Package RzFrida: ${CLUTTER_PACKAGE_RZ_FRIDA}")
message(STATUS "- Package JSDec: ${CLUTTER_PACKAGE_JSDEC}")
message(STATUS "- QT: ${CLUTTER_QT}")
message(STATUS "")

if (CLUTTER_QT LESS 5 OR CLUTTER_QT GREATER 6)
    message(FATAL_ERROR "Unsupported QT major version")
endif()

add_subdirectory(src)

if(CLUTTER_ENABLE_PACKAGING)
	add_subdirectory(dist)
endif()
