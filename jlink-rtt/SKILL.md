---
name: jlink-rtt
description: Read SEGGER RTT log output in real-time via J-Link debugger, supporting auto-scan of RTT control block addresses, applicable for debugging GD32/STM32 and other ARM Cortex-M microcontrollers. Trigger scenarios: (1) Read RTT debug logs from microcontroller, (2) User mentions "RTT", "view logs", "read serial" (RTT scenario), "real-time logs", (3) Need to view output information when debugging microcontroller programs, (4) Using features similar to SEGGER RTT Viewer. Even if user just says "see what the microcontroller prints" or "read RTT", this skill should be used.
---

# J-Link RTT Log Reading

Invoke `py_jlink_rtt.py` to connect to target chip via J-Link and read SEGGER RTT terminal output in real-time. Supports auto-scan to locate RTT control block in memory, and also supports manually specifying the address.

## Tool Script

**Script Path**: `py_jlink_rtt.py`
**Dependencies**: Python 3.x + `pylink` library

```bash
pip install pylink
```

## Usage

```bash
# Default parameters (GD32F303RC, auto-scan RTT address, 60 second timeout)
python py_jlink_rtt.py

# Specify chip model
python py_jlink_rtt.py -d STM32F103C8

# Manually specify RTT control block address (skip auto-scan, faster startup)
python py_jlink_rtt.py -a 0x20000B90

# Read channel 1, 30 second timeout, enable debug output
python py_jlink_rtt.py -c 1 -t 30 --debug

# Monitor logs while sending data at regular intervals (supports multiple --send)
python py_jlink_rtt.py -d GD32F303RC -t 10 --send 3:hello --send 6:test
```

## Parameter Description

| Parameter     | Short | Description                        | Default       |
| ------------- | ----- | ---------------------------------- | ------------- |
| `--device`    | `-d`  | Target chip model                  | `GD32F303RC` |
| `--channel`   | `-c`  | RTT channel number                 | `0`          |
| `--timeout`   | `-t`  | Running time (seconds)             | `60`         |
| `--rtt-addr`  | `-a`  | RTT control block address (hex)    | Auto-scan    |
| `--send`      | `-s`  | Send data at regular intervals (format see below) | Not send |
| `--debug`     | -     | Print rtt_read return type         | Off          |

## --send Parameter Format

```
--send seconds:content
```

- **seconds**: Time point to trigger sending (relative to when connection starts)
- **content**: String data to send
- Can use multiple `--send` for multiple sends

**Example**:

```bash
# Send "hello" at 3 seconds, send "start_test" at 7 seconds
--send 3:hello --send 7:start_test
```

## RTT Control Block Address

- **Auto-scan**: The script uses a two-layer strategy: prioritize using J-Link SDK built-in `rtt_start(0)` to automatically locate the control block (more reliable); if SDK scan fails, fall back to Python manually scanning RAM area (starting from `0x20000000`, 128KB range), searching for `"SEGGER RTT"` identifier. Recommended for first-time use.
- **Manual specification**: If the address is known (can be obtained from J-Link RTT Viewer or map file), use `-a` parameter to specify for faster startup.

> Note: After each firmware recompilation, the RTT control block address may change. It is recommended to re-auto-scan or check the new map file.

## Working Principle

1. Connect J-Link to target chip via SWD interface
2. Locate RTT control block: prioritize J-Link SDK built-in auto-scan, fall back to Python manual scan on failure
3. Start RTT session, periodically call `rtt_read()` to read buffer
4. According to `--send` schedule, call `rtt_write()` to send data at regular intervals
5. Real-time output UTF-8 decoded content to terminal
6. Disconnect on `Ctrl+C` or when timeout is reached

## Performance Tuning

The script has built-in batch read optimization (max 4096 bytes per read, 10ms refresh interval), suitable for high-frequency log scenarios. If garbled text appears, check if firmware RTT log uses UTF-8 encoding.
