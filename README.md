# Eternity
A 3rd stage bootloader for the RP2040, originally written for [sisyphus](https://github.com/Plajta/sisyphus).

This bootloader exposes a USB CDC interface using TinyUSB with a [protocol](./protocol/) that allows for flashing the reset of the flash.

# Size
As this bootloader is written to use USB its size is not exactly small. It could still be slimmed down though so if anyone is interested in contributing, feel free to open an issue or submit a pull request.

Right now the bootloader claims the first 32kB of the board's flash for itself even though it does only needs ~23kB right now. This was done for potential future expansion.
If you still need that extra space, you can get it by modifying the `ETERNITY_SIZE_BYTES_STRING` setting in CMakeLists.txt.

# Usage
This project can be flashed by itself, just like any other pico-sdk project. The software that gets loaded by it needs to get a bit of configuration though.

To build a project for loading by Eternity, you need to alter the linker script.
Start by copying the [memmap_example.ld.template](./memmap_example.ld.template) file to your project and probably renaming it. If you don't plan on integrating your project with Eternity, you'll need to also rewrite the two mentions of `${ETERNITY_SIZE_BYTES_STRING}` to whatever size you chose (probably 32kB). If you already have a custom linker script you probably also know how to merge it with the template.

Then add these two lines to your `CMakeLists.txt`:
```cmake
# Fills in the missing lines - thats why it's a .template
configure_file(${CMAKE_CURRENT_LIST_DIR}/memmap_example.ld.template ${CMAKE_BINARY_DIR}/memmap_custom.ld)
pico_set_linker_script(${PROJECT_NAME} ${CMAKE_BINARY_DIR}/memmap_custom.ld)
```

Now you're set! Well not exactly, while this builds a file that can be flashed, either by Eternity or by the normal .uf2 drag-and-drop-a-file method. This file wouldn't work for anyone not using Eternity. For that I recommend making a flag for CMake that only builds for Eternity when the user chooses to do so. For that you can look into how [sisyphus](https://github.com/Plajta/sisyphus) does it's `CMakeLists.txt` file.

## Including inside one binary
That isn't where you have to stop though! You can also include the project in a more integrated way that builds your project with Eternity into one single binary for easy flashing.

First you add eternity as a submodule to your project:
```bash
git submodule add https://github.com/Plajta/eternity.git
```

Now you can add eternity as a subdirectory in your project by adding the following lines to your `CMakeLists.txt`:
```cmake
add_subdirectory(eternity)
```

Then by adding these following lines you can build your project with Eternity into one single binary for easy initial flashing.
```cmake
# Convert string to integer
math(EXPR ETERNITY_SIZE_BYTES "${ETERNITY_SIZE_BYTES_STRING}")

set(OUTPUT_BIN "${CMAKE_BINARY_DIR}/combined.bin")

# Run the script after building main_app
add_custom_command(
    OUTPUT ${OUTPUT_BIN}
    COMMAND ${CMAKE_COMMAND} -E env python3 ${CMAKE_SOURCE_DIR}/eternity/merge_binaries.py
        ${CMAKE_BINARY_DIR}/eternity/eternity.bin
        ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.bin
        ${ETERNITY_SIZE_BYTES}
        ${OUTPUT_BIN}
    DEPENDS ${PROJECT_NAME} eternity
    COMMENT "Generating combined binary"
    VERBATIM
)

if(NOT PICO_NO_PICOTOOL)
    set(OUTPUT_UF2 "${CMAKE_BINARY_DIR}/combined.uf2")

    add_custom_command(
        OUTPUT ${OUTPUT_UF2}
        COMMAND picotool uf2 convert --quiet --family rp2040 ${OUTPUT_BIN} ${OUTPUT_UF2}
        DEPENDS ${OUTPUT_BIN}
        COMMENT "Generating combined UF2"
        VERBATIM
    )
    add_custom_target(combine_eternity ALL
        DEPENDS ${OUTPUT_BIN} ${OUTPUT_UF2}
    )
else()
    message(STATUS "PICO_NO_PICOTOOL is set — only generating .bin")
    add_custom_target(combine_eternity ALL
        DEPENDS ${OUTPUT_BIN}
    )
endif()
```

Yeah this one's a doozie but it's pretty cool!
