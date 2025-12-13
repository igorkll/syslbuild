// panic.c
#include <stdint.h>

volatile uint16_t* VIDEO = (uint16_t*)0xB8000;
const int COLS = 80;
const int ROWS = 25;

void puts(const char* s) {
    for (int i = 0; s[i]; i++) {
        VIDEO[i] = (uint16_t)s[i] | (0x0F << 8);
    }
}

void halt() {
    #if defined(__x86_64__) || defined(__i386__)
        while (1) __asm__ volatile("hlt");
    #elif defined(__aarch64__) || defined(__arm__)
        while (1) __asm__ volatile("wfi");
    #else
        while (1) { }
    #endif
}

void _start() {
    puts("!!! KERNEL PANIC !!!\nSystem halted.\n");
    halt();
}

