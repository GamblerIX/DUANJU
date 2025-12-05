cmake_minimum_required(VERSION 3.20)
project(DuanjuGUI VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Find Qt6
find_package(Qt6 REQUIRED COMPONENTS
    Core
    Gui
    Widgets
    Network
    Multimedia
    MultimediaWidgets
    Test
)

# Find libmpv (optional, fallback to Qt Multimedia)
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(MPV QUIET mpv)
endif()

# Find Google Test
find_package(GTest QUIET)
if(NOT GTest_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG v1.14.0
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)
endif()

# Find RapidCheck for property-based testing
FetchContent_Declare(
    rapidcheck
    GIT_REPOSITORY https://github.com/emil-e/rapidcheck.git
    GIT_TAG master
)
FetchContent_MakeAvailable(rapidcheck)

# Source files
set(SOURCES
    src/main.cpp
    src/mainwindow.cpp
    src/api/apiclient.cpp
    src/models/datamodels.cpp
    src/services/searchservice.cpp
    src/services/categoryservice.cpp
    src/services/videoservice.cpp
    src/widgets/searchwidget.cpp
    src/widgets/categorybrowser.cpp
    src/widgets/videoplayer.cpp
    src/widgets/logviewer.cpp
    src/widgets/episodelistdialog.cpp
    src/widgets/settingsdialog.cpp
    src/widgets/errorhandler.cpp
    src/utils/logmanager.cpp
    src/utils/configmanager.cpp
    src/utils/thememanager.cpp
)

set(HEADERS
    include/mainwindow.h
    include/api/apiclient.h
    include/models/datamodels.h
    include/services/searchservice.h
    include/services/categoryservice.h
    include/services/videoservice.h
    include/widgets/searchwidget.h
    include/widgets/categorybrowser.h
    include/widgets/videoplayer.h
    include/widgets/logviewer.h
    include/widgets/episodelistdialog.h
    include/widgets/settingsdialog.h
    include/widgets/errorhandler.h
    include/utils/logmanager.h
    include/utils/configmanager.h
    include/utils/thememanager.h
)

# Resources
set(RESOURCES
    resources/resources.qrc
)

# Main executable
add_executable(${PROJECT_NAME}
    ${SOURCES}
    ${HEADERS}
    ${RESOURCES}
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
    Qt6::Multimedia
    Qt6::MultimediaWidgets
)

# Link libmpv if available
if(MPV_FOUND)
    target_compile_definitions(${PROJECT_NAME} PRIVATE USE_MPV)
    target_include_directories(${PROJECT_NAME} PRIVATE ${MPV_INCLUDE_DIRS})
    target_link_libraries(${PROJECT_NAME} PRIVATE ${MPV_LIBRARIES})
endif()

# Windows specific settings
if(WIN32)
    target_link_libraries(${PROJECT_NAME} PRIVATE dwmapi)
    set_target_properties(${PROJECT_NAME} PROPERTIES
        WIN32_EXECUTABLE TRUE
    )
endif()

# Test executable
enable_testing()

set(TEST_SOURCES
    tests/test_main.cpp
    tests/test_datamodels.cpp
    tests/test_apiclient.cpp
    tests/test_configmanager.cpp
    tests/test_logmanager.cpp
    tests/test_searchvalidation.cpp
    tests/property_tests.cpp
    src/models/datamodels.cpp
    src/utils/configmanager.cpp
    src/utils/logmanager.cpp
    src/api/apiclient.cpp
    src/widgets/searchwidget.cpp
)

add_executable(${PROJECT_NAME}_tests ${TEST_SOURCES})

target_include_directories(${PROJECT_NAME}_tests PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${rapidcheck_SOURCE_DIR}/extras/gtest/include
)

target_link_libraries(${PROJECT_NAME}_tests PRIVATE
    Qt6::Core
    Qt6::Network
    Qt6::Widgets
    Qt6::Test
    GTest::gtest
    GTest::gtest_main
    GTest::gmock
    rapidcheck
    rapidcheck_gtest
)

include(GoogleTest)
gtest_discover_tests(${PROJECT_NAME}_tests)

# Install rules
install(TARGETS ${PROJECT_NAME}
    RUNTIME DESTINATION bin
)
