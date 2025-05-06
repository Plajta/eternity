cmake_minimum_required(VERSION 3.13)

set(ETERNITY_DEVICE_NAME "Eternity_bootloader" CACHE STRING "The device name used for info and USB descriptor")
string(REPLACE " " "_" DEVICE_NAME "${DEVICE_NAME}") # Remove potential spaces

if(NOT DEFINED GIT_COMMIT_SHA OR GIT_COMMIT_SHA STREQUAL "")
    execute_process(
    COMMAND git rev-parse --short HEAD
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    OUTPUT_VARIABLE GIT_COMMIT_SHA
    OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Check for uncommitted changes by looking at the output of git diff
    execute_process(
    COMMAND git diff --quiet
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE GIT_DIFF_RESULT
    )

    # If there are uncommitted changes, append -dirty to the commit SHA
    if(NOT GIT_DIFF_RESULT EQUAL 0)
        set(GIT_COMMIT_SHA "${GIT_COMMIT_SHA}-dirty")
    endif()
endif()

# Get the current build date and time
execute_process(
  COMMAND date "+%Y-%m-%d,%H:%M:%S"
  OUTPUT_VARIABLE BUILD_DATE
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

# initialize pico-sdk from GIT
# (note this can come from environment, CMake cache etc)
set(PICO_SDK_FETCH_FROM_GIT on)

# pico_sdk_import.cmake is a single file copied from this SDK
# note: this must happen before project()
include(pico_sdk_import.cmake)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON) # Required for clangd
set(ETERNITY_SIZE_BYTES_STRING "(32 * 1024)" CACHE INTERNAL "Size of Eternity bootloader in bytes eg. 64 * 1024 = 64kB")

# Convert string to integer
math(EXPR ETERNITY_SIZE_BYTES "${ETERNITY_SIZE_BYTES_STRING}")

project(eternity)

# initialize the Raspberry Pi Pico SDK
pico_sdk_init()

add_executable(${PROJECT_NAME}
    main.c
    usb/usb_descriptors.c
    protocol/protocol.c
)

target_compile_definitions(${PROJECT_NAME} PRIVATE
  GIT_COMMIT_SHA="${GIT_COMMIT_SHA}"
  ETERNITY_SIZE_BYTES=${ETERNITY_SIZE_BYTES}
  PROJECT_NAME="${PROJECT_NAME}"
  BUILD_DATE="${BUILD_DATE}"
  ETERNITY_DEVICE_NAME="${ETERNITY_DEVICE_NAME}"
)

# Add pico_stdlib library which aggregates commonly used features
target_link_libraries(${PROJECT_NAME} pico_stdlib pico_bootrom hardware_flash hardware_sync hardware_structs hardware_resets tinyusb_device tinyusb_board)

target_include_directories(${PROJECT_NAME} PUBLIC usb protocol)

# create map/bin/hex/uf2 file in addition to ELF.
pico_add_extra_outputs(${PROJECT_NAME})

# Binary info
pico_set_program_name(${PROJECT_NAME} ${PROJECT_NAME})
pico_set_program_description(${PROJECT_NAME} "A 3rd stage serial bootloader")
pico_set_program_version(${PROJECT_NAME} "0.1")
pico_set_program_url(${PROJECT_NAME} "https://plajta.eu")

# Flash setup

target_link_options(${PROJECT_NAME} PRIVATE -Wl,--print-memory-usage)

configure_file(${CMAKE_CURRENT_LIST_DIR}/memmap_bootloader.ld.template ${CMAKE_CURRENT_BINARY_DIR}/memmap_bootloader.ld)
pico_set_linker_script(${PROJECT_NAME} ${CMAKE_CURRENT_BINARY_DIR}/memmap_bootloader.ld)
