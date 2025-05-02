#pragma once
#define PROTOCOL_VERSION "1"

extern uint32_t ADDR_MAIN_PROGRAM[];
#define MAIN_PROGRAM_BASE_ADDR (uint32_t)(ADDR_MAIN_PROGRAM)

#define CMD_BUF_SIZE 128
#define INFO_BUF_SIZE 128
#define MAX_DATA_BUF_SIZE FLASH_PAGE_SIZE
#define MAX_ARG_COUNT 2 // Command and address

#define TIMEOUT_MS 10000

#define EOT_CHAR 0x04  // EOT (End Of Transmission) character

void protocol_loop(void);
