cmake_minimum_required(VERSION 3.12)
project(butter-sample-plugin)

set(CMAKE_CXX_STANDARD 20)

find_package(Butter REQUIRED)
find_package(Rizin REQUIRED)
set(CUTTER_INSTALL_PLUGDIR "${Butter_USER_PLUGINDIR}" CACHE STRING "Directory to install Butter plugin into")

set(CMAKE_AUTOMOC ON)

add_library(sample_plugin MODULE
    ButterSamplePlugin.h
    ButterSamplePlugin.cpp)
target_link_libraries(sample_plugin PRIVATE Butter::Butter Rizin::Core)
install(TARGETS sample_plugin DESTINATION "${CUTTER_INSTALL_PLUGDIR}")
