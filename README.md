# Embedded Skills

嵌入式开发相关的 OpenCode Skill 集合，包含 Keil MDK 工程解析、编译、修改以及 J-Link 烧录和 RTT 日志读取功能。

## 目录结构

```
embedded/
├── agent-log-helper/     # RTT 结构化日志系统
├── keil-parser/          # Keil 工程配置解析
├── keil-modifier/        # Keil .uvprojx 文件修改
├── keil-build/           # Keil 工程编译
├── jlink-download/       # J-Link 固件烧录
└── jlink-rtt/            # J-Link RTT 日志读取
```

## 环境安装

### Python 依赖

所有脚本基于 **Python 3.x** 运行，仅 `jlink-download` 和 `jlink-rtt` 需要额外依赖：

```bash
pip install pylink
```

其他脚本（keil-parser、keil-modifier、keil-build）仅使用 Python 标准库，无需额外安装。

### 硬件工具

| 工具 | 用途 | 备注 |
|------|------|------|
| Keil MDK | 编译 ARM 工程 | 需安装 UV4.exe，默认路径 `D:\application\keil_v5\UV4\UV4.exe` |
| J-Link | 烧录/调试 | 需安装 J-Link 驱动和固件 |

---

## Skill 列表

### 1. agent-log-helper（RTT 结构化日志）

**文件**: `agent-log-helper/agent_log.c` + `agent_log.h`

基于 SEGGER RTT 的日志系统，支持多模块分类（ SYS、I2C、SENSOR、UART、ADC、GPIO、TIMER）、日志级别过滤（OFF/ERR/WRN/INF/DBG/FAT）、格式化输出和颜色显示。

```c
agent_log_init();                              // 初始化
agent_log_inf(AGENT_LOG_MODULE_SYS, "BOOT");  // 无参日志
agent_log_err_fmt(AGENT_LOG_MODULE_I2C, "TIMEOUT", "addr=0x48"); // 格式化日志
agent_log_set_level(AGENT_LOG_LEVEL_INF);     // 设置级别
agent_log_set_color_enable(0);                // 关闭颜色（便于日志重定向）
```

**注意**：`agent_log_get_tick()` 为 weak symbol，需在应用层实现。

---

### 2. keil-parser（工程配置解析）

**脚本**: `keil-parser/py_keil_parser.py`

解析 `.uvprojx` 工程文件，提取宏定义、包含路径和源文件列表。

```bash
python py_keil_parser.py <工程文件路径1> [工程文件路径2] ...
```

**输出**: JSON 格式

```json
{
  "project.uvprojx": {
    "target_name": "Target",
    "defines": "USE_HAL_LIBRARY;STM32F103xB",
    "include_paths": ["../inc/", "../src/"],
    "source_files": [
      {"name": "main.c", "path": "C:/project/main.c"}
    ]
  }
}
```

---

### 3. keil-modifier（工程文件修改）

**脚本**: `keil-modifier/py_keil_modifier.py`

修改 `.uvprojx` 工程文件，支持列出/添加/删除文件和 Group，管理 include 路径。

```bash
# 列出所有 Group 和文件
python py_keil_modifier.py -p MyProject.uvprojx list

# 添加文件到 Group
python py_keil_modifier.py -p MyProject.uvprojx add -f .\src\my_module.c -g Application

# 从工程中移除文件
python py_keil_modifier.py -p MyProject.uvprojx remove -f .\src\old_file.c

# 新建空 Group
python py_keil_modifier.py -p MyProject.uvprojx add-group -g "Middleware"

# 删除 Group
python py_keil_modifier.py -p MyProject.uvprojx remove-group -g "Middleware"

# 列出所有 include 路径
python py_keil_modifier.py -p MyProject.uvprojx list-include-paths

# 添加 include 路径
python py_keil_modifier.py -p MyProject.uvprojx add-include-path -i ".\inc" ".\drivers\inc"

# 移除 include 路径
python py_keil_modifier.py -p MyProject.uvprojx remove-include-path -i ".\old_path"
```

**特性**:
- 自动备份原文件（`.uvprojx.bak`）
- 自动创建不存在的 Group
- 添加时自动去重（文件和 include 路径）
- 写回后 XML 格式化保持可读
- 支持 include 路径的增删查

---

### 4. keil-build（工程编译）

**脚本**: `keil-build/py_keil_build.py`

调用 Keil UV4 命令行编译工程。

```bash
# 增量编译（默认）
python py_keil_build.py -p <工程.uvprojx>

# 全量编译
python py_keil_build.py -p <工程.uvprojx> -r

# 指定 UV4.exe 路径
python py_keil_build.py -p <工程.uvprojx> -k "D:\keil\UV4\UV4.exe"
```

**输出**: JSON 格式

```json
{
  "status": "success",
  "errors_count": 0,
  "warnings_count": 3,
  "full_log": "..."
}
```

---

### 5. jlink-download（固件烧录）

**脚本**: `jlink-download/py_jlink_download.py`

使用 J-Link 将固件烧录到 ARM Cortex-M 芯片。

```bash
# 基本用法（默认 GD32F103C8）
python py_jlink_download.py firmware.bin

# 指定芯片型号
python py_jlink_download.py firmware.bin -d STM32F103C8

# 指定烧录地址
python py_jlink_download.py firmware.bin -a 0x08001000

# 跳过擦除和校验
python py_jlink_download.py firmware.bin --no-erase --no-verify
```

**参数**:

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--device` | `-d` | 芯片型号 | `GD32F103C8` |
| `--addr` | `-a` | 烧录起始地址 | `0x08000000` |
| `--no-erase` | - | 不擦除芯片 | 默认擦除 |
| `--no-verify` | - | 不校验数据 | 默认校验 |
| `--no-run` | - | 烧录后不复位 | 默认复位 |

---

### 6. jlink-rtt（RTT 日志读取）

**脚本**: `jlink-rtt/py_jlink_rtt.py`

通过 J-Link 实时读取 SEGGER RTT 终端输出。

```bash
# 默认参数（自动扫描 RTT 地址，超时 60 秒）
python py_jlink_rtt.py

# 指定芯片
python py_jlink_rtt.py -d STM32F103C8

# 手动指定 RTT 控制块地址
python py_jlink_rtt.py -a 0x20000B90

# 读取通道 1，超时 30 秒
python py_jlink_rtt.py -c 1 -t 30
```

**参数**:

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--device` | `-d` | 芯片型号 | `GD32F303RC` |
| `--channel` | `-c` | RTT 通道号 | `0` |
| `--timeout` | `-t` | 运行时间（秒） | `60` |
| `--rtt-addr` | `-a` | RTT 控制块地址 | 自动扫描 |
| `--debug` | - | 打印调试信息 | 关闭 |

---

## 典型工作流

```
1. agent-log-helper → 向工程添加 RTT 日志系统
2. keil-build       → 编译工程，检查是否有错误
3. jlink-download   → 烧录固件到芯片
4. jlink-rtt        → 调试时读取 RTT 日志
```

---

## 版本信息

| 组件 | 依赖 | 备注 |
|------|------|------|
| Python | 3.x | 标准库脚本无需额外依赖 |
| pylink | 最新版 | J-Link 通信库 |
| Keil MDK | v5 及以上 | UV4.exe 路径可配置 |
| J-Link | 固件最新版 | 需安装 J-Link 驱动 |
