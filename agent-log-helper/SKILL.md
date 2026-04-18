---
name: agent-log-helper
description: A guidance skill for integrating the agent_log logging system into Keil/MDK projects. Triggers: (1) User says "add agent_log", "add logging system", (2) User needs structured logging in Keil project, (3) User wants to add log output but doesn't know where to start, (4) User needs log initialization template or tick function implementation. Even if user just says "add log" or "use RTT logging", this skill should be used.
---

# Agent Log Logging System - Keil Project Integration Guide

This skill guides you through integrating the agent_log logging system into Keil/MDK projects, based on SEGGER RTT for structured bidirectional communication.

---

## Step 1: Copy Source Files

Copy the following files to the target project's `LogSystem/` directory:

The agent_log.c and agent_log.h files from this skill's folder.

---

## Step 2: Add to Keil Project

Use the keil-modifier skill to create a `LogSystem` Group and add source files:

```bash
# Create LogSystem Group
keil-modifier: create-group "LogSystem"

# Add agent_log.c to LogSystem Group
keil-modifier: add-file "LogSystem" "LogSystem/agent_log.c"
```

**Note**: `agent_log.h` does not need to be manually added to the project; simply `#include "agent_log.h"` in your code.

---

## Step 3: Add Include Path

Add the `LogSystem` directory to the Keil project include paths:

```
Options for Target → C/C++ → Include Paths → Add ../LogSystem
```

---

## Step 4: Implement Tick Function

`agent_log_get_tick()` is a **weak symbol** that must be implemented by the application layer.

**FreeRTOS Implementation Template**:

```c
// Implement in your main.c or system.c
#include "agent_log.h"

uint32_t agent_log_get_tick(void)
{
    return xTaskGetTickCount();  // FreeRTOS
}
```

**Bare-metal Implementation Template**:

```c
#include "agent_log.h"

extern volatile uint32_t g_sys_tick;  // Your system tick variable

uint32_t agent_log_get_tick(void)
{
    return g_sys_tick;
}
```

---

## Step 5: Initialize the Logging System

Call `agent_log_init()` during system initialization:

```c
#include "agent_log.h"

int main(void)
{
    // System hardware initialization...

    // Initialize logging system
    agent_log_init();

    // Start task scheduler (if using RTOS)
    vTaskStartScheduler();

    while (1) {
        // Main loop
    }
}
```

---

## API Reference

### System Control APIs

| Function | Description |
|----------|-------------|
| `agent_log_init()` | Initialize logging system, calls SEGGER_RTT_Init() |
| `agent_log_set_level(level)` | Set global log level |
| `agent_log_get_level()` | Get current global log level |
| `agent_log_set_color_enable(enable)` | Set color enable flag (1=enable, 0=disable) |
| `agent_log_get_color_enable()` | Get color enable status |
| `agent_log_get_tick()` | Get system tick value (weak symbol, must be implemented by application) |

### RTT Data Read APIs

| Function | Description |
|----------|-------------|
| `agent_log_has_data()` | Check if RTT downstream buffer has data to read |
| `agent_log_read(buf, size)` | Read data from RTT downstream buffer |

### RTOS Task APIs (Optional)

| Function | Description |
|----------|-------------|
| `agent_log_task()` | Default RTT command receive task (weak symbol) |
| `agent_log_task_create()` | Create Agent Log task (weak symbol) |
| `agent_log_parse_cmd(cmd)` | Command parsing interface (weak symbol, can be redefined by application) |

### Log Macros (Non-formatted Version)

Suitable for cases where only event occurrence needs to be recorded without additional data:

```c
agent_log_dbg(mod, event);    // Debug level
agent_log_inf(mod, event);    // Info level
agent_log_wrn(mod, event);    // Warning level
agent_log_err(mod, event);    // Error level
agent_log_fat(mod, event);    // Fatal error level
```

### Log Macros (Formatted Version)

Suitable for formatted data output:

```c
agent_log_dbg_fmt(mod, event, ...);    // Debug level
agent_log_inf_fmt(mod, event, ...);    // Info level
agent_log_wrn_fmt(mod, event, ...);    // Warning level
agent_log_err_fmt(mod, event, ...);    // Error level
agent_log_fat_fmt(mod, event, ...);    // Fatal error level
```

### Log Macros (With Source Location Version)

Output format: `[file:line] [tick][level][module][event] message\r\n`

Location information is automatically extracted from `__FILE__`, `__LINE__`, `__FUNCTION__` for quick log source localization.

**No-argument version**:
```c
agent_log_dbg_loc(mod, event);    // Debug level
agent_log_inf_loc(mod, event);    // Info level
agent_log_wrn_loc(mod, event);    // Warning level
agent_log_err_loc(mod, event);    // Error level
agent_log_fat_loc(mod, event);    // Fatal error level
```

**With-argument version**:
```c
agent_log_dbg_loc_fmt(mod, event, ...);    // Debug level
agent_log_inf_loc_fmt(mod, event, ...);    // Info level
agent_log_wrn_loc_fmt(mod, event, ...);    // Warning level
agent_log_err_loc_fmt(mod, event, ...);    // Error level
agent_log_fat_loc_fmt(mod, event, ...);    // Fatal error level
```

---

## Module List

| Module | Enum Value | Description |
|--------|------------|-------------|
| SYS | `AGENT_LOG_MODULE_SYS` | System |
| I2C | `AGENT_LOG_MODULE_I2C` | I2C Communication |
| SENSOR | `AGENT_LOG_MODULE_SENSOR` | Sensor |
| UART | `AGENT_LOG_MODULE_UART` | UART |
| ADC | `AGENT_LOG_MODULE_ADC` | ADC |
| GPIO | `AGENT_LOG_MODULE_GPIO` | GPIO |
| TIMER | `AGENT_LOG_MODULE_TIMER` | Timer |

---

## Log Levels

| Level | Enum Value | Description | Typical Usage |
|-------|------------|-------------|---------------|
| OFF | `AGENT_LOG_LEVEL_OFF` | Off | Disable all logs |
| FAT | `AGENT_LOG_LEVEL_FAT` | Fatal error | System about to halt or reset |
| ERR | `AGENT_LOG_LEVEL_ERR` | Function failure | Running in degraded mode |
| WRN | `AGENT_LOG_LEVEL_WRN` | Abnormal condition | Can continue |
| INF | `AGENT_LOG_LEVEL_INF` | Normal operation point | Main log flow |
| DBG | `AGENT_LOG_LEVEL_DBG` | Debug info | Disabled during normal operation |

**Level Values**: OFF(0) < FAT(1) < ERR(2) < WRN(3) < INF(4) < DBG(5)
- **Smaller value = higher priority** (FAT highest priority, always displayed)
- **Larger value = lower priority** (DBG lowest priority, most verbose)

**Default Value**: `AGENT_LOG_LEVEL_DBG` (most verbose, outputs all)

**Filtering Rule**: Output logs where `level <= s_log_level`, i.e., only output logs **with level value greater than or equal to the current level**.

---

## Usage Examples

### GPIO Module Logs

```c
// GPIO initialization
agent_log_inf(AGENT_LOG_MODULE_GPIO, "LED_INIT");
agent_log_inf(AGENT_LOG_MODULE_GPIO, "LED_INIT_OK");

// LED control
agent_log_inf_fmt(AGENT_LOG_MODULE_GPIO, "LED1_ON", "mode=%s", s_led_mode_str);
agent_log_inf_fmt(AGENT_LOG_MODULE_GPIO, "LED1_OFF", "mode=%s", s_led_mode_str);
```

### I2C Module Error Logs

```c
agent_log_err_fmt(AGENT_LOG_MODULE_I2C, "TIMEOUT",
    "addr=0x48 retry=%d/%d bus_state=%s",
    retry_count, max_retries, bus_state_str);
```

### Logs with Source Location

Suitable for scenarios requiring precise log source localization (e.g., quickly finding problem code lines during debugging):

```c
// No-argument version
agent_log_err_loc(AGENT_LOG_MODULE_I2C, "TIMEOUT");

// With-argument version
agent_log_err_loc_fmt(AGENT_LOG_MODULE_I2C, "BUS_ERROR",
    "addr=0x%02X flags=0x%X", addr, flags);
```

Example output:
```
[main.c:156] [1234][ERR][I2C   ][TIMEOUT ] addr=0x48 retry=3/3
[main.c:189] [1256][ERR][I2C   ][BUS_ERROR] addr=0x68 flags=0x02
```

---

## RTOS Task Usage

### Method 1: Use Built-in Task (Recommended)

The system provides `agent_log_task_create()` to create the default RTT command receive task:

```c
#include "agent_log.h"

int main(void)
{
    // System hardware initialization...

    agent_log_init();  // Optional, call during system startup

    // Create Agent Log task (receives RTT commands)
    agent_log_task_create();

    // Start task scheduler
    vTaskStartScheduler();

    while (1) {}
}
```

### Method 2: Custom Command Parsing

Redefine `agent_log_parse_cmd()` to implement custom command handling:

```c
// Redefine this function in your code (weak symbol)
void agent_log_parse_cmd(char *cmd)
{
    if (strcmp(cmd, "dbg") == 0) {
        agent_log_set_level(AGENT_LOG_LEVEL_DBG);
        agent_log_inf(AGENT_LOG_MODULE_SYS, "LEVEL_CHG_DBG");
    } else if (strcmp(cmd, "inf") == 0) {
        agent_log_set_level(AGENT_LOG_LEVEL_INF);
        agent_log_inf(AGENT_LOG_MODULE_SYS, "LEVEL_CHG_INF");
    } else if (strcmp(cmd, "wrn") == 0) {
        agent_log_set_level(AGENT_LOG_LEVEL_WRN);
        agent_log_inf(AGENT_LOG_MODULE_SYS, "LEVEL_CHG_WRN");
    } else if (strcmp(cmd, "err") == 0) {
        agent_log_set_level(AGENT_LOG_LEVEL_ERR);
        agent_log_inf(AGENT_LOG_MODULE_SYS, "LEVEL_CHG_ERR");
    } else if (strcmp(cmd, "fat") == 0) {
        agent_log_set_level(AGENT_LOG_LEVEL_FAT);
        agent_log_inf(AGENT_LOG_MODULE_SYS, "LEVEL_CHG_FAT");
    } else if (strcmp(cmd, "off") == 0) {
        agent_log_set_level(AGENT_LOG_LEVEL_OFF);
        agent_log_inf(AGENT_LOG_MODULE_SYS, "LEVEL_CHG_OFF");
    } else if (strcmp(cmd, "help") == 0) {
        agent_log_inf(AGENT_LOG_MODULE_SYS, "Commands: dbg/inf/wrn/err/fat/off");
    }
    // Add application custom commands...
}
```

### Method 3: Fully Custom Task

Redefine `agent_log_task()` to implement fully custom behavior:

```c
// Redefine this function in your code (weak symbol)
void agent_log_task(void *pvParameters)
{
    char cmd_buf[128];

    agent_log_init();

    while (1) {
        if (agent_log_has_data()) {
            int len = agent_log_read(cmd_buf, sizeof(cmd_buf) - 1);
            if (len > 0) {
                cmd_buf[len] = '\0';
                // Custom command handling...
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
```

### RTT Command Interaction Example

Send commands via J-Link RTT Viewer or other RTT client:

| Command | Function |
|---------|----------|
| `dbg` | Set log level to DBG (all output) |
| `inf` | Set log level to INF (info and above) |
| `wrn` | Set log level to WRN (warning and above) |
| `err` | Set log level to ERR (error and above) |
| `fat` | Set log level to FAT (fatal only) |
| `off` | Disable all log output |

---

## Log Format

**Standard Format**: `[tick][level][module][event] additional_data\r\n`

**With Source Location Format**: `[file:line] [tick][level][module][event] additional_data\r\n`

Example:
```
[1234][INF][SYS   ][BOOT    ] ====== System Init ======
[1235][INF][GPIO  ][LED_INIT] LED1 initialized
[1240][ERR][I2C   ][TIMEOUT ] addr=0x48 retry=3/3
[1241][FAT][SYS   ][HALT    ] reason=I2C_FAIL

[main.c:156] [1234][ERR][I2C   ][TIMEOUT ] addr=0x48 retry=3/3
[i2c.c:89]  [1256][ERR][I2C   ][BUS_ERROR] addr=0x68 flags=0x02
```

---

## RTT Configuration

- **Channel Number**: `0` (defined by `AGENT_LOG_RTT_CHANNEL`)
- **Buffer Size**: Upstream (log output) recommended 1024 bytes, downstream (command input) recommended 16 bytes or more
- To modify, change `AGENT_LOG_RTT_CHANNEL` macro in `agent_log.h`
- **Note**: Downstream buffer must be large enough to store command strings (recommended 64~128 bytes). If upstream log output is incomplete, first adjust buffer to 2048 bytes or larger

---

## Notes

1. `agent_log_get_tick()` is a **weak symbol** and must be implemented by the application layer
2. Formatted macros use an internal **128-byte temporary buffer**; strings exceeding this will be truncated
3. Logs output all levels by default (DBG); for production release, change to `INF` or `ERR`
4. RTOS task APIs (`agent_log_task`, `agent_log_task_create`, `agent_log_parse_cmd`) are all **weak symbols**; application layer can redefine as needed
5. Default stack size for `agent_log_task()` is **1024 words**, priority is **tskIDLE_PRIORITY + 4**; adjust according to actual requirements
