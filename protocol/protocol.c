#include <boards/pico.h>
#include <stdint.h>
#include <string.h>
#include <tusb.h>
#include <stdlib.h>
#include <errno.h>
#include <pico/stdlib.h>
#include <hardware/flash.h>
#include <hardware/sync.h>
#include "pico/bootrom.h"
#include "protocol.h"

__attribute__((noreturn))
void jump_to_main_app(uint32_t vector_table_addr);

void print_newline(char* c) {
    tud_cdc_write_str(c);
    tud_cdc_write_str("\r\n");
    tud_cdc_write_flush();
}

bool hextoaddr(char input[], uint32_t *output) {
    char *endptr;
    errno = 0;

    uint32_t result = strtoul(input, &endptr, 16);

    if (input[0] == '-' || input == endptr || *endptr != '\0') {
        print_newline("err invalid input");
        return false;
    }

    if (errno == ERANGE) {
        print_newline("err invalid range");
        return false;
    }

    if (result > (PICO_FLASH_SIZE_BYTES - ETERNITY_SIZE_BYTES)) {
        print_newline("err address out of range");
        return false;
    }

    if (result % FLASH_PAGE_SIZE) {
        print_newline("err address not aligned");
        return false;
    }

    *output = result;
    return true;
}

// // Function to convert unsigned integer to string, needed because snprintf is too big
void utos(uint32_t value, char *buf) {
    char tmp[10]; // enough for length of uint32_t
    uint8_t i = 0;
    do {
        tmp[i++] = '0' + (value % 10);
        value /= 10;
    } while (value && i < sizeof(tmp));

    // Reverse the digits into buf
    while (i--) {
        *buf++ = tmp[i];
    }
    *buf = '\0';
}

uint8_t append_to_buf(char buf[], size_t buf_len, const char *str, bool add_space) {
    // Relies on strings being null-terminated, but since only literals are used, this is safe.
    size_t len = strlen(str);
    if (len < buf_len) {
        memcpy(buf, str, len);

        // Add a space if needed and is safe
        if (add_space && buf_len - len > 0) {
            buf[len] = ' ';
            len++;
        }
    }

    return len;
}

uint8_t append_int_to_buf(char buf[], size_t buf_len, const uint32_t num, bool add_space) {
    char num_str[10]; // Enough space for uint32_t in decimal
    utos(num, num_str);
    size_t len = append_to_buf(buf, buf_len, num_str, add_space);
    return len;
}


void handle_command(char* cmd) {
    char *args[MAX_ARG_COUNT];
    int argc = 0;

    char *token = strtok(cmd, " ");
    while (token && argc < MAX_ARG_COUNT) {
        args[argc++] = token;
        token = strtok(NULL, " ");
    }

    if (argc == 0) return;

    if (strcmp(cmd, "read") == 0 && argc == 2) {
        uint32_t address;
        if (!hextoaddr(args[1], &address)) {
            return;
        }

        address += MAIN_PROGRAM_BASE_ADDR; // Memory mapped address

        uint8_t data[FLASH_PAGE_SIZE];
        memcpy(data, (unsigned char *)address, FLASH_PAGE_SIZE);
        tud_cdc_write(data, FLASH_PAGE_SIZE);
        tud_cdc_write_flush();
    }
    else if (strcmp(cmd, "write") == 0 && argc == 2) {
        uint32_t address;
        if (!hextoaddr(args[1], &address)) {
            return;
        }

        address += ETERNITY_SIZE_BYTES;

        print_newline("ack");

        size_t received = 0;
        absolute_time_t timeout = make_timeout_time_ms(TIMEOUT_MS);

        uint8_t buffer[FLASH_PAGE_SIZE];

        while (received < FLASH_PAGE_SIZE) {
            uint16_t count = tud_cdc_read(&buffer[received], FLASH_PAGE_SIZE - received);
            if (count > 0) {
                received += count;
                timeout = make_timeout_time_ms(TIMEOUT_MS);  // Reset timeout after successful read
            } else {
                sleep_ms(1);
                if (absolute_time_diff_us(get_absolute_time(), timeout) < 0) {
                    print_newline("err timeout");
                    return;
                }
            }
        }

        uint32_t ints = save_and_disable_interrupts();
        flash_range_program(address, (const uint8_t *)buffer, FLASH_PAGE_SIZE);
        restore_interrupts(ints);
    }
    else if (strcmp(cmd, "erase") == 0 && argc == 2) {
        uint32_t address;
        if (!hextoaddr(args[1], &address)) {
            return;
        }

        if ((address % FLASH_SECTOR_SIZE) != 0) {
            print_newline("err address not aligned");
            return;
        }

        address += ETERNITY_SIZE_BYTES;

        uint32_t ints = save_and_disable_interrupts();
        flash_range_erase(address, FLASH_SECTOR_SIZE);
        restore_interrupts(ints);

        print_newline("ack");
    }
    else if (strcmp(cmd, "info") == 0 && argc == 1) {
        char info_buf[INFO_BUF_SIZE];

        char *p = info_buf; // The original pointer needs to be retained but this one is shifted by the function
        size_t written = 0; // Tracks how much space is used


        written += append_to_buf(&info_buf[written], sizeof(info_buf), "bootloader", 1); // The <protocol> field
        written += append_to_buf(&info_buf[written], sizeof(info_buf), ETERNITY_DEVICE_NAME, 1);
        written += append_to_buf(&info_buf[written], sizeof(info_buf), GIT_COMMIT_SHA, 1);
        written += append_to_buf(&info_buf[written], sizeof(info_buf), PROTOCOL_VERSION, 1);
        written += append_to_buf(&info_buf[written], sizeof(info_buf), BUILD_DATE, 1);
        written += append_int_to_buf(&info_buf[written], sizeof(info_buf), PICO_FLASH_SIZE_BYTES, 1);
        written += append_int_to_buf(&info_buf[written], sizeof(info_buf), ETERNITY_SIZE_BYTES, 0);

        info_buf[INFO_BUF_SIZE-1] = '\0'; // Null-terminate the buffer just to be sure

        print_newline(info_buf);
    }
    else if (strcmp(cmd, "reset") == 0 && argc == 1) {
        rom_reset_usb_boot(0,0);
    }
    else if (strcmp(cmd, "jump") == 0 && argc == 1) {
        jump_to_main_app(MAIN_PROGRAM_BASE_ADDR);
    }
    else {
        print_newline("err unknown command");
    }
}

void protocol_loop()
{
    char cmd_buf[CMD_BUF_SIZE];
    size_t cmd_len = 0;

    while (tud_cdc_connected()) {
        if (tud_cdc_available()) {
            int n = tud_cdc_read(&cmd_buf[cmd_len], CMD_BUF_SIZE - cmd_len);

            cmd_len += n;

            if (cmd_len >= CMD_BUF_SIZE) {
                cmd_len = 0;
                memset(cmd_buf, 0, CMD_BUF_SIZE);
                tud_cdc_read_flush();
                print_newline("err command buffer overflow");
                continue;
            }

            // Look for EOT
            for (size_t i = cmd_len-n; i < cmd_len; ++i) {
                if (cmd_buf[i] == EOT_CHAR) { // 4 is EOT
                    cmd_buf[i] = '\0';  // Null-terminate line
                    handle_command(cmd_buf);  // Process command

                    cmd_len = 0;
                    memset(cmd_buf, 0, CMD_BUF_SIZE);
                    break;
                }
            }
        }
        sleep_ms(10);
    }
}
