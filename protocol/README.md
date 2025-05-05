# Eternity protocol

This protocol is in many ways similar to the one used by [sisyphus](https://github.com/Plajta/sisyphus). But obviously not the same as the usecase is different.

Commands are sent as strings, fields separated by spaces, terminated by **EOT** (`0x04`) character.

The device responds according to the specific command.

Errors are reported with messages starting with `err`, and successful operations respond with `ack`.

All adresses are in hexadecial with 0 starting at the main program address built into the bootloader at compile time usinga linker script. You CANNOT overwrite the bootloader itself (at least not in a way i am aware of).

A page of flash is 256 bytes long and a sector is 4096 bytes.

On invalid arguments:
  ```
  err invalid arguments
  ```
On overflow of the command buffer (128 bytes set in [protocol.h](./protocol.h)):
  ```
  err command buffer overflow
  ```

A handy python shell to test things out is [here](./shell.py), it uses `PySerial` wrapped in a backend package [here](./protocol.py) and also requires `rich` for nice color output.

Protocol version is incremented when there is a breaking change, it will NOT get incremented when eg. a new field in [info](#info) is added to the end.

---

## Command list

- [read](#read) – Read a page of flash
- [write](#write) – Write a page of flash
- [erase](#erase) – Erase a block of flash
- [info](#info) – Get information about the device and firmware
- [jump](#jump) – Jump to the main program
- [reset](#reset) – Reset the device into bootrom

---

## `read`

Read a page (256 bytes) of flash.

**Usage:**
```
read <address>
```

- `<address>` – Address aligned to page boundary (address % 256 == 0)

**Device response:**

- Device responds with a page (256 bytes) of data immediately.

**Errors:**

- `err invalid input` – if address format is incorrect
- `err invalid range` – if address is out of bounds
- `err address out of range` – if address exceeds flash region
- `err address not aligned` – if address is not page-aligned

---

## `write`

Write a page (256 bytes) of flash.

**Usage:**
```
write <address>
```

- `<address>` – Address aligned to page boundary (address % 256 == 0)

**Protocol:**

1. Device responds:

   ```
   ack
   ```

2. Host sends 256 bytes of data.

3. Device writes data to flash and does not send any final confirmation.

**Errors:**

- `err invalid input` – if address format is incorrect
- `err invalid range` – if address is out of bounds
- `err address out of range` – if address exceeds flash region
- `err address not aligned` – if address is not page-aligned
- `err timeout` – if data is not received in time

---

## `erase`

Erase a sector (4096 bytes) of flash.

**Usage:**
```
erase <address>
```

- `<address>` – Address aligned to sector boundary (address % 4096 == 0)

**Device response:**

- `ack` – if successful

**Errors:**

- `err invalid input` – if address format is incorrect
- `err invalid range` – if address is out of bounds
- `err address out of range` – if address exceeds flash region
- `err address not aligned` – if address is not sector-aligned

---

## `info`

Lists information about the device and firmware.

**Usage:**
```
info
```

**Device response:**
```
<device name> <git commit sha> <protocol version> <build date> <flash size> <bootloader size>
```

- `<device name>` – Name of the device set by CMakeLists.txt
- `<git commit sha>` – Git commit SHA at compile time, when compiled from a repository with uncommitted changes `-dirty` gets appended behind it
- `<protocol version>` – Version of the protocol set in [protocol.h](./protocol.h)
- `<build date>` – Date and time of the firmware build in `YYYY-MM-DD,HH:MM:SS`
- `<flash size>` – Size of the flash memory in bytes
- `<bootloader size>` – Size of the bootloader in bytes set in CMakeLists.txt

Terminated by a newline.

Example:

```
Eternity_bootloader 0448ff6 1 2025-05-04,23:11:21 2097152 32768
```

---

## `jump`

Jumps to the main application stored in flash.

**Usage:**

```
jump
```

**Device response:**

* None (device will immediately jump, breaking connection)

---

## `reset`

Resets the device into bootrom.

**Usage:**

```
reset
```

**Device response:**

* None (device resets and reboots into USB bootloader)

---
