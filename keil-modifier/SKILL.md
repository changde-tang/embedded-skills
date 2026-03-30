---
name: keil-uvprojx-modifier
description: 使用此 skill 来操作 Keil MDK 的 .uvprojx 工程文件。适用场景包括：列出工程中所有 Group 和文件、向指定 Group 添加源文件（.c/.cpp/.s/.asm/.lib/.h 等）、从工程中移除文件、新建或删除 Group、管理 include 路径（添加/删除/列出）。当用户提到 Keil、uvprojx、MDK 工程文件管理，或需要批量修改 Keil 工程结构时，使用此 skill。
---

# Keil .uvprojx 工程文件修改工具

## 工具概述

`py_keil_modifier.py` 是一个用于修改 Keil MDK `.uvprojx` XML 工程文件的命令行脚本。它支持列出、添加、删除文件和 Group，管理 include 路径，每次写入前自动备份原文件。

## 文件类型映射（FileType）

| 扩展名                 | FileType 值 | 说明                |
| ---------------------- | ----------- | ------------------- |
| `.c` / `.cpp`          | `1`         | C/C++ 源文件        |
| `.s` / `.asm`          | `2`         | 汇编源文件          |
| `.lib`                 | `3`         | 库文件              |
| `.txt`                 | `4`         | 文本文件            |
| `.h` / `.hpp` / `.inc` | `5`         | 头文件              |
| 其他                   | `1`         | 默认按 C 源文件处理 |

## 命令行用法

```bash
python py_keil_modifier.py -p <工程文件.uvprojx> <子命令> [选项]
```

### 列出所有 Group 和文件

```bash
python py_keil_modifier.py -p MyProject.uvprojx list
```

输出示例：

```
[Target] MyTarget
  [Group] Application
    - main.c  (.\src\main.c)
    - startup.s  (.\startup\startup_stm32.s)
  [Group] Drivers
    - stm32_hal.c  (.\Drivers\stm32_hal.c)
```

### 添加文件到 Group

若 Group 不存在则自动创建。

```bash
python py_keil_modifier.py -p MyProject.uvprojx add \
    -f .\src\my_module.c \
    -g Application
```

### 从工程中移除文件

按 `FilePath` 精确匹配，路径需与工程中一致。

```bash
python py_keil_modifier.py -p MyProject.uvprojx remove \
    -f .\src\old_file.c
```

### 新建空 Group

```bash
python py_keil_modifier.py -p MyProject.uvprojx add-group \
    -g "Middleware"
```

### 删除 Group（含其下所有文件记录）

```bash
python py_keil_modifier.py -p MyProject.uvprojx remove-group \
    -g "Middleware"
```

### 列出所有 include 路径

```bash
python py_keil_modifier.py -p MyProject.uvprojx list-include-paths
```

### 添加 include 路径

```bash
python py_keil_modifier.py -p MyProject.uvprojx add-include-path \
    -i ".\inc" ".\drivers\inc"
```

### 移除 include 路径

```bash
python py_keil_modifier.py -p MyProject.uvprojx remove-include-path \
    -i ".\old_path"
```

## Python API 用法

也可以直接在 Python 脚本中调用各函数：

```python
import argparse
from py_keil_modifier import cmd_add, cmd_list, cmd_remove, cmd_add_group, cmd_remove_group
from py_keil_modifier import cmd_list_include_paths, cmd_add_include_path, cmd_remove_include_path

# 构造 args 命名空间
args = argparse.Namespace(
    project="MyProject.uvprojx",
    file=".\\src\\new_file.c",
    group="Application"
)

# 添加文件
cmd_add(args)

# 列出工程结构
args_list = argparse.Namespace(project="MyProject.uvprojx")
cmd_list(args_list)

# 列出 include 路径
cmd_list_include_paths(args_list)

# 添加 include 路径
args_include = argparse.Namespace(
    project="MyProject.uvprojx",
    path=[".\\inc", ".\\drivers\\inc"]
)
cmd_add_include_path(args_include)
```

## 批量操作示例

批量向工程添加多个文件：

```python
import argparse
from py_keil_modifier import cmd_add

PROJECT = "MyProject.uvprojx"

files_to_add = [
    (".\\src\\module_a.c", "Application"),
    (".\\src\\module_b.c", "Application"),
    (".\\drivers\\drv_uart.c", "Drivers"),
    (".\\drivers\\drv_spi.c", "Drivers"),
]

for file_path, group_name in files_to_add:
    args = argparse.Namespace(
        project=PROJECT,
        file=file_path,
        group=group_name
    )
    cmd_add(args)
```

批量添加 include 路径：

```python
import argparse
from py_keil_modifier import cmd_add_include_path

PROJECT = "MyProject.uvprojx"

include_paths = [
    ".\\inc",
    ".\\drivers\\inc", 
    ".\\middleware\\inc"
]

args = argparse.Namespace(
    project=PROJECT,
    path=include_paths
)
cmd_add_include_path(args)
```

## 行为说明

- **自动备份**：每次写入前将原文件复制为 `<文件名>.bak`，例如 `MyProject.uvprojx.bak`。
- **自动创建 Group**：执行 `add` 时若目标 Group 不存在，自动新建。
- **去重检查**：添加文件时若 `FilePath` 已存在于该 Group，跳过并输出 `[Skip]`；添加 include 路径时也会检查重复。
- **多 Target 支持**：操作会作用于工程中的**所有** Target，适合单 Target 工程；多 Target 工程请注意此行为。
- **XML 格式化**：写回后 XML 会被重新缩进，保持人类可读。
- **编码**：输出文件使用 `UTF-8` 编码并包含 XML 声明。

## 注意事项

1. **文件路径格式**：建议使用与工程一致的相对路径（如 `.\\src\\main.c`），`remove` 命令的 `-f` 参数必须与 XML 中 `<FilePath>` 的值完全一致。
2. **多 Target 工程**：脚本会遍历所有 `<Target>` 节点，如需只修改特定 Target，需要额外扩展脚本。
3. **不修改磁盘文件**：此工具只修改 `.uvprojx` 工程文件的 XML 结构，不会在磁盘上创建、移动或删除实际源文件。
4. **依赖库**：仅使用 Python 标准库（`xml.etree.ElementTree`、`argparse`、`shutil`、`os`），无需额外安装。