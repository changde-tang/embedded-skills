---
name: jlink-rtt
description: 通过 J-Link 调试器实时读取 SEGGER RTT 日志输出，支持自动扫描 RTT 控制块地址，适用于 GD32/STM32 等 ARM Cortex-M 单片机的调试。触发场景：(1) 读取单片机的 RTT 调试日志，(2) 用户提到"RTT"、"查看日志"、"读取串口"（RTT 场景）、"实时日志"，(3) 调试单片机程序时需要查看输出信息，(4) 使用 SEGGER RTT Viewer 类似功能。即使用户只说"看看单片机打印了什么"或"读一下 RTT"，也应使用此 skill。
---

# J-Link RTT 日志读取

调用 `py_jlink_rtt.py` 通过 J-Link 连接目标芯片，实时读取 SEGGER RTT 终端输出。支持自动扫描内存定位 RTT 控制块，也支持手动指定地址。

## 工具脚本

**脚本路径**：`py_jlink_rtt.py`
**依赖**：Python 3.x + `pylink` 库

```bash
pip install pylink
```

## 使用方法

```bash
# 默认参数（GD32F303RC，自动扫描 RTT 地址，超时 60 秒）
python py_jlink_rtt.py

# 指定芯片型号
python py_jlink_rtt.py -d STM32F103C8

# 手动指定 RTT 控制块地址（跳过自动扫描，更快启动）
python py_jlink_rtt.py -a 0x20000B90

# 读取通道 1，超时 30 秒，开启调试输出
python py_jlink_rtt.py -c 1 -t 30 --debug

# 监听日志的同时定时发送数据（支持多次 --send）
python py_jlink_rtt.py -d GD32F303RC -t 10 --send 3:hello --send 6:test
```

## 参数说明

| 参数         | 简写 | 说明                       | 默认值       |
| ------------ | ---- | -------------------------- | ------------ |
| `--device`   | `-d` | 目标芯片型号               | `GD32F303RC` |
| `--channel`  | `-c` | RTT 通道号                 | `0`          |
| `--timeout`  | `-t` | 运行时间（秒）             | `60`         |
| `--rtt-addr` | `-a` | RTT 控制块地址（十六进制） | 自动扫描     |
| `--send`     | `-s` | 定时发送数据（格式见下方） | 不发送       |
| `--debug`    | -    | 打印 rtt_read 返回类型     | 关闭         |

## --send 参数格式

```
--send 秒数:内容
```

- **秒数**：触发发送的时间点（相对于开始连接的时间）
- **内容**：要发送的字符串数据
- 可重复使用多个 `--send` 实现多次发送

**示例**：

```bash
# 第 3 秒发送 "hello"，第 7 秒发送 "start_test"
--send 3:hello --send 7:start_test
```

## RTT 控制块地址

- **自动扫描**：脚本扫描 RAM 区域（默认 `0x20000000` 起，范围 128KB），查找 `"SEGGER RTT"` 标识符。首次使用推荐此方式。
- **手动指定**：如果已知地址（可从 J-Link RTT Viewer 或 map 文件中获取），用 `-a` 参数指定，启动更快。

> 注意：每次重新编译固件后，RTT 控制块地址可能改变，建议重新自动扫描或查阅新 map 文件。

## 工作原理

1. 连接 J-Link，以 SWD 接口连接目标芯片
2. 扫描/定位 RTT 控制块（`_SEGGER_RTT` 结构体）
3. 启动 RTT 会话，周期性调用 `rtt_read()` 读取缓冲区
4. 根据 `--send` 计划定时调用 `rtt_write()` 发送数据
5. 实时将 UTF-8 解码后的内容输出到终端
6. 按 `Ctrl+C` 或达到超时后断开连接

## 性能调优

脚本内置批量读取优化（单次最大 4096 字节，10ms 刷新间隔），适合高频日志场景。如有乱码，检查固件端 RTT 日志是否使用 UTF-8 编码。
