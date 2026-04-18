---
name: jlink-download
description: Use J-Link debugger to flash firmware (.bin or .hex) to ARM Cortex-M microcontrollers, supporting GD32/STM32 and other chips. Trigger scenarios: (1) Flash firmware to microcontroller, (2) User mentions "flash", "burn", "download firmware", "download", (3) Need to write compiled .bin or .hex file to chip, (4) Program target board via J-Link. Even if user just says "flash it" or "burn the chip", this skill should be used.
---

# J-Link Firmware Flashing

Invoke `py_jlink_download.py` to flash firmware files to target chips via J-Link debugger, supporting full process of erase, flash, verify, and reset.

## Tool Script

**Script Path**: `py_jlink_download.py`
**Dependencies**: Python 3.x + `pylink` library

```bash
pip install pylink
```

## Usage

```bash
# Basic usage (default chip GD32F103C8)
python py_jlink_download.py firmware.bin

# Specify chip model
python py_jlink_download.py firmware.bin -d STM32F103C8

# Specify flash start address
python py_jlink_download.py firmware.bin -a 0x08001000

# Skip erase and verify (faster)
python py_jlink_download.py firmware.bin --no-erase --no-verify
```

## Parameter Description

| Parameter     | Short | Description                        | Default       |
| ------------- | ----- | ---------------------------------- | ------------- |
| `firmware`    | -     | Firmware file path (.bin or .hex) | **Required**  |
| `--device`    | `-d`  | Target chip model                  | `GD32F103C8`  |
| `--addr`      | `-a`  | Flash start address                | `0x08000000`  |
| `--no-erase`  | -     | Skip chip erase before flashing   | Default erase |
| `--no-verify` | -     | Skip flash data verification       | Default verify |
| `--no-run`    | -     | Do not reset and run after flash   | Default reset |

## Flash Process

1. Initialize and connect J-Link
2. Connect to target chip (SWD interface)
3. Erase chip (optional)
4. Write firmware file
5. Read memory to verify data (optional)
6. Reset and run program (optional)

## Common Chip Models

- `GD32F103C8` / `GD32F303RC`
- `STM32F103C8` / `STM32F103RET6`

> If chip model is unknown, run `JLinkDevices` command to view the complete device list supported by J-Link.

## Notes

- Ensure J-Link debugger is connected to both computer and target board
- Chip model must exactly match the name in J-Link database
- For `.hex` file flashing, verification step errors can be ignored (hex format contains address information)
