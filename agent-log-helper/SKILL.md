---
name: agent-log-helper
description: 向 Keil/MDK 工程添加 agent_log 日志系统的指导 skill。触发场景：(1) 用户说"帮我添加 agent_log"、"添加日志系统"，(2) 用户需要在 Keil 工程中使用结构化日志，(3) 用户想要在代码中添加日志输出但不知道如何下手，(4) 用户需要日志初始化模板或 tick 函数实现。即使用户只说"添加日志"或"我想用 RTT 日志"，也应使用此 skill。
---

# Agent Log 日志系统 - Keil 工程集成指南

本 skill 指导你向 Keil/MDK 工程添加 agent_log 日志系统，基于 SEGGER RTT 实现结构化双向通信。

---

## 第一步：复制源文件

将以下文件复制到目标工程的 `LogSystem/` 目录下：

该skills文件夹下的agent_log.c，agent_log.h

---

## 第二步：添加到 Keil 工程

使用 keil-modifier skill 创建 `LogSystem` Group 并添加源文件：

```bash
# 创建 LogSystem Group
keil-modifier: create-group "LogSystem"

# 将 agent_log.c 添加到 LogSystem Group
keil-modifier: add-file "LogSystem" "LogSystem/agent_log.c"
```

**说明**：`agent_log.h` 不需要手动添加到工程，只需要在代码中 `#include "agent_log.h"` 即可。

---

## 第三步：添加头文件路径

在 Keil 工程选项中添加 `App` 目录到 include 路径：

```
Options for Target → C/C++ → Include Paths → 添加 ../LogSystem
```

---

## 第四步：实现时间戳函数

`agent_log_get_tick()` 是 **weak symbol**，需要你在应用层实现。

**FreeRTOS 实现模板**：

```c
// 在你的 main.c 或 system.c 中实现
#include "agent_log.h"

uint32_t agent_log_get_tick(void)
{
    return xTaskGetTickCount();  // FreeRTOS
}
```

**裸机实现模板**：

```c
#include "agent_log.h"

extern volatile uint32_t g_sys_tick;  // 你的系统 tick 变量

uint32_t agent_log_get_tick(void)
{
    return g_sys_tick;
}
```

---

## 第五步：初始化日志系统

在系统初始化阶段调用 `agent_log_init()`：

```c
#include "agent_log.h"

int main(void)
{
    // 系统硬件初始化...

    // 初始化日志系统
    agent_log_init();

    // 开始任务调度（如果有 RTOS）
    vTaskStartScheduler();

    while (1) {
        // 主循环
    }
}
```

---

## API 参考

### 日志宏（无格式化版本）

适用于仅需记录事件发生，无需附加数据：

```c
agent_log_dbg(mod, event);    // 调试级别
agent_log_inf(mod, event);    // 信息级别
agent_log_wrn(mod, event);    // 警告级别
agent_log_err(mod, event);    // 错误级别
agent_log_fat(mod, event);    // 致命错误级别
```

### 日志宏（格式化版本）

适用于需要输出格式化数据：

```c
agent_log_dbg_fmt(mod, event, ...);    // 调试级别
agent_log_inf_fmt(mod, event, ...);    // 信息级别
agent_log_wrn_fmt(mod, event, ...);    // 警告级别
agent_log_err_fmt(mod, event, ...);    // 错误级别
agent_log_fat_fmt(mod, event, ...);    // 致命错误级别
```

### 日志宏（带源码位置版本）

输出格式：`[file:line] [tick][level][module][event] message\r\n`

位置信息自动从 `__FILE__`、`__LINE__`、`__FUNCTION__` 提取，便于快速定位日志来源。

**无参版本**：
```c
agent_log_dbg_loc(mod, event);    // 调试级别
agent_log_inf_loc(mod, event);    // 信息级别
agent_log_wrn_loc(mod, event);    // 警告级别
agent_log_err_loc(mod, event);    // 错误级别
agent_log_fat_loc(mod, event);    // 致命错误级别
```

**有参版本**：
```c
agent_log_dbg_loc_fmt(mod, event, ...);    // 调试级别
agent_log_inf_loc_fmt(mod, event, ...);    // 信息级别
agent_log_wrn_loc_fmt(mod, event, ...);    // 警告级别
agent_log_err_loc_fmt(mod, event, ...);    // 错误级别
agent_log_fat_loc_fmt(mod, event, ...);    // 致命错误级别
```

---

## 模块列表

| 模块 | 枚举值 | 说明 |
|------|--------|------|
| SYS | `AGENT_LOG_MODULE_SYS` | 系统 |
| I2C | `AGENT_LOG_MODULE_I2C` | I2C 通信 |
| SENSOR | `AGENT_LOG_MODULE_SENSOR` | 传感器 |
| UART | `AGENT_LOG_MODULE_UART` | 串口 |
| ADC | `AGENT_LOG_MODULE_ADC` | ADC |
| GPIO | `AGENT_LOG_MODULE_GPIO` | GPIO |
| TIMER | `AGENT_LOG_MODULE_TIMER` | 定时器 |

---

## 日志级别

| 级别 | 说明 | 典型用途 |
|------|------|----------|
| FAT | 致命错误 | 系统即将停机或复位 |
| ERR | 功能失败 | 已降级运行 |
| WRN | 异常情况 | 仍可继续 |
| INF | 正常运行节点 | 日志主干 |
| DBG | 调试信息 | 正常运行时关闭 |

**级别数值**：OFF(0) < ERR(1) < WRN(2) < INF(3) < DBG(4) < FAT(5)

**默认值**：`AGENT_LOG_LEVEL_FAT`（最冗长，全部输出）

---

## 使用示例

### GPIO 模块日志

```c
// GPIO 初始化
agent_log_inf(AGENT_LOG_MODULE_GPIO, "LED_INIT");
agent_log_inf(AGENT_LOG_MODULE_GPIO, "LED_INIT_OK");

// LED 控制
agent_log_inf_fmt(AGENT_LOG_MODULE_GPIO, "LED1_ON", "mode=%s", s_led_mode_str);
agent_log_inf_fmt(AGENT_LOG_MODULE_GPIO, "LED1_OFF", "mode=%s", s_led_mode_str);
```

### I2C 模块错误日志

```c
agent_log_err_fmt(AGENT_LOG_MODULE_I2C, "TIMEOUT",
    "addr=0x48 retry=%d/%d bus_state=%s",
    retry_count, max_retries, bus_state_str);
```

### 带源码位置的日志

适用于需要精确定位日志来源的场景（如调试时快速找到问题代码行）：

```c
// 无参版本
agent_log_err_loc(AGENT_LOG_MODULE_I2C, "TIMEOUT");

// 有参版本
agent_log_err_loc_fmt(AGENT_LOG_MODULE_I2C, "BUS_ERROR",
    "addr=0x%02X flags=0x%X", addr, flags);
```

输出示例：
```
[main.c:156] [1234][ERR][I2C   ][TIMEOUT ] addr=0x48 retry=3/3
[main.c:189] [1256][ERR][I2C   ][BUS_ERROR] addr=0x68 flags=0x02
```

---

## 动态调整日志级别

可以在运行时通过 RTT 下行通道接收命令调整日志级别：

```c
char rx_buf[128];

while (1) {
    if (agent_log_has_data()) {
        int rx_len = agent_log_read(rx_buf, sizeof(rx_buf));
        if (rx_len > 0) {
            if (strcmp(rx_buf, "dbg") == 0) {
                agent_log_set_level(AGENT_LOG_LEVEL_DBG);
                agent_log_inf(AGENT_LOG_MODULE_SYS, "LEVEL_CHG_DBG");
            } else if (strcmp(rx_buf, "inf") == 0) {
                agent_log_set_level(AGENT_LOG_LEVEL_INF);
                agent_log_inf(AGENT_LOG_MODULE_SYS, "LEVEL_CHG_INF");
            }
        }
    }
    vTaskDelay(pdMS_TO_TICKS(10));
}
```

---

## 日志格式

**标准格式**：`[tick][level][module][event] 附加数据\r\n`

**带源码位置格式**：`[file:line] [tick][level][module][event] 附加数据\r\n`

示例：
```
[1234][INF][SYS   ][BOOT    ] ====== System Init ======
[1235][INF][GPIO  ][LED_INIT] LED1 initialized
[1240][ERR][I2C   ][TIMEOUT ] addr=0x48 retry=3/3
[1241][FAT][SYS   ][HALT    ] reason=I2C_FAIL

[main.c:156] [1234][ERR][I2C   ][TIMEOUT ] addr=0x48 retry=3/3
[i2c.c:89]  [1256][ERR][I2C   ][BUS_ERROR] addr=0x68 flags=0x02
```

---

## RTT 配置

- **通道号**：`0`（`AGENT_LOG_RTT_CHANNEL` 定义）
- **缓冲区大小**：上行 1024 字节，下行 16 字节
- 如需修改，在 `agent_log.h` 中修改 `AGENT_LOG_RTT_CHANNEL` 宏

---

## 注意事项

1. `agent_log_get_tick()` 是 **weak symbol**，必须由应用层实现
2. 格式化宏内部使用 **128 字节临时缓冲区**，超长字符串会被截断
3. 日志默认输出全部级别（FATA），正式发布时可改为 `INF` 或 `ERR`
