---
name: jlink-download
description: 使用 J-Link 调试器将固件（.bin 或 .hex）烧录到 ARM Cortex-M 单片机，支持 GD32/STM32 等芯片。触发场景：(1) 烧录固件到单片机，(2) 用户提到"flash"、"烧录"、"下载固件"、"download"，(3) 需要将编译好的 .bin 或 .hex 文件写入芯片，(4) 通过 J-Link 对目标板编程。即使用户只说"把固件烧进去"或"flash 一下芯片"，也应使用此 skill。
---

# J-Link 固件烧录

调用 `py_jlink_download.py` 通过 J-Link 调试器将固件文件烧录到目标芯片，支持擦除、烧录、校验、复位全流程。

## 工具脚本

**脚本路径**：`py_jlink_download.py`  
**依赖**：Python 3.x + `pylink` 库

```bash
pip install pylink
```

## 使用方法

```bash
# 基本用法（默认芯片 GD32F103C8）
python py_jlink_download.py firmware.bin

# 指定芯片型号
python py_jlink_download.py firmware.bin -d STM32F103C8

# 指定烧录起始地址
python py_jlink_download.py firmware.bin -a 0x08001000

# 跳过擦除和验证（加快速度）
python py_jlink_download.py firmware.bin --no-erase --no-verify
```

## 参数说明

| 参数          | 简写 | 说明                         | 默认值       |
| ------------- | ---- | ---------------------------- | ------------ |
| `firmware`    | -    | 固件文件路径（.bin 或 .hex） | **必填**     |
| `--device`    | `-d` | 目标芯片型号                 | `GD32F103C8` |
| `--addr`      | `-a` | 烧录起始地址                 | `0x08000000` |
| `--no-erase`  | -    | 不擦除芯片直接烧录           | 默认擦除     |
| `--no-verify` | -    | 不校验烧录数据               | 默认校验     |
| `--no-run`    | -    | 烧录后不复位运行             | 默认复位     |

## 烧录流程

1. 初始化并连接 J-Link
2. 连接目标芯片（SWD 接口）
3. 擦除芯片（可选）
4. 写入固件文件
5. 读取内存校验数据（可选）
6. 复位并运行程序（可选）

## 常用芯片型号

- `GD32F103C8` / `GD32F303RC`
- `STM32F103C8` / `STM32F103RET6`

> 如芯片型号未知，可运行 `JLinkDevices` 命令查看 J-Link 支持的完整设备列表。

## 注意事项

- 确保 J-Link 调试器已连接到电脑和目标板
- 芯片型号必须与 J-Link 数据库中的名称完全一致
- 对 `.hex` 文件烧录时，校验步骤的报错可忽略（hex 格式包含地址信息）