# Eternity
A 3rd stage bootloader for the RP2040, originally written for [sisyphus](https://github.com/Plajta/sisyphus).

This bootloader exposes a USB CDC interface using TinyUSB with a protocol that allows for flashing the reset of the flash.

# Size
As this bootloader is written to use USB it's size is not exactly small. It could still be slimmed down though so if anyone is interested in contributing, feel free to open an issue or submit a pull request.

Right now the bootloader claims the first 32kB of the board's flash for itself even though it does only needs ~23kB right now. This was done for potential future expansion.
If you still need that extra space, you can get it by modifying the `ETERNITY_SIZE_BYTES_STRING` setting in CMakeLists.txt.

# Usage
This project can be flashed by itself, just like any other pico-sdk project. The software that gets loaded by it needs to get a bit of configuration though.

To build a project for loading by Eternity, you need to alter the linker script.
Start by copying the [memmap_example.ld.template](./memmap_example.ld.template) file to your project and probably renaming it. If you already have a custom linker script you probably also know how to merge it with the template.

Then add these two lines to your `CMakeLists.txt`:
```
# Fills in the missing lines - thats why it's a .template
configure_file(${CMAKE_CURRENT_LIST_DIR}/memmap_example.ld.template ${CMAKE_BINARY_DIR}/memmap_custom.ld)
pico_set_linker_script(${PROJECT_NAME} ${CMAKE_BINARY_DIR}/memmap_custom.ld)
```

Now you're set! Well not exactly, while this builds a file that can be flashed, either by Eternity or by the normal .uf2 drag-and-drop-a-file method. This file wouldn't work for anyone not using Eternity. For that i recommend making a flag for CMake that only builds for Eternity when the user chooses to do so. For that you can look into how [sisyphus](https://github.com/Plajta/sisyphus) does it's `CMakeLists.txt` file.
