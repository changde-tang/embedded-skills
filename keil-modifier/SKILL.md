---
name: keil-uvprojx-modifier
description: Use this skill to operate Keil MDK's .uvprojx project files. Applicable scenarios: list all Groups and files in project, add source files to specified Group (.c/.cpp/.s/.asm/.lib/.h etc.), remove files from project, create or delete Groups, manage include paths (add/remove/list). Use this skill when user mentions Keil, uvprojx, MDK project file management, or needs batch modification of Keil project structure.
---

# Keil .uvprojx Project File Modification Tool

## Tool Overview

`py_keil_modifier.py` is a command-line script for modifying Keil MDK `.uvprojx` XML project files. It supports listing, adding, removing files and Groups, managing include paths, and automatically backs up the original file before each write.

## File Type Mapping (FileType)

| Extension              | FileType Value | Description              |
| ---------------------- | -------------- | ------------------------ |
| `.c` / `.cpp`          | `1`            | C/C++ source file        |
| `.s` / `.asm`          | `2`            | Assembly source file     |
| `.lib`                 | `3`            | Library file             |
| `.txt`                 | `4`            | Text file                |
| `.h` / `.hpp` / `.inc` | `5`            | Header file              |
| Other                  | `1`            | Default to C source file |

## Command Line Usage

```bash
python py_keil_modifier.py -p <project file.uvprojx> <subcommand> [options]
```

### List All Groups and Files

```bash
python py_keil_modifier.py -p MyProject.uvprojx list
```

Example output:

```
[Target] MyTarget
  [Group] Application
    - main.c  (.\src\main.c)
    - startup.s  (.\startup\startup_stm32.s)
  [Group] Drivers
    - stm32_hal.c  (.\Drivers\stm32_hal.c)
```

### Add File to Group

If Group does not exist, it will be created automatically.

```bash
python py_keil_modifier.py -p MyProject.uvprojx add \
    -f .\src\my_module.c \
    -g Application
```

### Remove File from Project

Exact match by `FilePath`, path must be consistent with project.

```bash
python py_keil_modifier.py -p MyProject.uvprojx remove \
    -f .\src\old_file.c
```

### Create New Empty Group

```bash
python py_keil_modifier.py -p MyProject.uvprojx add-group \
    -g "Middleware"
```

### Delete Group (including all file records under it)

```bash
python py_keil_modifier.py -p MyProject.uvprojx remove-group \
    -g "Middleware"
```

### List All Include Paths

```bash
python py_keil_modifier.py -p MyProject.uvprojx list-include-paths
```

### Add Include Path

```bash
python py_keil_modifier.py -p MyProject.uvprojx add-include-path \
    -i ".\inc" ".\drivers\inc"
```

### Remove Include Path

```bash
python py_keil_modifier.py -p MyProject.uvprojx remove-include-path \
    -i ".\old_path"
```

## Python API Usage

Can also call functions directly in Python scripts:

```python
import argparse
from py_keil_modifier import cmd_add, cmd_list, cmd_remove, cmd_add_group, cmd_remove_group
from py_keil_modifier import cmd_list_include_paths, cmd_add_include_path, cmd_remove_include_path

# Construct args namespace
args = argparse.Namespace(
    project="MyProject.uvprojx",
    file=".\\src\\new_file.c",
    group="Application"
)

# Add file
cmd_add(args)

# List project structure
args_list = argparse.Namespace(project="MyProject.uvprojx")
cmd_list(args_list)

# List include paths
cmd_list_include_paths(args_list)

# Add include path
args_include = argparse.Namespace(
    project="MyProject.uvprojx",
    path=[".\\inc", ".\\drivers\\inc"]
)
cmd_add_include_path(args_include)
```

## Batch Operation Examples

Batch add multiple files to project:

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

Batch add include paths:

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

## Behavior Notes

- **Auto backup**: Each write copies the original file to `<filename .bak>`, e.g., `MyProject.uvprojx.bak`.
- **Auto create Group**: When executing `add`, if target Group does not exist, it will be newly created automatically.
- **Deduplication check**: When adding a file, if `FilePath` already exists in that Group, it will be skipped with `[Skip]` output; duplicate check also applies when adding include paths.
- **Multi-Target support**: Operations apply to **all** Targets in the project, suitable for single Target projects; note this behavior for multi-Target projects.
- **XML formatting**: After write-back, XML will be re-indented to maintain human readability.
- **Encoding**: Output file uses `UTF-8` encoding and includes XML declaration.

## Notes

1. **File path format**: It is recommended to use relative paths consistent with the project (e.g., `.\\src\\main.c`). The `-f` parameter for `remove` command must exactly match the value of `<FilePath>` in XML.
2. **Multi-Target projects**: The script iterates through all `<Target>` nodes. If you need to modify only a specific Target, the script needs additional extension.
3. **Does not modify disk files**: This tool only modifies the `.uvprojx` project file's XML structure. It will not create, move, or delete actual source files on disk.
4. **Dependencies**: Uses only Python standard library (`xml.etree.ElementTree`, `argparse`, `shutil`, `os`), no additional installation required.
