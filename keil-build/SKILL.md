---
name: keil-build
description: Compile Keil MDK projects (.uvprojx) via command line using Keil UV4 compiler, supporting incremental build and full rebuild, and parse build results. Trigger scenarios: (1) Compile Keil/MDK ARM project, (2) User mentions "build", "compile", "construct" project, (3) Need to check if project has build errors or warnings, (4) Need to compile before flashing firmware. Even if user just says "compile it for me" or "build this project", this skill should be used.
---

# Keil Project Compilation

Invoke `py_keil_build.py` to compile projects via Keil UV4 command-line interface, and return structured build results.

## Tool Script

**Script Path**: `py_keil_build.py`
**Dependencies**: Python 3.x standard library + Installed Keil MDK (with UV4.exe)

## Usage

```bash
# Incremental build (default)
python py_keil_build.py -p <project.uvprojx>

# Full rebuild (clean rebuild)
python py_keil_build.py -p <project.uvprojx> -r

# Specify UV4.exe path
python py_keil_build.py -p <project.uvprojx> -k "D:\keil\UV4\UV4.exe"
```

## Parameter Description

| Parameter      | Short | Description                | Default                               |
| -------------- | ----- | -------------------------- | ------------------------------------- |
| `--project`    | `-p`  | `.uvprojx` file path      | **Required**                          |
| `--keil`       | `-k`  | UV4.exe path               | `D:\application\keil_v5\UV4\UV4.exe` |
| `--rebuild`    | `-r`  | Full rebuild              | Incremental build                     |

## Output Structure

Returns JSON format result:

```json
{
  "status": "success",       // "success" or "failed" or "error"
  "errors_count": 0,         // Number of build errors
  "warnings_count": 3,       // Number of build warnings
  "full_log": "..."          // Build log (last 2000 characters)
}
```

## Notes

- Keil default installation path: `D:\application\keil_v5\UV4\UV4.exe`, if different please specify with `-k`
- Build log is also written to `build_agent_log.txt` in the project directory
- `errors_count` of -1 indicates log parsing failed (compiler did not output summary line normally)

## Typical Workflow

1. First use `keil-parser` to confirm project configuration is correct
2. Call this tool to build, check if `errors_count` is 0
3. After successful build, use `jlink-download` to flash firmware
