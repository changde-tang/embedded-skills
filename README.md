# Embedded Skills

ARM MCU 开发全流程 Skill 集合，涵盖工程解析、编译、烧录、日志等环节。

## 目录结构

| 目录 | 说明 |
|------|------|
| `arm-tools-chain/` | 开发流程总控编排 |
| `agent-log-helper/` | RTT 结构化日志系统 |
| `keil-parser/` | .uvprojx 工程配置解析 |
| `keil-modifier/` | .uvprojx 工程文件修改 |
| `keil-build/` | Keil 工程命令行编译 |
| `jlink-download/` | J-Link 固件烧录 |
| `jlink-rtt/` | J-Link RTT 实时日志读取 |

## 环境要求

- **Python**: 3.x（keil 系列脚本仅用标准库）
- **J-Link Python**: `pip install pylink`（jlink-download / jlink-rtt 专用）
- **Keil MDK**: UV4.exe（keil-build 专用）
- **J-Link 驱动**: J-Link 硬件烧录/调试

## 子技能概览

| Skill | 职责 |
|-------|------|
| `arm-tools-chain` | 全流程总控，自动编排 S1-S6 执行顺序和错误处理 |
| `agent-log-helper` | 提供 `agent_log.c/h`，基于 RTT 的多模块分级日志 |
| `keil-parser` | 解析 .uvprojx 输出配置（宏、路径、源文件） |
| `keil-modifier` | 修改工程结构（增删文件/Group、路径管理） |
| `keil-build` | 命令行编译 Keil 工程并解析结果 |
| `jlink-download` | J-Link 烧录 .bin/.hex 到 ARM Cortex-M 芯片 |
| `jlink-rtt` | J-Link 实时读取 RTT 日志（支持自动扫描控制块） |

## 标准工作流

```
S1 解析工程 → S2 修改工程 → S3 注入日志 → S4 编译 → S5 烧录 → S6 查看日志
```

详细内容（流程选择、错误回退）请查阅各 Skill 的 `SKILL.md`。

## 版本信息

| 组件 | 要求 |
|------|------|
| Python | 3.x |
| pylink | J-Link 通信（仅 jlink-download / jlink-rtt 需要） |
| Keil MDK | v5+（UV4.exe 路径可配置） |
| J-Link | 驱动最新版 |
