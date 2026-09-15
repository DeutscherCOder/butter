cmake_minimum_required(VERSION 3.12)
project(clutter-sample-plugin)

set(CMAKE_CXX_STANDARD 20)

find_package(Clutter REQUIRED)
find_package(Rizin REQUIRED)
set(CUTTER_INSTALL_PLUGDIR "${Clutter_USER_PLUGINDIR}" CACHE STRING "Directory to install Clutter plugin into")

set(CMAKE_AUTOMOC ON)

add_library(sample_plugin MODULE
    ClutterSamplePlugin.h
    ClutterSamplePlugin.cpp)
target_link_libraries(sample_plugin PRIVATE Clutter::Clutter Rizin::Core)
install(TARGETS sample_plugin DESTINATION "${CUTTER_INSTALL_PLUGDIR}")
