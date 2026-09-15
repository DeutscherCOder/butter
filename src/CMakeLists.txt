configure_file("${CMAKE_CURRENT_SOURCE_DIR}/ButterConfig.h.in"
               "${CMAKE_CURRENT_BINARY_DIR}/ButterConfig.h")

set(SOURCES
    Main.cpp
    core/Butter.cpp
    core/ButterJson.cpp
    core/RizinCpp.cpp
    core/Basefind.cpp
    dialogs/EditStringDialog.cpp
    dialogs/WriteCommandsDialogs.cpp
    widgets/DisassemblerGraphView.cpp
    widgets/OverviewView.cpp
    common/DisassemblyPreview.cpp
    common/RichTextPainter.cpp
    dialogs/InitialOptionsDialog.cpp
    dialogs/AboutDialog.cpp
    dialogs/CommentsDialog.cpp
    dialogs/EditInstructionDialog.cpp
    dialogs/FlagDialog.cpp
    dialogs/GlobalVariableDialog.cpp
    dialogs/RemoteDebugDialog.cpp
    dialogs/NativeDebugDialog.cpp
    dialogs/XrefsDialog.cpp
    core/MainWindow.cpp
    common/Helpers.cpp
    common/MdHighlighter.cpp
    common/DirectionalComboBox.cpp
    dialogs/preferences/AsmOptionsWidget.cpp
    dialogs/NewFileDialog.cpp
    common/AnalysisTask.cpp
    widgets/CommentsWidget.cpp
    widgets/ConsoleWidget.cpp
    widgets/Dashboard.cpp
    widgets/EntrypointWidget.cpp
    widgets/ExportsWidget.cpp
    widgets/FlagsWidget.cpp
    widgets/FunctionsWidget.cpp
    widgets/GlobalsWidget.cpp
    widgets/ImportsWidget.cpp
    widgets/Omnibar.cpp
    widgets/RelocsWidget.cpp
    widgets/SectionsWidget.cpp
    widgets/SegmentsWidget.cpp
    widgets/StringsWidget.cpp
    widgets/SymbolsWidget.cpp
    menus/DisassemblyContextMenu.cpp
    menus/DecompilerContextMenu.cpp
    menus/FlirtContextMenu.cpp
    widgets/DisassemblyWidget.cpp
    widgets/HexdumpWidget.cpp
    common/Configuration.cpp
    common/Colors.cpp
    common/TempConfig.cpp
    common/PjHandle.cpp
    common/SvgIconEngine.cpp
    common/SyntaxHighlighter.cpp
    widgets/DecompilerWidget.cpp
    widgets/VisualNavbar.cpp
    widgets/GraphView.cpp
    dialogs/preferences/PreferencesDialog.cpp
    dialogs/preferences/AppearanceOptionsWidget.cpp
    dialogs/preferences/GraphOptionsWidget.cpp
    dialogs/preferences/PreferenceCategory.cpp
    dialogs/preferences/InitializationFileEditor.cpp
    widgets/QuickFilterView.cpp
    widgets/ClassesWidget.cpp
    widgets/ResourcesWidget.cpp
    widgets/VTablesWidget.cpp
    widgets/TypesWidget.cpp
    widgets/HeadersWidget.cpp
    widgets/SearchWidget.cpp
    ButterApplication.cpp
    dialogs/RizinPluginsDialog.cpp
    widgets/ButterDockWidget.cpp
    widgets/GraphWidget.cpp
    widgets/OverviewWidget.cpp
    dialogs/VersionInfoDialog.cpp
    widgets/FlirtWidget.cpp
    common/AsyncTask.cpp
    dialogs/AsyncTaskDialog.cpp
    widgets/StackWidget.cpp
    widgets/RegistersWidget.cpp
    widgets/ThreadsWidget.cpp
    widgets/ProcessesWidget.cpp
    widgets/BacktraceWidget.cpp
    dialogs/MapFileDialog.cpp
    common/CommandTask.cpp
    widgets/ProgressIndicator.cpp
    common/RizinTask.cpp
    dialogs/RizinTaskDialog.cpp
    widgets/DebugActions.cpp
    widgets/MemoryMapWidget.cpp
    dialogs/preferences/DebugOptionsWidget.cpp
    dialogs/preferences/PluginsOptionsWidget.cpp
    widgets/BreakpointWidget.cpp
    dialogs/BreakpointsDialog.cpp
    dialogs/AttachProcDialog.cpp
    widgets/RegisterRefsWidget.cpp
    dialogs/SetToDataDialog.cpp
    dialogs/EditVariablesDialog.cpp
    dialogs/EditFunctionDialog.cpp
    widgets/ButterTreeView.cpp
    widgets/ComboQuickFilterView.cpp
    dialogs/HexdumpRangeDialog.cpp
    common/ButterSeekable.cpp
    common/RefreshDeferrer.cpp
    dialogs/WelcomeDialog.cpp
    common/RunScriptTask.cpp
    dialogs/EditMethodDialog.cpp
    dialogs/TypesInteractionDialog.cpp
    dialogs/TypesVariablesDialog.cpp
    widgets/SdbWidget.cpp
    plugins/PluginManager.cpp
    common/BasicBlockHighlighter.cpp
    common/BasicInstructionHighlighter.cpp
    widgets/ColorPicker.cpp
    common/ColorThemeWorker.cpp
    widgets/ColorThemeComboBox.cpp
    widgets/ColorThemeListView.cpp
    dialogs/preferences/ColorThemeEditDialog.cpp
    common/UpdateWorker.cpp
    widgets/MemoryDockWidget.cpp
    common/BugReporting.cpp
    common/HighDpiPixmap.cpp
    widgets/GraphGridLayout.cpp
    widgets/HexWidget.cpp
    common/SelectionHighlight.cpp
    common/Decompiler.cpp
    menus/AddressableItemContextMenu.cpp
    common/AddressableItemModel.cpp
    widgets/ListDockWidget.cpp
    dialogs/MultitypeFileSaveDialog.cpp
    widgets/BoolToggleDelegate.cpp
    common/IOModesController.cpp
    common/SettingsUpgrade.cpp
    dialogs/LayoutManager.cpp
    common/ButterLayout.cpp
    widgets/GraphHorizontalAdapter.cpp
    common/ResourcePaths.cpp
    widgets/ButterGraphView.cpp
    widgets/SimpleTextGraphView.cpp
    widgets/RizinGraphWidget.cpp
    widgets/CallGraph.cpp
    widgets/AddressableDockWidget.cpp
    dialogs/preferences/AnalysisOptionsWidget.cpp
    common/DecompilerHighlighter.cpp
    dialogs/GlibcHeapInfoDialog.cpp
    widgets/HeapDockWidget.cpp
    widgets/GlibcHeapWidget.cpp
    dialogs/GlibcHeapBinsDialog.cpp
    widgets/HeapBinsGraphView.cpp
    dialogs/ArenaInfoDialog.cpp
    tools/basefind/BaseFindDialog.cpp
    tools/basefind/BaseFindSearchDialog.cpp
    tools/basefind/BaseFindResultsDialog.cpp
    widgets/AddressRangeScrollBar.cpp
    dialogs/preferences/ShortcutOptionsWidget.cpp
    shortcuts/ShortcutManager.cpp
    shortcuts/DefaultShortcuts.cpp
    dialogs/MarkDialog.cpp
    dialogs/ProfileDirectivesDialog.cpp
    dialogs/RegisterProfileDialog.cpp
    dialogs/EditRegProfileDialog.cpp
    common/DisassemblyHelper.cpp
    widgets/SearchBarWidget.cpp
    widgets/SearchableDockWidget.cpp
    common/ButterSearchable.cpp
    widgets/SearchableTextEdit.cpp
    dialogs/preferences/SymbolsOptionsWidget.cpp
    widgets/ItemCountLineEdit.cpp
    widgets/AbstractFilterView.cpp
    dialogs/preferences/InterfaceOptionsWidget.cpp
    common/Json.cpp
    dialogs/preferences/RizinConfigOptionsWidget.cpp
    dialogs/IntervalDialog.cpp
    dialogs/StringListDialog.cpp
)
set(HEADER_FILES
    core/Butter.h
    core/ButterCommon.h
    core/ButterDescriptions.h
    core/ButterJson.h
    core/RizinCpp.h
    core/Basefind.h
    dialogs/EditStringDialog.h
    dialogs/WriteCommandsDialogs.h
    widgets/DisassemblerGraphView.h
    widgets/OverviewView.h
    common/RichTextPainter.h
    common/CachedFontMetrics.h
    common/Metrics.h
    dialogs/AboutDialog.h
    dialogs/preferences/AsmOptionsWidget.h
    dialogs/CommentsDialog.h
    dialogs/EditInstructionDialog.h
    dialogs/FlagDialog.h
    dialogs/GlobalVariableDialog.h
    dialogs/RemoteDebugDialog.h
    dialogs/NativeDebugDialog.h
    dialogs/XrefsDialog.h
    common/Helpers.h
    core/MainWindow.h
    common/MdHighlighter.h
    common/DirectionalComboBox.h
    dialogs/InitialOptionsDialog.h
    dialogs/NewFileDialog.h
    common/AnalysisTask.h
    widgets/CommentsWidget.h
    widgets/ConsoleWidget.h
    widgets/Dashboard.h
    widgets/EntrypointWidget.h
    widgets/ExportsWidget.h
    widgets/FlagsWidget.h
    widgets/FunctionsWidget.h
    widgets/ImportsWidget.h
    widgets/Omnibar.h
    widgets/RelocsWidget.h
    widgets/SectionsWidget.h
    widgets/SegmentsWidget.h
    widgets/StringsWidget.h
    widgets/SymbolsWidget.h
    menus/DisassemblyContextMenu.h
    menus/DecompilerContextMenu.h
    menus/FlirtContextMenu.h
    widgets/DisassemblyWidget.h
    widgets/HexdumpWidget.h
    common/Configuration.h
    common/Colors.h
    common/TempConfig.h
    common/PjHandle.h
    common/SvgIconEngine.h
    common/SyntaxHighlighter.h
    widgets/DecompilerWidget.h
    widgets/VisualNavbar.h
    widgets/GraphView.h
    dialogs/preferences/PreferencesDialog.h
    dialogs/preferences/AppearanceOptionsWidget.h
    dialogs/preferences/PreferenceCategory.h
    dialogs/preferences/GraphOptionsWidget.h
    dialogs/preferences/InitializationFileEditor.h
    widgets/QuickFilterView.h
    widgets/ClassesWidget.h
    widgets/ResourcesWidget.h
    ButterApplication.h
    widgets/VTablesWidget.h
    widgets/TypesWidget.h
    widgets/HeadersWidget.h
    widgets/SearchWidget.h
    dialogs/RizinPluginsDialog.h
    widgets/ButterDockWidget.h
    widgets/GraphWidget.h
    widgets/OverviewWidget.h
    dialogs/VersionInfoDialog.h
    widgets/FlirtWidget.h
    common/AsyncTask.h
    dialogs/AsyncTaskDialog.h
    widgets/StackWidget.h
    widgets/RegistersWidget.h
    widgets/ThreadsWidget.h
    widgets/ProcessesWidget.h
    widgets/BacktraceWidget.h
    dialogs/MapFileDialog.h
    common/StringsTask.h
    common/FunctionsTask.h
    common/CommandTask.h
    widgets/ProgressIndicator.h
    plugins/ButterPlugin.h
    common/RizinTask.h
    dialogs/RizinTaskDialog.h
    widgets/DebugActions.h
    widgets/MemoryMapWidget.h
    dialogs/preferences/DebugOptionsWidget.h
    dialogs/preferences/PluginsOptionsWidget.h
    widgets/BreakpointWidget.h
    dialogs/BreakpointsDialog.h
    dialogs/AttachProcDialog.h
    widgets/RegisterRefsWidget.h
    dialogs/SetToDataDialog.h
    common/InitialOptions.h
    dialogs/EditVariablesDialog.h
    dialogs/EditFunctionDialog.h
    widgets/ButterTreeView.h
    widgets/ComboQuickFilterView.h
    dialogs/HexdumpRangeDialog.h
    common/ButterSeekable.h
    common/RefreshDeferrer.h
    dialogs/WelcomeDialog.h
    common/RunScriptTask.h
    common/Json.h
    dialogs/EditMethodDialog.h
    dialogs/TypesInteractionDialog.h
    dialogs/TypesVariablesDialog.h
    widgets/SdbWidget.h
    plugins/PluginManager.h
    common/BasicBlockHighlighter.h
    common/BasicInstructionHighlighter.h
    common/UpdateWorker.h
    widgets/ColorPicker.h
    common/ColorThemeWorker.h
    widgets/ColorThemeComboBox.h
    widgets/MemoryDockWidget.h
    widgets/ColorThemeListView.h
    dialogs/preferences/ColorThemeEditDialog.h
    common/BugReporting.h
    common/HighDpiPixmap.h
    widgets/GraphLayout.h
    widgets/GraphGridLayout.h
    widgets/HexWidget.h
    common/SelectionHighlight.h
    common/Decompiler.h
    menus/AddressableItemContextMenu.h
    common/AddressableItemModel.h
    widgets/ListDockWidget.h
    widgets/AddressableItemList.h
    dialogs/MultitypeFileSaveDialog.h
    widgets/BoolToggleDelegate.h
    common/IOModesController.h
    common/SettingsUpgrade.h
    dialogs/LayoutManager.h
    common/ButterLayout.h
    common/BinaryTrees.h
    common/LinkedListPool.h
    widgets/GraphHorizontalAdapter.h
    common/ResourcePaths.h
    widgets/ButterGraphView.h
    widgets/SimpleTextGraphView.h
    widgets/RizinGraphWidget.h
    widgets/CallGraph.h
    widgets/AddressableDockWidget.h
    dialogs/preferences/AnalysisOptionsWidget.h
    common/DecompilerHighlighter.h
    dialogs/GlibcHeapInfoDialog.h
    widgets/HeapDockWidget.h
    widgets/GlibcHeapWidget.h
    dialogs/GlibcHeapBinsDialog.h
    widgets/HeapBinsGraphView.h
    dialogs/ArenaInfoDialog.h
    tools/basefind/BaseFindDialog.h
    tools/basefind/BaseFindSearchDialog.h
    tools/basefind/BaseFindResultsDialog.h
    widgets/AddressRangeScrollBar.h
    dialogs/preferences/ShortcutOptionsWidget.h
    shortcuts/ShortcutManager.h
    shortcuts/DefaultShortcuts.h
    dialogs/MarkDialog.h
    dialogs/ProfileDirectivesDialog.h
    dialogs/RegisterProfileDialog.h
    dialogs/EditRegProfileDialog.h
    common/DisassemblyHelper.h
    widgets/SearchBarWidget.h
    widgets/SearchableDockWidget.h
    common/ButterSearchable.h
    widgets/SearchableTextEdit.h
    dialogs/preferences/SymbolsOptionsWidget.h
    widgets/ItemCountLineEdit.h
    widgets/AbstractFilterView.h
    dialogs/preferences/InterfaceOptionsWidget.h
    dialogs/preferences/RizinConfigOptionsWidget.h
    dialogs/IntervalDialog.h
    dialogs/StringListDialog.h
)
set(UI_FILES
    dialogs/AboutDialog.ui
    dialogs/EditStringDialog.ui
    dialogs/Base64EnDecodedWriteDialog.ui
    dialogs/DuplicateFromOffsetDialog.ui
    dialogs/IncrementDecrementDialog.ui
    dialogs/preferences/AsmOptionsWidget.ui
    dialogs/CommentsDialog.ui
    dialogs/EditInstructionDialog.ui
    dialogs/FlagDialog.ui
    dialogs/GlobalVariableDialog.ui
    dialogs/RemoteDebugDialog.ui
    dialogs/NativeDebugDialog.ui
    dialogs/XrefsDialog.ui
    dialogs/NewFileDialog.ui
    dialogs/InitialOptionsDialog.ui
    dialogs/EditFunctionDialog.ui
    core/MainWindow.ui
    widgets/ConsoleWidget.ui
    widgets/Dashboard.ui
    widgets/EntrypointWidget.ui
    widgets/FlagsWidget.ui
    widgets/GlobalsWidget.ui
    widgets/StringsWidget.ui
    widgets/HexdumpWidget.ui
    dialogs/preferences/PreferencesDialog.ui
    dialogs/preferences/AppearanceOptionsWidget.ui
    dialogs/preferences/GraphOptionsWidget.ui
    dialogs/preferences/InitializationFileEditor.ui
    widgets/QuickFilterView.ui
    widgets/DecompilerWidget.ui
    widgets/VTablesWidget.ui
    widgets/TypesWidget.ui
    widgets/SearchWidget.ui
    dialogs/RizinPluginsDialog.ui
    dialogs/VersionInfoDialog.ui
    widgets/FlirtWidget.ui
    dialogs/AsyncTaskDialog.ui
    dialogs/RizinTaskDialog.ui
    widgets/StackWidget.ui
    widgets/RegistersWidget.ui
    widgets/ThreadsWidget.ui
    widgets/ProcessesWidget.ui
    widgets/BacktraceWidget.ui
    dialogs/MapFileDialog.ui
    dialogs/preferences/DebugOptionsWidget.ui
    widgets/BreakpointWidget.ui
    dialogs/BreakpointsDialog.ui
    dialogs/AttachProcDialog.ui
    widgets/RegisterRefsWidget.ui
    dialogs/SetToDataDialog.ui
    dialogs/EditVariablesDialog.ui
    widgets/ButterTreeView.ui
    widgets/ComboQuickFilterView.ui
    dialogs/HexdumpRangeDialog.ui
    dialogs/WelcomeDialog.ui
    dialogs/EditMethodDialog.ui
    dialogs/TypesInteractionDialog.ui
    dialogs/TypesVariablesDialog.ui
    widgets/SdbWidget.ui
    widgets/ColorPicker.ui
    dialogs/preferences/ColorThemeEditDialog.ui
    widgets/ListDockWidget.ui
    dialogs/LayoutManager.ui
    widgets/RizinGraphWidget.ui
    dialogs/preferences/AnalysisOptionsWidget.ui
    dialogs/GlibcHeapInfoDialog.ui
    widgets/HeapDockWidget.ui
    widgets/GlibcHeapWidget.ui
    dialogs/GlibcHeapBinsDialog.ui
    dialogs/ArenaInfoDialog.ui
    tools/basefind/BaseFindDialog.ui
    tools/basefind/BaseFindSearchDialog.ui
    tools/basefind/BaseFindResultsDialog.ui
    dialogs/preferences/ShortcutOptionsWidget.ui
    dialogs/MarkDialog.ui
    dialogs/ProfileDirectivesDialog.ui
    dialogs/RegisterProfileDialog.ui
    dialogs/EditRegProfileDialog.ui
    widgets/SearchBarWidget.ui
    dialogs/preferences/SymbolsOptionsWidget.ui
    dialogs/preferences/InterfaceOptionsWidget.ui
    dialogs/preferences/RizinConfigOptionsWidget.ui
)
set(QRC_FILES
    resources.qrc
    themes/native/native.qrc
    themes/qdarkstyle/dark.qrc
    themes/midnight/midnight.qrc
    themes/lightstyle/light.qrc
)

set(BUTTER_INCLUDE_DIRECTORIES core widgets common plugins menus .)

if (BUTTER_ENABLE_PYTHON)
    list(APPEND SOURCES common/QtResImporter.cpp common/PythonManager.cpp common/PythonAPI.cpp)
    list(APPEND HEADER_FILES common/QtResImporter.h common/PythonManager.h common/PythonAPI.h)
endif()

if(BUTTER_ENABLE_PYTHON_BINDINGS)
    if (BUTTER_QT EQUAL 6)
        set(PYSIDE_NAME PySide6)
        set(SHIBOKEN_COMMAND Shiboken6::shiboken6)
        set (BUTTER_PYSIDE_LIBS Shiboken6::libshiboken PySide6::pyside6)
    elseif(BUTTER_QT EQUAL 5)
        set(PYSIDE_NAME PySide2)
        set(SHIBOKEN_COMMAND Shiboken2::shiboken2)
        set (BUTTER_PYSIDE_LIBS Shiboken2::libshiboken PySide2::pyside2)
    endif()

    set(BINDINGS_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/bindings")
    set(BINDINGS_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/bindings")

    configure_file("${BINDINGS_SRC_DIR}/bindings.xml.in" "${BINDINGS_BUILD_DIR}/bindings.xml")

    execute_process(COMMAND "${PYTHON_EXECUTABLE}" "${BINDINGS_SRC_DIR}/src_list.py" cmake "${BINDINGS_BUILD_DIR}" OUTPUT_VARIABLE BINDINGS_SOURCE)

    set_property(SOURCE ${BINDINGS_SOURCE} PROPERTY SKIP_AUTOGEN ON)

    include_directories("${BINDINGS_BUILD_DIR}/ButterBindings")

    set(SHIBOKEN_OPTIONS)
    if (WIN32)
        list(APPEND SHIBOKEN_OPTIONS --avoid-protected-hack)
    endif()

    add_custom_command(OUTPUT ${BINDINGS_SOURCE}
            COMMAND "${SHIBOKEN_COMMAND}" --project-file="${BINDINGS_BUILD_DIR}/bindings.txt" ${SHIBOKEN_OPTIONS} ${SHIBOKEN_EXTRA_OPTIONS}
            DEPENDS "${BINDINGS_BUILD_DIR}/bindings.xml" "${BINDINGS_BUILD_DIR}/bindings.txt"
            IMPLICIT_DEPENDS CXX "${CMAKE_CURRENT_SOURCE_DIR}/bindings/bindings.h"
            COMMENT "Generating Python bindings with ${SHIBOKEN_COMMAND}")
else()
    set(BINDINGS_SOURCE "")
endif()


if (TARGET Graphviz::GVC)
    list(APPEND SOURCES widgets/GraphvizLayout.cpp)
    list(APPEND HEADER_FILES widgets/GraphvizLayout.h)
endif()

if (WIN32)
    set(PLATFORM_RESOURCES "img/butter.rc")
    set(OPTIONS WIN32)
else()
    set(PLATFORM_RESOURCES "")
endif()

if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU"
        OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    add_definitions(-Wall -Wextra)
    set_source_files_properties(${BINDINGS_SOURCE} PROPERTIES COMPILE_FLAGS -w)
endif()

# Make a source group for Visual Studio
set(BUTTER_SOURCES ${OPTIONS} ${UI_FILES} ${QRC_FILES} ${PLATFORM_RESOURCES} ${SOURCES} ${HEADER_FILES})
source_group(TREE "${CMAKE_CURRENT_LIST_DIR}" FILES ${BUTTER_SOURCES})

add_executable(Butter ${BUTTER_SOURCES} ${BINDINGS_SOURCE})
set_target_properties(Butter PROPERTIES
        OUTPUT_NAME butter
        RUNTIME_OUTPUT_DIRECTORY ..
        PDB_OUTPUT_DIRECTORY ..
        ENABLE_EXPORTS ON
        CXX_VISIBILITY_PRESET hidden)
target_compile_definitions(Butter PRIVATE BUTTER_SOURCE_BUILD)

# Set Butter as the startup project in Visual Studio
set_property(DIRECTORY ${PROJECT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT Butter)

foreach(_dir ${BUTTER_INCLUDE_DIRECTORIES})
    target_include_directories(Butter PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/${_dir}>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/butter/${_dir}>
    )
endforeach()

if (TARGET Graphviz::GVC)
    target_link_libraries(Butter PRIVATE Graphviz::GVC)
    target_compile_definitions(Butter PRIVATE BUTTER_ENABLE_GRAPHVIZ)
endif()

target_link_libraries(Butter PUBLIC ${QT_PREFIX}::Core ${QT_PREFIX}::Widgets ${QT_PREFIX}::Gui PRIVATE  ${QT_PREFIX}::Svg ${QT_PREFIX}::Network)
if (BUTTER_QT EQUAL 6)
    target_link_libraries(Butter PUBLIC Qt6::Core5Compat Qt6::SvgWidgets)
    target_link_libraries(Butter PRIVATE Qt6::OpenGLWidgets)
endif()

target_link_libraries(Butter PUBLIC ${RIZIN_TARGET})
if(BUTTER_ENABLE_PYTHON)
    target_link_libraries(Butter PRIVATE Python3::Python)

    if(BUTTER_ENABLE_PYTHON_BINDINGS)
        target_link_libraries(Butter PRIVATE ${BUTTER_PYSIDE_LIBS})

        get_target_property(RAW_BINDINGS_INCLUDE_DIRS Butter INCLUDE_DIRECTORIES)
        if(NOT BUTTER_USE_BUNDLED_RIZIN)
            get_target_property(RAW_RIZIN_INCLUDE_DIRS ${RIZIN_TARGET} INTERFACE_INCLUDE_DIRECTORIES)
            list(APPEND RAW_BINDINGS_INCLUDE_DIRS "${RAW_RIZIN_INCLUDE_DIRS}")
        endif()
        set(BINDINGS_INCLUDE_DIRS "")
        foreach(_dir ${RAW_BINDINGS_INCLUDE_DIRS})
            string(REGEX REPLACE "\\$<BUILD_INTERFACE:(.*)>" "\\1" _dir ${_dir})
            string(REGEX REPLACE "\\$<INSTALL_INTERFACE:(.*)>" "" _dir ${_dir})
            if (NOT "${_dir}" STREQUAL "")
                list(APPEND BINDINGS_INCLUDE_DIRS "${_dir}")
            endif()
        endforeach()

        set(BINDINGS_INCLUDE_DIR_LINES "")
        if(APPLE)
            if (_qt5Core_install_prefix)
                list(APPEND BINDINGS_INCLUDE_DIRS "${_qt5Core_install_prefix}/include")
                list(APPEND BINDINGS_INCLUDE_DIRS "${_qt5Core_install_prefix}/include/QtCore")
                list(APPEND BINDINGS_INCLUDE_DIRS "${_qt5Core_install_prefix}/include/QtGui")
                list(APPEND BINDINGS_INCLUDE_DIRS "${_qt5Core_install_prefix}/include/QtWidgets")
            elseif(BUTTER_QT EQUAL 6)
                string(APPEND BINDINGS_INCLUDE_DIR_LINES "framework-include-path=${QT6_INSTALL_PREFIX}/${QT6_INSTALL_LIBS}\n")
            endif()
        endif()
        list(APPEND BINDINGS_INCLUDE_DIRS ${${QT_PREFIX}Core_INCLUDE_DIRS} ${${QT_PREFIX}Widgets_INCLUDE_DIRS} ${${QT_PREFIX}Gui_INCLUDE_DIRS})
        list(APPEND BINDINGS_INCLUDE_DIRS ${Rizin_INCLUDE_DIRS})
        list(APPEND BINDINGS_INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}")

        foreach(_dir ${BINDINGS_INCLUDE_DIRS})
            if (NOT "${_dir}" STREQUAL "")
                string(APPEND BINDINGS_INCLUDE_DIR_LINES "include-path = ${_dir}\n")
            endif()
        endforeach()

        configure_file("${BINDINGS_SRC_DIR}/bindings.txt.in" "${BINDINGS_BUILD_DIR}/bindings.txt")
        add_definitions(-DWIN32_LEAN_AND_MEAN)
    endif()
endif()

if(TARGET KF${BUTTER_QT}::SyntaxHighlighting)
    target_link_libraries(Butter PRIVATE KF${BUTTER_QT}::SyntaxHighlighting)
    target_compile_definitions(Butter PRIVATE BUTTER_ENABLE_KSYNTAXHIGHLIGHTING)
endif()

if (BUTTER_APPIMAGE_BUILD)
    target_compile_definitions(Butter PRIVATE APPIMAGE)
endif()

if (BUTTER_PACKAGE_JSDEC)
	target_compile_definitions(Butter PRIVATE BUTTER_BUNDLE_JSDEC)
endif()

if(APPLE AND BUTTER_ENABLE_PACKAGING AND BUTTER_USE_BUNDLED_RIZIN)
	target_compile_definitions(Butter PRIVATE MACOS_RZ_BUNDLED)
endif()

if(BUTTER_ENABLE_PACKAGING)
    target_compile_definitions(Butter PRIVATE BUTTER_ENABLE_PACKAGING)
endif()

if(BUTTER_ENABLE_TRANSLATIONS)
    include(Translations)
endif()

# Install files
install(TARGETS Butter
        EXPORT ButterTargets
        RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
        BUNDLE DESTINATION "." # needs to be tested
        ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}" COMPONENT Devel)
install(EXPORT ButterTargets
    NAMESPACE Butter::
    DESTINATION "${BUTTER_INSTALL_CONFIGDIR}"
    COMPONENT Devel)
include(CMakePackageConfigHelpers)
configure_package_config_file(${CMAKE_CURRENT_SOURCE_DIR}/../cmake/ButterConfig.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/ButterConfig.cmake"
    INSTALL_DESTINATION "${BUTTER_INSTALL_CONFIGDIR}"
    NO_SET_AND_CHECK_MACRO
    NO_CHECK_REQUIRED_COMPONENTS_MACRO)
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/ButterConfigVersion.cmake"
    VERSION "${BUTTER_VERSION_FULL}"
    COMPATIBILITY AnyNewerVersion)
install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/ButterConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/ButterConfigVersion.cmake"
    DESTINATION ${BUTTER_INSTALL_CONFIGDIR}
    COMPONENT Devel)
foreach(_file ${HEADER_FILES})
    # Can't use target PUBLIC_HEADER option for installing due to multiple directories
    get_filename_component(_header_dir "${_file}" DIRECTORY)
    install (FILES "${_file}" DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/butter/${_header_dir}" COMPONENT Devel)
endforeach()

# ---------------------------------------------------------------------------
# Compatibility facade for out-of-tree plugins written against upstream Butter.
#
# Plugin sources and their CMakeLists live outside this repository, so the pre-
# rebrand names stay resolvable: a Butter*.h is installed next to every
# Butter*.h, `include <Butter.h>` pulls in the aliases from ButterCompat.h, and
# a forwarding CMake package keeps find_package(Butter) / Butter::Butter
# working. Only names are aliased - the types, the ABI and the Qt interface IID
# are the Butter ones. See the "Rebrand and compatibility" section of README.md.
# ---------------------------------------------------------------------------
set(COMPAT_DIR "${CMAKE_CURRENT_BINARY_DIR}/compat")
file(MAKE_DIRECTORY "${COMPAT_DIR}")
foreach(_file ${HEADER_FILES})
    get_filename_component(_name "${_file}" NAME)
    get_filename_component(_dir "${_file}" DIRECTORY)
    if(_name MATCHES "^Butter")
        string(REPLACE "Butter" "Butter" _compat_name "${_name}")
        string(TOUPPER "${_compat_name}" _compat_guard)
        string(REGEX REPLACE "[^A-Z0-9_]" "_" _compat_guard "${_compat_guard}")
        # Hand-written shims (ButterCompat.h lives alongside them) take precedence.
        if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/compat/${_dir}/${_compat_name}")
            set(_compat_file "${CMAKE_CURRENT_SOURCE_DIR}/compat/${_dir}/${_compat_name}")
        else()
            file(MAKE_DIRECTORY "${COMPAT_DIR}/${_dir}")
            set(_compat_file "${COMPAT_DIR}/${_dir}/${_compat_name}")
            file(WRITE "${_compat_file}"
"// Generated compatibility shim for plugins written against upstream Butter.\n"
"// The real header is Butter, this just makes the old include path resolve.\n"
"#ifndef ${_compat_guard}\n"
"#define ${_compat_guard}\n\n"
"#include \"${_name}\"\n"
"#include <ButterCompat.h>\n\n"
"#endif // ${_compat_guard}\n")
        endif()
        install(FILES "${_compat_file}"
                DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/butter/${_dir}" COMPONENT Devel)
        list(APPEND COMPAT_SHIM_DESTS "${CMAKE_INSTALL_INCLUDEDIR}/butter/${_dir}/${_compat_name}")
    endif()
endforeach()

# Everything else under src/compat (ButterCompat.h and any future shim) is
# installed verbatim, skipping what the loop above already placed.
file(GLOB_RECURSE COMPAT_SOURCES RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/compat"
     "${CMAKE_CURRENT_SOURCE_DIR}/compat/*.h")
foreach(_file ${COMPAT_SOURCES})
    get_filename_component(_dir "${_file}" DIRECTORY)
    if(NOT "${CMAKE_INSTALL_INCLUDEDIR}/butter/${_file}" IN_LIST COMPAT_SHIM_DESTS)
        install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/compat/${_file}"
                DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/butter/${_dir}" COMPONENT Devel)
    endif()
endforeach()

install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/../cmake/ButterCompat.cmake"
        DESTINATION "${BUTTER_COMPAT_CMAKE_CONFIGDIR}" RENAME ButterConfig.cmake
        COMPONENT Devel)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/ButterConfigVersion.cmake"
        DESTINATION "${BUTTER_COMPAT_CMAKE_CONFIGDIR}" RENAME ButterConfigVersion.cmake
        COMPONENT Devel)

if(UNIX AND NOT APPLE)
    install(FILES "img/butter.svg"
        DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/icons/hicolor/scalable/apps")
    install(FILES "re.rizin.butter.desktop"
        DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/applications")
    install(FILES "re.rizin.butter.appdata.xml"
        DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/metainfo")
endif()
