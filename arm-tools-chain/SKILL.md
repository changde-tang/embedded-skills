---
name: arm-tools-chain
description: ARM MCU development full-process orchestration skill. Must read this file first when performing any ARM/Keil/MDK/STM32/GD32 related development tasks to determine execution order and strategy. Applicable scenarios: using ARM toolchain, developing new features, adding logs, compiling and flashing, debugging and viewing logs, full-process development, etc. Keywords: Keil, MDK, ARM, STM32, GD32, uvprojx, compile, flash, RTT, log, development.
---

# ARM MCU Development · Orchestration Controller

## 1. Sub-Skill Index

| ID   | Skill            | Core Responsibility                  |
| ---- | ---------------- | ------------------------------------- |
| S1   | keil-parser      | Parse .uvprojx, read project config  |
| S2   | keil-modifier    | Modify project structure (files, Groups, paths) |
| S3   | agent-log-helper | Inject agent_log logging system into project |
| S4   | keil-build       | Command-line compile, parse errors/warnings |
| S5   | jlink-download   | Flash firmware via J-Link            |
| S6   | jlink-rtt        | Real-time RTT log reading             |

> **Required before execution**: Read corresponding SKILL.md → Execute → Check result → Continue or rollback

---

## 2. Task Type Recognition

Before starting any task, determine which scenario the user's intent falls into, and select the corresponding flow:

| User Intent Keywords              | Execution Flow             |
| -------------------------------- | -------------------------- |
| Develop new feature, add code, modify project | → Flow A (full development flow) |
| Add logs, agent_log, check logs | → Flow B (log integration flow) |
| Compile only, build, check errors | → Flow C (standalone compile) |
| Flash, download firmware         | → Flow D (compile + flash) |
| View logs, RTT, debug output     | → Flow E (flash + debug) |
| I'm not sure / do everything for me | → Flow A (full flow) |

---

## 3. Main Execution Flows

### Flow A · Full Development Flow (Recommended Default)

```
S1(parse) → S2(modify) → S3(inject log) → S4(build) → S5(flash) → S6(view log)
```

Applicable for: Starting from scratch, feature development, unsure where to start.

**Execution Steps:**

```
STEP 1 [S1 keil-parser]
  Goal: Understand current project structure
  Read: keil-parser/SKILL.md
  Execute: Parse .uvprojx, output Groups, source files, include paths, defines
  Success: Successfully extracted project configuration
  Failure: → See "Error Handling E1"

STEP 2 [S2 keil-modifier]
  Goal: Modify project structure as needed
  Prerequisite: Known project structure from S1 output
  Read: keil-modifier/SKILL.md
  Execute: Add/remove files, Groups, include paths
  Success: .uvprojx can be opened normally in Keil after modification
  Skip condition: Skip if user did not require modifying project structure

STEP 3 [S3 agent-log-helper]
  Goal: Inject structured logging system
  Prerequisite: S2 complete (or skipped)
  Read: agent-log-helper/SKILL.md
  Execute: Add log macros, initialization function, tick handling
  Success: Log-related files added to project, code can compile
  Skip condition: Skip if user explicitly does not need logs

STEP 4 [S4 keil-build]
  Goal: Compile project, ensure no errors
  Read: keil-build/SKILL.md
  Execute: Incremental build, parse output
  Success: Build return code is 0, no Errors
  Warning: Warnings exist, inform user but do not block flow
  Failure: → See "Error Handling E2"

STEP 5 [S5 jlink-download]
  Goal: Flash compiled output to target chip
  Prerequisite: S4 build succeeded, .bin/.hex file exists
  Read: jlink-download/SKILL.md
  Execute: Flash firmware via J-Link
  Success: Flash complete, chip responds
  Failure: → See "Error Handling E3"

STEP 6 [S6 jlink-rtt]
  Goal: View real-time RTT log output
  Prerequisite: S5 flash succeeded
  Read: jlink-rtt/SKILL.md
  Execute: Auto-scan RTT control block, read logs
  Success: Logs output normally
  Failure: → See "Error Handling E4"
```

---

### Flow B · Log Integration Flow

```
S1(parse) → S3(inject log) → S4(build) → S5(flash) → S6(view log)
```

Applicable for: Project already exists, only need to add agent_log logging system. Skips S2 (no project structure modification).

---

### Flow C · Standalone Compile

```
S4(build)
```

Applicable for: Code already modified, just need to check for build errors.
Failure: → Based on error content, decide to return to S1/S2/S3 for fixes, then rebuild.

---

### Flow D · Compile + Flash

```
S4(build) → S5(flash)
```

Applicable for: Code is ready, execute compile then flash directly.

---

### Flow E · Flash + Debug

```
S5(flash) → S6(view log)
```

Applicable for: Firmware already compiled, flash directly and view RTT logs.

---

## 4. Error Handling and Rollback Strategy

### E1 · keil-parser Failure (Cannot Parse Project)

**Possible Causes**: .uvprojx path error, file corrupted, format incompatible
**Rollback Strategy**:

```
1. Confirm .uvprojx file path with user
2. Check if file exists and is readable
3. Fix and re-execute S1
4. If still failing → Stop, report specific error to user
```

---

### E2 · keil-build Build Failure

**Distribute based on error type:**

```
Case A: Syntax error / function undefined / header file missing
  Rollback: → S3(fix code) or S2(supplement include path) → Rebuild S4
  Max retries: 2

Case B: Link error (symbol redefinition, memory overflow)
  Rollback: → S2(check for duplicate file additions) → Rebuild S4
  Max retries: 1

Case C: Toolchain error (UV4 path issue)
  Rollback: → Stop, prompt user to check Keil installation path
```

---

### E3 · jlink-download Flash Failure

**Distribute based on error type:**

```
Case A: J-Link not connected / device not recognized
  Rollback: → Prompt user to check USB connection and target board power → Retry S5
  Max retries: 2

Case B: Firmware file does not exist
  Rollback: → Re-execute S4 build → Then execute S5
  Max retries: 1

Case C: Chip model mismatch
  Rollback: → Confirm chip model with user → Stop and wait for user input
```

---

### E4 · jlink-rtt Read Failure

**Distribute based on error type:**

```
Case A: RTT control block scan failed
  Rollback: → Prompt to check if agent_log initialization is called in code → Retry S6
  Max retries: 1

Case B: J-Link disconnected
  Rollback: → Check connection → Re-execute S5(reflash) → Then execute S6

Case C: No output (program may be stuck)
  Rollback: → Suggest user to check if tick function is called in main()
  → Fix, then return to Flow D to reflash
```

---

## 5. Execution Log Specification

Each step must output in the following format to make execution transparent and traceable:

```
╔══════════════════════════════════════╗
║  [STEP S1] keil-parser · Parse Project ║
╚══════════════════════════════════════╝
→ Reading: keil-parser/SKILL.md
→ Executing...
✅ Success: Found 3 Groups, 12 source files, 5 include paths

╔══════════════════════════════════════╗
║  [STEP S4] keil-build · Build Project  ║
╚══════════════════════════════════════╝
→ Reading: keil-build/SKILL.md
→ Executing incremental build...
❌ Failure: error C3861: 'agent_log_init' undeclared
→ Triggering rollback strategy E2-CaseA: returning to S3 to fix code
```

---

## 6. General Rules

1. **Before each step executes**, must read the corresponding SKILL.md first, do not execute from memory
2. **When skipping a step**, clearly inform the user "Skipping S2, reason: user did not require modifying project structure"
3. **Maximum rollback count**: Each step retries at most **2 times**, exceeding stops and reports to user
4. **Do not loop infinitely**: Total rollback count does not exceed **3 times**, exceeding must request user intervention
5. **When encountering uncertain situations**, prioritize asking the user, do not guess chip model, path, etc.
6. **After each Flow completes**, output a complete execution summary

---

## 7. Execution Summary Template

```
══════════════════════════════════
  ARM MCU Development Flow · Execution Summary
══════════════════════════════════
Execution Flow: Flow A (Full Development Flow)
Chip Model: GD32F303CCT6
Project Path: /path/to/project.uvprojx

Step Results:
  ✅ S1 keil-parser    · Parse complete (3 Groups, 12 files)
  ✅ S2 keil-modifier  · Added agent_log.c to Middleware Group
  ✅ S3 agent-log      · Logging system injection complete
  ❌ S4 keil-build     · Build failed → Triggered E2-A → Retry after fix
  ✅ S4 keil-build     · 2nd build succeeded (0 Error, 2 Warning)
  ✅ S5 jlink-download · Flash succeeded
  ✅ S6 jlink-rtt      · Log output normal

Total: 6 steps completed, 1 rollback, approx. 3 minutes
══════════════════════════════════
```
