modules_list = """
# storages
ahci
nvme
virtio_blk
virtio_pci
sd_mod
sr_mod
usb_storage
uas
megaraid_sas
mpt3sas
hpsa

# filesystems
ext4
btrfs
xfs
vfat
f2fs

# usb
xhci_pci
xhci_hcd
ehci_pci
ehci_hcd
ohci_pci
ohci_hcd
uhci_hcd
usbcore
usbhid
hid_generic

# other
dm_mod
dm_snapshot
dm_mirror
raid0
raid1
raid456
raid10

# raspberry pi
mmc_block
sdhci
sdhci_pci

# --- Хранилище (MMC/SD) ---
sunxi_mmc
mmc_block
dw_mmc
dw_mmc_pltfm
dw_mmc_sunxi

# --- HDMI / Дисплей (DRM) ---
sun4i_drm
sun8i_mixer
sun8i_hdmi_phy
dw_hdmi
dw_hdmi_i2s_audio
dw_hdmi_cec
display_connector
panfrost

# --- Аудио (ALSA / ASoC) ---
snd_soc_sunxi_machine
snd_soc_sunxi_ahub
snd_soc_sunxi_ahub_dam
snd_soc_hdmi_codec
snd_soc_core
snd_pcm_dmaengine
snd_compress

# --- USB ---
musb_hdrc
sunxi
phy_generic
usbcore
usbhid
xhci_hcd
ehci_hcd
ohci_hcd
uhci_hcd

# --- Хранилище (MMC/SD) ---
sdhci
sdhci_pci
mmc_block
pcie_brcmstb
reset-raspberrypi

# --- HDMI / Дисплей (DRM) ---
vc4
v3d
drm
drm_kms_helper
cec
i2c_bcm2835
bcm2835_codec
bcm2835_isp
bcm2835_v4l2
bcm2835_mmal_vchiq
raspberrypi_hwmon
videobuf2_dma_contig
videobuf2_vmalloc
videobuf2_memops
videobuf2_v4l2
videobuf2_common
videodev
vc_sm_cma
drm_panel_orientation_quirks
backlight

# --- Аудио (ALSA / ASoC) ---
snd_soc_hdmi_codec
snd_bcm2835
snd_soc_core
snd_compress
snd_pcm_dmaengine

# --- USB ---
usbhid
usb_storage
xhci_hcd
ehci_hcd
ohci_hcd
uhci_hcd
usbcore

# --- Драйверы DRM/KMS для Plymouth ---
# Intel (i915)
drm
drm_kms_helper
i915
intel_agp
simpledrm

# AMD (amdgpu и старый radeon)
amdgpu
radeon
ttm

# NVIDIA (свободный nouveau; для проприетарного nvidia — см. примечание)
nouveau
drm_ttm_helper

# Общий фреймбуфер (резерв, если KMS не сработает)
fbcon
efifb
vesafb

# --- Ядро звуковой подсистемы ---
soundcore
snd
snd_pcm
snd_timer
snd_hwdep
snd_rawmidi
snd_seq_device
snd_mixer_oss
snd_pcm_oss

# --- Контроллеры и кодеки ---
# Intel HDA (самый распространённый на десктопе)
snd_hda_intel
snd_hda_codec
snd_hda_codec_hdmi
snd_hda_codec_realtek
snd_hda_codec_generic
snd_hda_core

# USB-аудио (внешние звуковые карты, гарнитуры)
snd_usb_audio
snd_usbmidi_lib

# Базовые модули (если не встроены в ядро)
snd_soc_core
snd_compress
snd_pcm_dmaengine

# Основной модуль для аналогового и HDMI-аудио на Raspberry Pi
snd_bcm2835

# Для вывода звука через HDMI
snd_soc_hdmi_codec

# Базовые модули
snd_soc_core
snd_compress
snd_pcm_dmaengine

# Модули для аудиосистемы Allwinner
snd_soc_sunxi_machine
snd_soc_sunxi_ahub
snd_soc_sunxi_ahub_dam

# Для вывода звука через HDMI
snd_soc_hdmi_codec

ahci
amdgpu
async_memcpy
async_pq
async_raid6_recov
async_tx
async_xor
axp20x
axp20x_regulator
axp20x_usb_power
backlight
bcm2835_codec
bcm2835_dma
bcm2835_isp
bcm2835_mmal_vchiq
bcm2835_rng
bcm2835_thermal
bcm2835_v4l2
bcm2835_wdt
btrfs
cec
clk_bcm2835
crc32c
cryptd
crypto_simd
display_connector
dm_bufio
dm_cache
dm_crypt
dm_log
dm_mirror
dm_mod
dm_persistent_data
dm_raid
dm_region_hash
dm_snapshot
dm_thin_pool
drm
drm_kms_helper
drm_panel_orientation_quirks
drm_ttm_helper
dw_hdmi
dw_hdmi_cec
dw_hdmi_i2s_audio
dw_mmc
dw_mmc_pltfm
dw_mmc_sunxi
dwc2
efifb
ehci_hcd
ehci_pci
ext4
f2fs
fbcon
gpio_bcm2835
hid_generic
hpsa
i2c_bcm2835
i915
intel_agp
megaraid_sas
mmc_block
mpt3sas
musb_hdrc
nouveau
nvme
ohci_hcd
ohci_pci
panfrost
pcie_brcmstb
phy_generic
phy_sun4i_usb
pinctrl_bcm2835
pinctrl_sun50i_h616
radeon
raid0
raid1
raid10
raid456
raspberrypi_hwmon
reset_raspberrypi
sd_mod
sdhci
sdhci_iproc
sdhci_pci
simpledrm
snd
snd_bcm2835
snd_compress
snd_hda_codec
snd_hda_codec_generic
snd_hda_codec_hdmi
snd_hda_codec_realtek
snd_hda_core
snd_hda_intel
snd_hwdep
snd_mixer_oss
snd_pcm
snd_pcm_dmaengine
snd_pcm_oss
snd_rawmidi
snd_seq_device
snd_soc_core
snd_soc_hdmi_codec
snd_soc_sun4i_i2s
snd_soc_sun50i_codec_analog
snd_soc_sun8i_codec
snd_soc_sunxi_ahub
snd_soc_sunxi_ahub_dam
snd_soc_sunxi_machine
snd_timer
snd_usb_audio
snd_usbmidi_lib
soundcore
spi_bcm2835
sr_mod
sun4i_drm
sun4i_i2s
sun50i_codec_analog
sun50i_h616_ccu
sun6i_dma
sun8i_codec
sun8i_hdmi_phy
sun8i_mixer
sunxi
sunxi_mmc
ttm
uas
uhci_hcd
usb_storage
usbcore
usbhid
v3d
vc4
vc_sm_cma
vesafb
vfat
videobuf2_common
videobuf2_dma_contig
videobuf2_memops
videobuf2_v4l2
videobuf2_vmalloc
videodev
virtio_blk
virtio_pci
xfs
xhci_hcd
xhci_pci
"""