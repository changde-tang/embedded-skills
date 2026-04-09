/**
 * @file agent_log.c
 * @brief Agent 日志系统实现
 *
 * 通过 SEGGER RTT 实现日志输出，支持多模块分类、日志级别过滤、
 * 格式化参数输出等功能。
 */

#include "agent_log.h"
#include "../Pack/ThirdParty/SEGGER_RTT/SEGGER_RTT.h"
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include "FreeRTOS.h"
#include "task.h"

/* -------------------- 模块级别状态 -------------------- */
/** @brief 当前全局日志级别，低于此级别的日志将被过滤不输出 */
static agent_log_level_t s_log_level = AGENT_LOG_DEFAULT_LEVEL;

/** @brief 颜色开关，1=启用颜色输出，0=纯文本（便于日志重定向到文件） */
static uint8_t s_color_enable = 1;

/**
 * @brief 日志级别颜色表（对应 agent_log_level_t 枚举顺序）
 *
 * 通过 ANSI 转义序列实现不同级别日志的颜色区分，
 * RTT Viewer / J-Link RTT Viewer 均支持 ANSI 颜色。
 */
static const char *g_level_colors[AGENT_LOG_LEVEL_DBG + 1] = {
    "",                                   // OFF (0): 不输出
    RTT_CTRL_TEXT_BRIGHT_MAGENTA,        // FAT (1): 亮紫红
    RTT_CTRL_TEXT_BRIGHT_RED,             // ERR (2): 亮红
    RTT_CTRL_TEXT_BRIGHT_YELLOW,          // WRN (3): 亮黄
    RTT_CTRL_TEXT_BRIGHT_WHITE,          // INF (4): 亮白（默认）
    RTT_CTRL_TEXT_BRIGHT_CYAN,           // DBG (5): 亮青
};

/**
 * @brief 模块名称表（固定6字符宽度，不足用空格补齐）
 *
 * 索引与 agent_log_module_t 枚举顺序一一对应，
 * 添加新模块时需同步在此数组中添加对应名称。
 */
static const char *g_mod_names[AGENT_LOG_MODULE_MAX] = {
    "SYS   ",   /**< 系统模块 */
    "I2C   ",   /**< I2C 通信模块 */
    "SENSOR",   /**< 传感器模块 */
    "UART  ",   /**< 串口通信模块 */
    "ADC   ",   /**< ADC 模数转换模块 */
    "GPIO  ",   /**< GPIO 输入输出模块 */
    "TIMER ",   /**< 定时器模块 */
};

/* -------------------- 弱符号接口 -------------------- */
/**
 * @brief 获取系统Tick值（弱符号实现）
 *
 * 默认返回0。用户可在外部重新实现此函数以提供真实的系统运行时间。
 * 重新实现时需保持函数签名一致，并使用 __attribute__((weak)) 或在工程中确保唯一定义。
 *
 * @return 当前系统运行时间（单位由用户自定义，建议使用毫秒）
 */
__attribute__((weak)) uint32_t agent_log_get_tick(void) {
    return 0;
}

/* -------------------- 初始化与级别控制 -------------------- */
/**
 * @brief 初始化日志系统
 *
 * 调用 SEGGER_RTT_Init() 配置 RTT 通信，并将日志级别恢复为默认值。
 * 应在系统早期初始化阶段调用。
 */
void agent_log_init(void) {
    SEGGER_RTT_Init();
    s_log_level = AGENT_LOG_DEFAULT_LEVEL;
}

/**
 * @brief 设置全局日志级别
 *
 * @param level 新的日志级别。低于该级别的日志在输出时会被直接丢弃，
 *              从而减少 RTT 带宽占用和日志噪音。
 */
void agent_log_set_level(agent_log_level_t level) {
    s_log_level = level;
}

/**
 * @brief 获取当前全局日志级别
 *
 * @return 当前生效的日志级别
 */
agent_log_level_t agent_log_get_level(void) {
    return s_log_level;
}

/* -------------------- 颜色开关 -------------------- */
/**
 * @brief 设置颜色输出开关
 *
 * @param enable 1=启用颜色（默认），0=关闭颜色输出为纯文本
 *               关闭颜色后可避免 ANSI 转义码污染日志文件
 */
void agent_log_set_color_enable(uint8_t enable) {
    s_color_enable = enable ? 1 : 0;
}

/**
 * @brief 获取当前颜色开关状态
 * @return 1=颜色启用，0=颜色关闭
 */
uint8_t agent_log_get_color_enable(void) {
    return s_color_enable;
}

/* -------------------- 内部辅助函数 -------------------- */
/**
 * @brief 将日志级别枚举转换为字符串
 *
 * @param level 日志级别枚举值
 * @return 对应的字符串标识（DBG/INF/WRN/ERR/FAT/UNK）
 */
static const char *level_to_str(agent_log_level_t level) {
    switch (level) {
        case AGENT_LOG_LEVEL_DBG: return "DBG";
        case AGENT_LOG_LEVEL_INF: return "INF";
        case AGENT_LOG_LEVEL_WRN: return "WRN";
        case AGENT_LOG_LEVEL_ERR: return "ERR";
        case AGENT_LOG_LEVEL_FAT: return "FAT";
        default: return "UNK";
    }
}

/**
 * @brief 内部日志打印函数
 *
 * 将格式化后的字符串通过 SEGGER RTT 通道输出。
 * 使用固定大小缓冲区（128字节），避免动态内存分配。
 *
 * @param fmt  格式化字符串
 * @param ...  可变参数
 */
static void log_printf(const char *fmt, ...) {
    char buf[256];
    va_list args;

    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);

    SEGGER_RTT_WriteString(AGENT_LOG_RTT_CHANNEL, buf);
}

/* -------------------- 核心日志写入 -------------------- */
/**
 * @brief 核心日志写入函数
 *
 * 根据全局日志级别和模块有效性进行过滤，然后通过 RTT 输出完整日志。
 *
 * 日志输出格式：[tick][level][module][event] message\r\n
 * - tick:   系统运行时间（由 agent_log_get_tick() 提供）
 * - level:  日志级别字符串（DBG/INF/WRN/ERR/FAT）
 * - module: 模块名称（6字符固定宽度）
 * - event:  事件标签，描述当前操作的简短标识
 * - message:格式化消息体（当 fmt 非 NULL 时输出）
 *
 * @param mod   日志所属模块，参见 agent_log_module_t
 * @param level 日志级别，参见 agent_log_level_t
 * @param event 事件标签，描述当前操作的简短标识字符串
 * @param fmt   格式化字符串（可选），为 NULL 时仅输出标签部分，不换行
 */
void agent_log_write(agent_log_module_t mod, agent_log_level_t level, const char *event, const char *fmt, ...) {
    /* 级别过滤：level 值越大级别越高，比较 level 与当前阈值 */
    if (level > s_log_level) return;

    /* 模块有效性检查，防止数组越界 */
    if (mod >= AGENT_LOG_MODULE_MAX) return;

    uint32_t tick = agent_log_get_tick();
    const char *lvl_str = level_to_str(level);
    const char *mod_str = g_mod_names[mod];

    /* 颜色前缀：根据开关和级别决定颜色码 */
    const char *color_prefix = (level != AGENT_LOG_LEVEL_OFF && s_color_enable)
                                 ? g_level_colors[level] : "";

    if (fmt != NULL) {
        /* 有参版本：输出标签 + 格式化消息体 */
        log_printf("%s[%lu][%s][%s][%s] ", color_prefix, tick, lvl_str, mod_str, event);

        char body[128];
        va_list args;
        va_start(args, fmt);
        vsnprintf(body, sizeof(body), fmt, args);
        va_end(args);

        SEGGER_RTT_WriteString(AGENT_LOG_RTT_CHANNEL, body);
    } else {
        /* 无参版本：仅输出标签，不带尾部空格 */
        log_printf("%s[%lu][%s][%s][%s]", color_prefix, tick, lvl_str, mod_str, event);
    }

    /* 尾部颜色重置 + 统一换行 */
    SEGGER_RTT_WriteString(AGENT_LOG_RTT_CHANNEL, RTT_CTRL_RESET "\r\n");
}

/* -------------------- 源码位置日志 -------------------- */
/**
 * @brief 提取路径中的文件名部分
 *
 * @param path 完整文件路径
 * @return 仅文件名部分（不含目录前缀）
 */
static const char * basename(const char *path) {
    const char *p = path + strlen(path);
    while (p > path && p[-1] != '\\' && p[-1] != '/') {
        --p;
    }
    return p;
}

/**
 * @brief 带源码位置的日志写入函数实现
 *
 * 输出格式：[file:line] [tick][level][module][event] message\r\n
 * 位置信息在最前面，便于定位日志来源。
 */
void agent_log_write_loc(agent_log_module_t mod, agent_log_level_t level,
                         const char *file, int line, const char *func,
                         const char *event, const char *fmt, ...) {
    /* 级别过滤 */
    if (level > s_log_level) return;
    if (mod >= AGENT_LOG_MODULE_MAX) return;

    const char *lvl_str = level_to_str(level);
    const char *mod_str = g_mod_names[mod];
    const char *color_prefix = (level != AGENT_LOG_LEVEL_OFF && s_color_enable)
                                ? g_level_colors[level] : "";

    /* 输出位置标签 [file:line] 前缀 */
    log_printf("%s[%s:%d] ", color_prefix, basename(file), line);

    if (fmt != NULL) {
        /* 有参版本：输出标准头部 + 格式化消息体 */
        log_printf("[%lu][%s][%s][%s] ", agent_log_get_tick(), lvl_str, mod_str, event);

        char body[128];
        va_list args;
        va_start(args, fmt);
        vsnprintf(body, sizeof(body), fmt, args);
        va_end(args);

        SEGGER_RTT_WriteString(AGENT_LOG_RTT_CHANNEL, body);
    } else {
        /* 无参版本：仅输出标准头部 */
        log_printf("[%lu][%s][%s][%s]", agent_log_get_tick(), lvl_str, mod_str, event);
    }

    SEGGER_RTT_WriteString(AGENT_LOG_RTT_CHANNEL, RTT_CTRL_RESET "\r\n");
}

/* -------------------- RTT 数据读取功能 -------------------- */
/**
 * @brief 检查RTT下行缓冲区是否有数据可读
 *
 * @return int 返回非0表示有数据可读，0表示无数据
 */
int agent_log_has_data(void)
{
    return SEGGER_RTT_HasData(AGENT_LOG_RTT_CHANNEL);
}

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
int agent_log_read(char *buffer, unsigned int buffer_size)
{
    unsigned int rx_len;

    /* 参数检查 */
    if (buffer == NULL || buffer_size == 0) {
        return 0;
    }

    /* 检查是否有数据可读 */
    if (SEGGER_RTT_HasData(AGENT_LOG_RTT_CHANNEL) == 0) {
        return 0;
    }

    /* 确保有空间存储终止符 */
    if (buffer_size == 1) {
        buffer[0] = '\0';
        return 0;
    }

    /* 读取数据，预留1字节用于终止符 */
    rx_len = SEGGER_RTT_Read(AGENT_LOG_RTT_CHANNEL, buffer, buffer_size - 1);

    if (rx_len == 0) {
        return 0;
    }

    /* 添加字符串终止符 */
    buffer[rx_len] = '\0';

    /* 去除尾部换行符（支持\r\n和\n\r） */
    while (rx_len > 0 && (buffer[rx_len-1] == '\n' || buffer[rx_len-1] == '\r')) {
        buffer[rx_len-1] = '\0';
        rx_len--;
    }

    return rx_len;
}

/* -------------------- 弱定义命令解析接口 -------------------- */
/**
 * @brief 命令解析接口（弱符号实现）
 *
 * 默认空实现。应用层可通过重新定义此函数提供命令解析能力。
 * agent_log_task() 默认会调用此函数处理接收到的命令。
 *
 * @param cmd 接收到的命令字符串（已去除尾部换行符）
 */
__attribute__((weak)) void agent_log_parse_cmd(char *cmd)
{
    (void)cmd;
    /* 默认空实现，应用层可覆盖以添加自定义命令解析 */
}

/* -------------------- 弱定义任务函数 -------------------- */
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
__attribute__((weak)) void agent_log_task(void *pvParameters)
{
    char cmd_buf[128];
    (void)pvParameters;

    agent_log_init();
    agent_log_set_color_enable(1);

    agent_log_inf(AGENT_LOG_MODULE_SYS, "=== Agent Log Task Started ===");

    /* 打印帮助信息 */
    agent_log_inf(AGENT_LOG_MODULE_SYS, "=== Available commands ===");
    agent_log_inf(AGENT_LOG_MODULE_SYS, "help - Show this help");
    agent_log_inf(AGENT_LOG_MODULE_SYS, "dbg/inf/wrn/err/fat - Log level test");
    agent_log_inf(AGENT_LOG_MODULE_SYS, "(Application commands via agent_log_parse_cmd)");

    while (1) {
        if (agent_log_has_data()) {
            int len = agent_log_read(cmd_buf, sizeof(cmd_buf) - 1);
            if (len > 0) {
                cmd_buf[len] = '\0';
                agent_log_parse_cmd(cmd_buf);
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

/**
 * @brief 创建 Agent Log 任务（弱符号实现）
 *
 * 默认使用 xTaskCreate() 创建 agent_log_task。
 * 应用层可重新定义此函数以自定义任务创建方式。
 *
 * @return pdTRUE if task was created successfully, pdFALSE otherwise
 */
__attribute__((weak)) BaseType_t agent_log_task_create(void)
{
    return xTaskCreate(
        agent_log_task,           /* 任务函数 */
        "AgentLog",               /* 任务名称 */
        1024,                     /* 堆栈大小 */
        NULL,                     /* 参数 */
        (tskIDLE_PRIORITY + 4),  /* 优先级 */
        NULL                      /* 任务句柄 */
    );
}
