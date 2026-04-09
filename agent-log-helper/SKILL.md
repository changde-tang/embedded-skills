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

### 系统控制接口

| 函数 | 说明 |
|------|------|
| `agent_log_init()` | 初始化日志系统，调用 SEGGER_RTT_Init() |
| `agent_log_set_level(level)` | 设置全局日志级别 |
| `agent_log_get_level()` | 获取当前全局日志级别 |
| `agent_log_set_color_enable(enable)` | 设置颜色开关（1=启用，0=关闭） |
| `agent_log_get_color_enable()` | 获取颜色开关状态 |
| `agent_log_get_tick()` | 获取系统 tick 值（weak symbol，需应用层实现） |

### RTT 数据读取接口

| 函数 | 说明 |
|------|------|
| `agent_log_has_data()` | 检查 RTT 下行缓冲区是否有数据可读 |
| `agent_log_read(buf, size)` | 从 RTT 下行缓冲区读取数据 |

### RTOS 任务接口（可选）

| 函数 | 说明 |
|------|------|
| `agent_log_task()` | 默认的 RTT 命令接收任务（weak symbol） |
| `agent_log_task_create()` | 创建 Agent Log 任务（weak symbol） |
| `agent_log_parse_cmd(cmd)` | 命令解析接口（weak symbol，可由应用层重定义） |

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

| 级别 | 枚举值 | 说明 | 典型用途 |
|------|--------|------|----------|
| OFF | `AGENT_LOG_LEVEL_OFF` | 关闭 | 关闭所有日志 |
| FAT | `AGENT_LOG_LEVEL_FAT` | 致命错误 | 系统即将停机或复位 |
| ERR | `AGENT_LOG_LEVEL_ERR` | 功能失败 | 已降级运行 |
| WRN | `AGENT_LOG_LEVEL_WRN` | 异常情况 | 仍可继续 |
| INF | `AGENT_LOG_LEVEL_INF` | 正常运行节点 | 日志主干 |
| DBG | `AGENT_LOG_LEVEL_DBG` | 调试信息 | 正常运行时关闭 |

**级别数值**：OFF(0) < FAT(1) < ERR(2) < WRN(3) < INF(4) < DBG(5)
- **数值越小级别越高**（FAT 最高优先级，始终显示）
- **数值越大级别越低**（DBG 最低优先级，最详细）

**默认值**：`AGENT_LOG_LEVEL_DBG`（最冗长，全部输出）

**过滤规则**：输出 `level <= s_log_level` 的日志，即只输出**级别数值大于等于当前级别**的日志。

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

## RTOS 任务使用方式

### 方式一：使用内置任务（推荐）

系统提供 `agent_log_task_create()` 创建默认的 RTT 命令接收任务：

```c
#include "agent_log.h"

int main(void)
{
    // 系统硬件初始化...

    agent_log_init();  // 可选，系统启动时调用

    // 创建 Agent Log 任务（接收 RTT 命令）
    agent_log_task_create();

    // 开始任务调度
    vTaskStartScheduler();

    while (1) {}
}
```

### 方式二：自定义命令解析

重定义 `agent_log_parse_cmd()` 实现自定义命令处理：

```c
// 在你的代码中重新定义此函数（弱符号）
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
    // 添加应用自定义命令...
}
```

### 方式三：完全自定义任务

重定义 `agent_log_task()` 实现完全自定义的行为：

```c
// 在你的代码中重新定义此函数（弱符号）
void agent_log_task(void *pvParameters)
{
    char cmd_buf[128];

    agent_log_init();

    while (1) {
        if (agent_log_has_data()) {
            int len = agent_log_read(cmd_buf, sizeof(cmd_buf) - 1);
            if (len > 0) {
                cmd_buf[len] = '\0';
                // 自定义命令处理...
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
```

### RTT 命令交互示例

通过 J-Link RTT Viewer 或其他 RTT 客户端发送命令：

| 命令 | 功能 |
|------|------|
| `dbg` | 设置日志级别为 DBG（全部输出） |
| `inf` | 设置日志级别为 INF（信息及以上） |
| `wrn` | 设置日志级别为 WRN（警告及以上） |
| `err` | 设置日志级别为 ERR（错误及以上） |
| `fat` | 设置日志级别为 FAT（仅致命错误） |
| `off` | 关闭所有日志输出 |

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
- **缓冲区大小**：上行（日志输出）建议 1024 字节，下行（命令输入）建议 16 字节以上
- 如需修改，在 `agent_log.h` 中修改 `AGENT_LOG_RTT_CHANNEL` 宏
- **注意**：下行缓冲区需足够存储命令字符串（建议 64~128 字节），若上行（日志输出不完整）首先调整缓冲区为 2048 字节或更大

---

## 注意事项

1. `agent_log_get_tick()` 是 **weak symbol**，必须由应用层实现
2. 格式化宏内部使用 **128 字节临时缓冲区**，超长字符串会被截断
3. 日志默认输出全部级别（DBG），正式发布时可改为 `INF` 或 `ERR`
4. RTOS 任务接口（`agent_log_task`、`agent_log_task_create`、`agent_log_parse_cmd`）均为 **weak symbol**，应用层可按需重定义
5. `agent_log_task()` 默认堆栈大小为 **1024 字**，优先级为 **tskIDLE_PRIORITY + 4**，可根据实际需求调整
