---
name: keil-parser
description: Parse Keil MDK project files (.uvprojx), extract macro definitions, include paths, and source file lists. Trigger scenarios: (1) Need to read or analyze Keil project configuration, (2) Query project's macro definitions (defines), header file paths (include paths), source file list, (3) Need to understand project structure before compiling, flashing, etc., (4) User mentions .uvprojx file and wants to know its contents. Even if user just says "check project configuration" or "analyze this Keil project", this skill should be used.
---

# Keil Project Configuration Parsing

Invoke `py_keil_parser.py` to parse `.uvprojx` project files and get project compilation configuration information.

## Tool Script

**Script Path**: `py_keil_parser.py`
**Dependencies**: Python 3.x standard library (no additional installation required)

## Usage

```bash
python py_keil_parser.py <project file path 1> [project file path 2] ...
```

Supports parsing multiple project files simultaneously.

## Output Structure

Output is in JSON format, containing the following fields:

| Field           | Description                                |
| --------------- | ------------------------------------------ |
| `target_name`   | Project target name                        |
| `defines`       | Macro definition string, separated by semicolons |
| `include_paths` | Include path list                         |
| `source_files`  | Source file list, each item contains `name` and `path` |

### Example Output

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

## Typical Use Cases

- Before calling compilation tools, first parse the project to confirm macro definitions and paths are correct
- Check which source files are included in the project
- Compare configuration differences between two projects
