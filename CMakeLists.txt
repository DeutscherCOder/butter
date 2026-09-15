cmake_minimum_required(VERSION 3.12)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(DisallowInSource)
include(Utils)

set(BUTTER_PYTHON_MIN 3.5)

option(BUTTER_USE_BUNDLED_RIZIN "Use rizin from ./rizin submodule instead of searching for it on the system" ON)
option(BUTTER_USE_ADDITIONAL_RIZIN_PATHS "Search rizin in additional paths which are not part of default system library paths.\
 Disable this option if you are linking against rizin pacakged as proper system library or in a custom path and additional are paths causing problems." ON)
option(BUTTER_ENABLE_PYTHON "Enable Python integration. Requires Python >= ${BUTTER_PYTHON_MIN}." OFF)
option(BUTTER_ENABLE_PYTHON_BINDINGS "Enable generating Python bindings with Shiboken. Unused if BUTTER_ENABLE_PYTHON=OFF." OFF)
option(BUTTER_APPIMAGE_BUILD "Enable Appimage specific changes. Doesn't cause building of Appimage itself." OFF)
tri_option(BUTTER_ENABLE_KSYNTAXHIGHLIGHTING "Use KSyntaxHighlighting" AUTO)
tri_option(BUTTER_ENABLE_GRAPHVIZ "Enable use of graphviz for graph layout" AUTO)
set(SHIBOKEN_EXTRA_OPTIONS "" CACHE STRING "Extra options for shiboken generator")
set(BUTTER_EXTRA_PLUGIN_DIRS "" CACHE STRING "List of addition plugin locations")
option(BUTTER_ENABLE_DEPENDENCY_DOWNLOADS "Enable downloading of dependencies. Setting to OFF doesn't affect any downloads done by rizin build." OFF)
option(BUTTER_ENABLE_PACKAGING "Enable building platform-specific packages for distributing" OFF)
option(BUTTER_ENABLE_SIGDB "Downloads and installs sigdb (only available when BUTTER_USE_BUNDLED_RIZIN=ON)." OFF)
option(BUTTER_ENABLE_TRANSLATIONS "Build and install translation files" ON)
option(BUTTER_PACKAGE_DEPENDENCIES "During install step include the third party dependencies." OFF)
option(BUTTER_PACKAGE_RZ_GHIDRA "Compile and install rz-ghidra during install step." OFF)
option(BUTTER_PACKAGE_RZ_LIBSWIFT "Compile and install rz-libswift demangler during the install step." OFF)
option(BUTTER_PACKAGE_RZ_LIBYARA "Compile and install rz-libyara during the install step." OFF)
option(BUTTER_PACKAGE_RZ_SILHOUETTE "Compile and install rz-silhouette during the install step." OFF)
option(BUTTER_PACKAGE_RZ_FRIDA "Compile and install rz-frida during the install step." OFF)
option(BUTTER_PACKAGE_JSDEC "Compile and install jsdec during install step." OFF)
set("BUTTER_QT" 6 CACHE STRING "Major QT version to use 5|6")
set_property(CACHE "BUTTER_QT" PROPERTY STRINGS 5 6)
option(BUTTER_INCLUDE_GIT_HASH "Include git hash in full version" ON)
set(BUTTER_VERSION_SUFFIX "" CACHE STRING "Can be used by packagers to differentiate multiple packages using same source, for example build number or presence of additional patches.")

if(NOT BUTTER_ENABLE_PYTHON)
    set(BUTTER_ENABLE_PYTHON_BINDINGS OFF)
endif()

set(BUTTER_VERSION_MAJOR 2)
set(BUTTER_VERSION_MINOR 5)
set(BUTTER_VERSION_PATCH 0)

set(BUTTER_VERSION "${BUTTER_VERSION_MAJOR}.${BUTTER_VERSION_MINOR}.${BUTTER_VERSION_PATCH}")


if (BUTTER_INCLUDE_GIT_HASH)
    execute_process(COMMAND git  -C "${CMAKE_CURRENT_SOURCE_DIR}" --git-dir=.git log --pretty=format:'%h' -n 1
                    OUTPUT_VARIABLE GIT_REV
                    ERROR_QUIET)
endif()

# Check whether we got any revision (which isn't
# always the case, e.g. when someone downloaded a zip file
if (NOT BUTTER_INCLUDE_GIT_HASH OR "${GIT_REV}" STREQUAL "")
    set(BUTTER_VERSION_FULL "${BUTTER_VERSION}${BUTTER_VERSION_SUFFIX}")
else()
    execute_process(
        COMMAND git -C "${CMAKE_CURRENT_SOURCE_DIR}" --git-dir=.git rev-parse --abbrev-ref HEAD
        OUTPUT_VARIABLE GIT_BRANCH)
    string(STRIP "${GIT_REV}" GIT_REV)
    string(SUBSTRING "${GIT_REV}" 1 7 GIT_REV)
    string(STRIP "${GIT_BRANCH}" GIT_BRANCH)
    set(BUTTER_VERSION_FULL "${BUTTER_VERSION}${BUTTER_VERSION_SUFFIX}-${GIT_BRANCH}-${GIT_REV}")
endif()

project(Butter VERSION "${BUTTER_VERSION}")

# Enable solution folder support
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# Put Qt files in a separate folder
set_property(GLOBAL PROPERTY AUTOGEN_SOURCE_GROUP "Generated Files")

set(CMAKE_CXX_STANDARD 20)

include(ButterInstallDirs)

if(BUTTER_USE_BUNDLED_RIZIN)
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
if (BUTTER_QT GREATER_EQUAL 6)
    list(APPEND QT_COMPONENTS Core5Compat SvgWidgets OpenGLWidgets)
endif()
set(QT_PREFIX "Qt${BUTTER_QT}")
find_package(${QT_PREFIX} REQUIRED COMPONENTS ${QT_COMPONENTS})

if(BUTTER_ENABLE_PYTHON)
    find_package (Python3 ${BUTTER_PYTHON_MIN} REQUIRED COMPONENTS Interpreter Development)
    set (PYTHON_EXECUTABLE ${Python3_EXECUTABLE})

    add_definitions(-DBUTTER_ENABLE_PYTHON)

    if(BUTTER_ENABLE_PYTHON_BINDINGS)
        if (BUTTER_QT GREATER_EQUAL 6)
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
        elseif(BUTTER_QT EQUAL 5)
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
            message(FATAL_ERROR "Unsupported QT version ${BUTTER_QT}")
        endif()

        foreach(_dir IN LISTS PYSIDE_INCLUDE_DIRS)
            include_directories(${_dir}
                ${_dir}/QtCore
                ${_dir}/QtGui
                ${_dir}/QtWidgets)
        endforeach()

        add_definitions(-DBUTTER_ENABLE_PYTHON_BINDINGS)
    endif()
endif()

if(BUTTER_ENABLE_KSYNTAXHIGHLIGHTING)
    if(BUTTER_ENABLE_KSYNTAXHIGHLIGHTING STREQUAL AUTO)
        find_package(KF${BUTTER_QT}SyntaxHighlighting)
        if(KF${BUTTER_QT}SyntaxHighlighting_FOUND)
            set(KSYNTAXHIGHLIGHTING_STATUS ON)
        else()
            set(KSYNTAXHIGHLIGHTING_STATUS "OFF (KSyntaxHighlighting not found)")
        endif()
    else()
        find_package(KF${BUTTER_QT}SyntaxHighlighting REQUIRED)
        set(KSYNTAXHIGHLIGHTING_STATUS ON)
    endif()
endif()

if (BUTTER_ENABLE_GRAPHVIZ)
    if (BUTTER_ENABLE_GRAPHVIZ STREQUAL AUTO)
        find_package(Graphviz)
    else()
        find_package(Graphviz REQUIRED)
    endif()
    set (BUTTER_ENABLE_GRAPHVIZ ${Graphviz_FOUND})
endif()

message(STATUS "")
message(STATUS "Building Butter version ${BUTTER_VERSION_FULL}")
message(STATUS "Options:")
message(STATUS "- Bundled rizin: ${BUTTER_USE_BUNDLED_RIZIN}")
if(BUTTER_USE_BUNDLED_RIZIN)
    message(STATUS "- Bundled sigdb: ${BUTTER_ENABLE_SIGDB}")
endif()
message(STATUS "- Python: ${BUTTER_ENABLE_PYTHON}")
message(STATUS "- Python Bindings: ${BUTTER_ENABLE_PYTHON_BINDINGS}")
message(STATUS "- KSyntaxHighlighting: ${KSYNTAXHIGHLIGHTING_STATUS}")
message(STATUS "- Graphviz: ${BUTTER_ENABLE_GRAPHVIZ}")
message(STATUS "- Downloads dependencies: ${BUTTER_ENABLE_DEPENDENCY_DOWNLOADS}")
message(STATUS "- Enable Packaging: ${BUTTER_ENABLE_PACKAGING}")
message(STATUS "- Package Dependencies: ${BUTTER_PACKAGE_DEPENDENCIES}")
message(STATUS "- Package RzGhidra: ${BUTTER_PACKAGE_RZ_GHIDRA}")
message(STATUS "- Package RzLibSwift: ${BUTTER_PACKAGE_RZ_LIBSWIFT}")
message(STATUS "- Package RzLibYara: ${BUTTER_PACKAGE_RZ_LIBYARA}")
message(STATUS "- Package RzSilhouette: ${BUTTER_PACKAGE_RZ_SILHOUETTE}")
message(STATUS "- Package RzFrida: ${BUTTER_PACKAGE_RZ_FRIDA}")
message(STATUS "- Package JSDec: ${BUTTER_PACKAGE_JSDEC}")
message(STATUS "- QT: ${BUTTER_QT}")
message(STATUS "")

if (BUTTER_QT LESS 5 OR BUTTER_QT GREATER 6)
    message(FATAL_ERROR "Unsupported QT major version")
endif()

add_subdirectory(src)

if(BUTTER_ENABLE_PACKAGING)
	add_subdirectory(dist)
endif()
