# opi_zero3_st7735
## 160x128 tft
example of connecting the st7735 display to the orange pi zero 3  

## changes in project
* added "waitFbBeforeModules" to "exclude_cmdline" and added "waitFbAfterModules" to "cmdline". this is necessary so that the framebuffer waits after the module loader at the initramfs stage and the deadlock does not occur. these parameters are handled at the custom initramfs level.
* setted "platform_opi_zero3_hdmi_audio_high_priority" to false. so that the sound goes to the line output
* added device tree overlays "display.dtso" and "disable_hdmi.dtso" to connect an external display and disconnect the HDMI
* enabled "uartlogs" and "uartlogs_login" to debug the system via UART
* disable "integrate_firmwares", "integrate_firmwares2" and "integrate_advanced_gpu_packages" to minimize the size of the final firmware

## display connection
* V3.3 - VCC (Power)
* GND - GND (Groud)
* PH9 - CS (Chip select)
* PC11 - RESET
* PC6 - A0/DC (Data/Command)
* PH7 - SDA (MOSI)
* PH6 - SCK (CLK/Clock)
* PC15 - LED (Backlight)
