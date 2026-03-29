---
name: keil-build
description: 通过命令行调用 Keil UV4 编译器编译 Keil MDK 工程（.uvprojx），支持增量编译和全量编译，并解析编译结果。触发场景：(1) 编译 Keil/MDK ARM 工程，(2) 用户提到"build"、"编译"、"构建"工程，(3) 需要检查工程是否有编译错误或警告，(4) 在烧录固件前需要先编译工程。即使用户只说"帮我编译一下"或"build 这个工程"，也应使用此 skill。
---

# Keil 工程编译

调用 `py_keil_build.py` 通过 Keil UV4 命令行接口编译工程，并返回结构化的编译结果。

## 工具脚本

**脚本路径**：`py_keil_build.py`  
**依赖**：Python 3.x 标准库 + 已安装 Keil MDK（含 UV4.exe）

## 使用方法

```bash
# 增量编译（默认）
python py_keil_build.py -p <工程.uvprojx>

# 全量编译（clean rebuild）
python py_keil_build.py -p <工程.uvprojx> -r

# 指定 UV4.exe 路径
python py_keil_build.py -p <工程.uvprojx> -k "D:\keil\UV4\UV4.exe"
```

## 参数说明

| 参数        | 简写 | 说明                | 默认值                               |
| ----------- | ---- | ------------------- | ------------------------------------ |
| `--project` | `-p` | `.uvprojx` 文件路径 | **必填**                             |
| `--keil`    | `-k` | UV4.exe 路径        | `D:\application\keil_v5\UV4\UV4.exe` |
| `--rebuild` | `-r` | 全量编译            | 增量编译                             |

## 输出结构

返回 JSON 格式结果：

```json
{
  "status": "success",       // "success" 或 "failed" 或 "error"
  "errors_count": 0,         // 编译错误数量
  "warnings_count": 3,       // 编译警告数量
  "full_log": "..."          // 编译日志（最后 2000 字符）
}
```

## 注意事项

- Keil 默认安装路径：`D:\application\keil_v5\UV4\UV4.exe`，如不同请用 `-k` 指定
- 编译日志同时写入工程目录下的 `build_agent_log.txt`
- `errors_count` 为 -1 表示日志解析失败（编译器未能正常输出汇总行）

## 典型工作流

1. 先用 `keil-parser` 确认工程配置无误
2. 调用此工具编译，检查 `errors_count` 是否为 0
3. 编译成功后，使用 `jlink-download` 烧录固件