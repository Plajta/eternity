#include <pico/stdlib.h>
#include <hardware/resets.h>
#include <hardware/watchdog.h>
#include <hardware/structs/scb.h>
#include <hardware/structs/nvic.h>
#include <hardware/structs/systick.h>
#include <pico/time.h>
#include <stdint.h>
#include <tusb.h>
#include "protocol.h"

extern uint32_t ADDR_MAIN_PROGRAM[];
#define MAIN_PROGRAM_BASE_ADDR (uint32_t)(ADDR_MAIN_PROGRAM)

static repeating_timer_t usb_timer;

static bool usb_background_task(repeating_timer_t *rt) {
    (void) rt;
    tud_task();  // TinyUSB background task
    return true; // Keep repeating
}

bool vector_table_is_valid(uint32_t vector_table_addr) {
    /*
        Very simple vector table validity check
    */
    uint32_t *vector_table = (uint32_t *)vector_table_addr;
    uint32_t initial_sp = vector_table[0];
    uint32_t reset_handler = vector_table[1];
    return initial_sp != 0xFFFFFFFF && reset_handler != 0xFFFFFFFF;
}

__attribute__((noreturn))
void jump_to_main_app(uint32_t vector_table_addr) {
    /*
        Heavily inspired by:
        https://github.com/usedbytes/rp2040-serial-bootloader/blob/d973e609e46e706122475dd8b60db60bcebd9b60/main.c#L62
    */

    // Disable Interrupts
   	systick_hw->csr &= ~1;
   	nvic_hw->icer = 0xFFFFFFFF;
	nvic_hw->icpr = 0xFFFFFFFF;

	// Reset the peripherals
    reset_block(~(RESETS_RESET_IO_QSPI_BITS | RESETS_RESET_PADS_QSPI_BITS | RESETS_RESET_SYSCFG_BITS | RESETS_RESET_PLL_SYS_BITS));

    // Jump to the main app
    uint32_t *vector_table = (uint32_t *)vector_table_addr;
    uint32_t initial_sp = vector_table[0];
    uint32_t reset_handler = vector_table[1];

    // Set the vector table for the app
    scb_hw->vtor = vector_table_addr;

    // Set up the stack pointer
    asm volatile("msr msp, %0" :: "r"(initial_sp) :);

    // Jump to reset handler of the main app
    ((void (*)(void))reset_handler)();
    __builtin_unreachable();
}

int main() {
    if (!vector_table_is_valid(MAIN_PROGRAM_BASE_ADDR) || watchdog_caused_reboot()){
        gpio_init(PICO_DEFAULT_LED_PIN);
        gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
        tusb_init();
        add_repeating_timer_ms(1, usb_background_task, NULL, &usb_timer);
        while (true){
            if (tud_cdc_connected()){
                protocol_loop();
            }
            sleep_ms(1);
        }
    }
    else{
        jump_to_main_app(MAIN_PROGRAM_BASE_ADDR);
    }
}
