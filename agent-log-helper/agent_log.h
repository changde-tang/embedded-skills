/**
 * @file agent_log.h
 * @brief Agent 日志系统头文件
 *
 * 提供统一的日志接口，支持多模块、日志级别控制、可变参数格式化输出、
 * 不同级别自动配色。通过 SEGGER RTT 通道输出日志信息。
 *
 * =============================================================
 * 使用说明：
 *
 * 1. 初始化：
 *    agent_log_init();  // 在系统启动时调用，初始化 RTT
 *
 * 2. 设置日志级别：
 *    agent_log_set_level(AGENT_LOG_LEVEL_INF);  // 仅输出 INF 及以上级别
 *
 * 3. 颜色开关（默认开启）：
 *    agent_log_set_color_enable(0);  // 关闭颜色，便于日志重定向到文件
 *    agent_log_set_color_enable(1);  // 重新开启颜色
 *
 * 4. 使用无参日志宏（仅记录事件）：
 *    agent_log_inf(AGENT_LOG_MODULE_SYS, "Task started");
 *    agent_log_dbg(AGENT_LOG_MODULE_I2C, "Bus idle");
 *    agent_log_err(AGENT_LOG_MODULE_UART, "Timeout");
 *
 * 5. 使用有参日志宏（支持格式化输出）：
 *    agent_log_inf_fmt(AGENT_LOG_MODULE_SENSOR, "Value=%d", value);
 *    agent_log_err_fmt(AGENT_LOG_MODULE_GPIO, "Pin%d error", pin);
 *
 * =============================================================
 * 添加新模块步骤：
 * 1. 在 agent_log_module_t 枚举中添加新模块（位于 MAX 之前）
 * 2. 在 agent_log.c 的 g_mod_names[] 数组中添加名称（固定6字符）
 * 3. 枚举顺序必须与数组顺序一致
 * =============================================================
 */

#ifndef AGENT_LOG_H
#define AGENT_LOG_H

#include <stdint.h>
#include "FreeRTOS.h"
#include "task.h"

// ====================== RTT 配置 ======================
#define AGENT_LOG_RTT_CHANNEL     0

// ====================== 模块列表 ======================

/* -------------------- 模块添加说明 --------------------
 * 当需要添加新模块时，按以下步骤操作：
 * 1. 在 agent_log_config.h 的 agent_log_module_t 枚举中添加新模块（位于 MAX 之前）
 * 2. 在 agent_log.c 的 g_mod_names[] 数组中添加对应的名称字符串
 *    - 必须固定 6 字符宽度，不足用空格补齐
 *    - 位于数组中 MAX 之前的对应位置
 * 3. 枚举顺序必须与数组顺序一致
 * 示例：添加 AGENT_LOG_MODULE_SPI
 *   // agent_log_config.h 中:
 *   typedef enum {
 *       ...
 *       AGENT_LOG_MODULE_SPI,
 *       AGENT_LOG_MODULE_MAX
 *   } agent_log_module_t;
 *
 *   // agent_log.c 中 g_mod_names[] 添加:
 *   "SPI   ",
 * ------------------------------------------------------- */

typedef enum {
    AGENT_LOG_MODULE_SYS,      // 系统
    AGENT_LOG_MODULE_I2C,      // I2C 通信
    AGENT_LOG_MODULE_SENSOR,   // 传感器
    AGENT_LOG_MODULE_UART,     // 串口
    AGENT_LOG_MODULE_ADC,      // ADC
    AGENT_LOG_MODULE_GPIO,     // GPIO
    AGENT_LOG_MODULE_TIMER,    // 定时器
    AGENT_LOG_MODULE_MAX
} agent_log_module_t;

// ====================== 日志级别 ======================
typedef enum {
    AGENT_LOG_LEVEL_OFF = 0,
    AGENT_LOG_LEVEL_FAT,    /* 最高优先级，始终显示 */
    AGENT_LOG_LEVEL_ERR,
    AGENT_LOG_LEVEL_WRN,
    AGENT_LOG_LEVEL_INF,
    AGENT_LOG_LEVEL_DBG     /* 最低优先级，最详细 */
} agent_log_level_t;

// ====================== 级别名称（固定3字符） ======================
#define AGENT_LOG_LVL_DBG  "DBG"
#define AGENT_LOG_LVL_INF  "INF"
#define AGENT_LOG_LVL_WRN  "WRN"
#define AGENT_LOG_LVL_ERR  "ERR"
#define AGENT_LOG_LVL_FAT  "FAT"

// ====================== 默认配置 ======================
#define AGENT_LOG_DEFAULT_LEVEL  AGENT_LOG_LEVEL_DBG


/**
 * @brief 初始化日志系统
 *
 * 调用 SEGGER_RTT_Init() 初始化 RTT 通信，
 * 并将日志级别恢复为默认级别 AGENT_LOG_DEFAULT_LEVEL。
 * 应在系统初始化阶段调用。
 */
void agent_log_init(void);

/**
 * @brief 设置全局日志级别
 * @param level 日志级别，低于该级别的日志将被过滤
 *
 * 例如设置为 AGENT_LOG_LEVEL_WRN 时，DBG 和 INF 级别日志不会输出。
 */
void agent_log_set_level(agent_log_level_t level);

/**
 * @brief 获取当前全局日志级别
 * @return 当前日志级别
 */
agent_log_level_t agent_log_get_level(void);

/* -------------------- 颜色控制 -------------------- */

/**
 * @brief 设置颜色输出开关
 *
 * 启用颜色后，不同日志级别在 J-Link RTT Viewer 中会以不同颜色显示：
 * - DBG: 亮青色
 * - INF: 亮白色（默认）
 * - WRN: 亮黄色
 * - ERR: 亮红色
 * - FAT: 亮紫红色
 *
 * 关闭颜色后可避免 ANSI 转义码污染日志文件（适用于日志重定向场景）。
 *
 * @param enable 1=启用颜色（默认），0=关闭颜色输出为纯文本
 */
void agent_log_set_color_enable(uint8_t enable);

/**
 * @brief 获取当前颜色开关状态
 * @return 1=颜色启用，0=颜色关闭
 */
uint8_t agent_log_get_color_enable(void);

/**
 * @brief 核心日志写入函数
 *
 * 根据模块、级别过滤日志，并通过 RTT 输出。
 * 支持带事件标签的格式化输出。
 *
 * 日志格式：[tick][level][module][event] message\r\n
 *
 * @param mod   日志所属模块，参见 agent_log_module_t
 * @param level 日志级别，参见 agent_log_level_t
 * @param event 事件标签，描述当前操作的简短标识
 * @param fmt   格式化字符串（可选），为 NULL 时仅输出标签部分
 */
void agent_log_write(agent_log_module_t mod, agent_log_level_t level, const char *event, const char *fmt, ...);

/**
 * @brief 带源码位置的日志写入函数
 *
 * 将日志输出到 RTT，格式：[file:line] [tick][level][module][event] message\r\n
 *
 * @param mod   日志所属模块
 * @param level 日志级别
 * @param file  源码文件名（建议用 __FILE__ 传入，会自动提取文件名部分）
 * @param line  源码行号（用 __LINE__ 传入）
 * @param func  函数名（用 __FUNCTION__ 传入）
 * @param event 事件标签
 * @param fmt   格式化字符串（可选），为 NULL 时仅输出标签部分
 */
void agent_log_write_loc(agent_log_module_t mod, agent_log_level_t level,
                         const char *file, int line, const char *func,
                         const char *event, const char *fmt, ...);

/**
 * @brief 检查RTT下行缓冲区是否有数据可读
 *
 * @return int 返回非0表示有数据可读，0表示无数据
 */
int agent_log_has_data(void);

/**
 * @brief 从RTT下行缓冲区读取数据
 *
 * 封装RTT下行缓冲区的数据检查、读取和预处理功能，包括：
 * 1. 检查缓冲区是否有数据
 * 2. 读取数据到用户缓冲区
 * 3. 自动添加字符串终止符('\0')
 * 4. 自动去除尾部换行符('\n'和'\r')
 *
 * @param buffer 用户提供的缓冲区指针，用于存储读取的数据
 * @param buffer_size 缓冲区大小（字节数），函数会确保不越界
 * @return int 实际读取的字节数（不包括终止符），返回0表示无数据或读取失败
 *
 * @note 缓冲区大小应至少为1，以确保能存储终止符
 * @note 函数会预留1字节用于存储字符串终止符，因此最大可读取 buffer_size-1 字节
 * @note 如果读取的数据以换行符结尾，换行符会被移除
 */
int agent_log_read(char *buffer, unsigned int buffer_size);

/* ==================== 任务相关接口 ==================== */

/**
 * @brief Agent Log 任务（弱符号实现）
 *
 * 默认的 RTT 命令接收任务。功能包括：
 * - 初始化日志系统
 * - 循环读取 RTT 下行数据
 * - 调用 agent_log_parse_cmd() 解析并执行命令
 *
 * 应用层可重新定义此函数以自定义行为。
 *
 * @param pvParameters 任务参数（未使用）
 */
void agent_log_task(void *pvParameters);

/**
 * @brief 创建 Agent Log 任务（弱符号实现）
 *
 * 默认使用 xTaskCreate() 创建 agent_log_task。
 * 应用层可重新定义此函数以自定义任务创建方式。
 *
 * @return pdTRUE if task was created successfully, pdFALSE otherwise
 */
BaseType_t agent_log_task_create(void);

/**
 * @brief 命令解析接口（弱符号实现）
 *
 * 默认空实现。应用层可通过重新定义此函数提供命令解析能力。
 * agent_log_task() 默认会调用此函数处理接收到的命令。
 *
 * @param cmd 接收到的命令字符串（已去除尾部换行符）
 */
void agent_log_parse_cmd(char *cmd);

/* ==================== 无参版本宏 ====================
 * 适用于仅需记录事件发生，无需附加数据的情况。
 * 例如：agent_log_inf(AGENT_LOG_SYS, "Task started");
 * 输出示例：[1234][SYS][INF][Task started]
 * ==================================================== */

/** @brief 信息级别日志（无参版本） */
#define agent_log_inf(mod, event) \
    agent_log_write(mod, AGENT_LOG_LEVEL_INF, event, NULL)

/** @brief 调试级别日志（无参版本） */
#define agent_log_dbg(mod, event) \
    agent_log_write(mod, AGENT_LOG_LEVEL_DBG, event, NULL)

/** @brief 警告级别日志（无参版本） */
#define agent_log_wrn(mod, event) \
    agent_log_write(mod, AGENT_LOG_LEVEL_WRN, event, NULL)

/** @brief 错误级别日志（无参版本） */
#define agent_log_err(mod, event) \
    agent_log_write(mod, AGENT_LOG_LEVEL_ERR, event, NULL)

/** @brief 致命错误级别日志（无参版本） */
#define agent_log_fat(mod, event) \
    agent_log_write(mod, AGENT_LOG_LEVEL_FAT, event, NULL)

/* ==================== 有参版本宏 ====================
 * 适用于需要输出格式化数据的场景，支持类似 printf 的可变参数。
 * 例如：agent_log_inf_fmt(AGENT_LOG_SENSOR, "ADC%d", "val=%d", 2, 1234);
 * 输出示例：[1234][SYS][INF][ADC2] val=1234
 * ==================================================== */

/** @brief 信息级别日志（有参版本，支持格式化） */
#define agent_log_inf_fmt(mod, event, ...) \
    agent_log_write(mod, AGENT_LOG_LEVEL_INF, event, ##__VA_ARGS__)

/** @brief 调试级别日志（有参版本，支持格式化） */
#define agent_log_dbg_fmt(mod, event, ...) \
    agent_log_write(mod, AGENT_LOG_LEVEL_DBG, event, ##__VA_ARGS__)

/** @brief 警告级别日志（有参版本，支持格式化） */
#define agent_log_wrn_fmt(mod, event, ...) \
    agent_log_write(mod, AGENT_LOG_LEVEL_WRN, event, ##__VA_ARGS__)

/** @brief 错误级别日志（有参版本，支持格式化） */
#define agent_log_err_fmt(mod, event, ...) \
    agent_log_write(mod, AGENT_LOG_LEVEL_ERR, event, ##__VA_ARGS__)

/** @brief 致命错误级别日志（有参版本，支持格式化） */
#define agent_log_fat_fmt(mod, event, ...) \
    agent_log_write(mod, AGENT_LOG_LEVEL_FAT, event, ##__VA_ARGS__)

/* ==================== 带源码位置的版本宏 ====================
 * 输出格式：[file:line] [tick][level][module][event] message\r\n
 * 位置信息放在最前面，便于快速定位日志来源。
 * =========================================================== */

/** @brief 信息级别日志（带源码位置，无参版本） */
#define agent_log_inf_loc(mod, event) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_INF, __FILE__, __LINE__, __FUNCTION__, event, NULL)

/** @brief 调试级别日志（带源码位置，无参版本） */
#define agent_log_dbg_loc(mod, event) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_DBG, __FILE__, __LINE__, __FUNCTION__, event, NULL)

/** @brief 警告级别日志（带源码位置，无参版本） */
#define agent_log_wrn_loc(mod, event) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_WRN, __FILE__, __LINE__, __FUNCTION__, event, NULL)

/** @brief 错误级别日志（带源码位置，无参版本） */
#define agent_log_err_loc(mod, event) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_ERR, __FILE__, __LINE__, __FUNCTION__, event, NULL)

/** @brief 致命错误级别日志（带源码位置，无参版本） */
#define agent_log_fat_loc(mod, event) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_FAT, __FILE__, __LINE__, __FUNCTION__, event, NULL)

/** @brief 信息级别日志（带源码位置，有参版本） */
#define agent_log_inf_loc_fmt(mod, event, ...) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_INF, __FILE__, __LINE__, __FUNCTION__, event, ##__VA_ARGS__)

/** @brief 调试级别日志（带源码位置，有参版本） */
#define agent_log_dbg_loc_fmt(mod, event, ...) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_DBG, __FILE__, __LINE__, __FUNCTION__, event, ##__VA_ARGS__)

/** @brief 警告级别日志（带源码位置，有参版本） */
#define agent_log_wrn_loc_fmt(mod, event, ...) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_WRN, __FILE__, __LINE__, __FUNCTION__, event, ##__VA_ARGS__)

/** @brief 错误级别日志（带源码位置，有参版本） */
#define agent_log_err_loc_fmt(mod, event, ...) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_ERR, __FILE__, __LINE__, __FUNCTION__, event, ##__VA_ARGS__)

/** @brief 致命错误级别日志（带源码位置，有参版本） */
#define agent_log_fat_loc_fmt(mod, event, ...) \
    agent_log_write_loc(mod, AGENT_LOG_LEVEL_FAT, __FILE__, __LINE__, __FUNCTION__, event, ##__VA_ARGS__)

#endif /* AGENT_LOG_H */
