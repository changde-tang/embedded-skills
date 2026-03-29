---
name: keil-parser
description: 解析 Keil MDK 工程文件（.uvprojx），提取宏定义、包含路径和源文件列表。触发场景：(1) 需要读取或分析 Keil 工程配置，(2) 查询工程的宏定义（defines）、头文件路径（include paths）、源文件列表，(3) 在编译、烧录等流程前需要了解工程结构，(4) 用户提到 .uvprojx 文件并想知道其内容。即使用户只是说"看看工程配置"或"分析一下这个 Keil 工程"，也应使用此 skill。
---

# Keil 工程配置解析

调用 `py_keil_parser.py` 解析 `.uvprojx` 工程文件，获取工程的编译配置信息。

## 工具脚本

**脚本路径**：`py_keil_parser.py`  
**依赖**：Python 3.x 标准库（无需额外安装）

## 使用方法

```bash
python py_keil_parser.py <工程文件路径1> [工程文件路径2] ...
```

支持同时解析多个工程文件。

## 输出结构

输出为 JSON 格式，包含以下字段：

| 字段            | 说明                                |
| --------------- | ----------------------------------- |
| `target_name`   | 工程目标名称                        |
| `defines`       | 宏定义字符串，分号分隔              |
| `include_paths` | 包含路径列表                        |
| `source_files`  | 源文件列表，每项含 `name` 和 `path` |

### 示例输出

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

## 典型用途

- 在调用编译工具前，先解析工程确认宏定义和路径是否正确
- 检查工程中包含了哪些源文件
- 对比两个工程的配置差异