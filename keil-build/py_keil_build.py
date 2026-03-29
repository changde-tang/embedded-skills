import subprocess
import os
import re
import argparse

def build_keil_project(project_path, keil_path=None, rebuild=False):
    """
    Skill: 调用 Keil 命令行编译工程
    :param project_path: .uvprojx 文件路径
    :param keil_path: UV4.exe 的路径，如果不提供则尝试默认路径
    :param rebuild: True 为全编译 (-r), False 为增量编译 (-b)
    """

    # keil的安装路径
    if not keil_path:
        keil_path = r"D:\application\keil_v5\UV4\UV4.exe"
    
    if not os.path.exists(project_path):
        return {"status": "error", "message": f"Project file not found: {project_path}"}

    log_file = os.path.join(os.path.dirname(project_path), "build_agent_log.txt")
    flag = "-r" if rebuild else "-b"
    
    # 执行命令: UV4 -b project.uvprojx -j0 -o log.txt
    # -j0 表示隐藏界面（静默模式）
    cmd = f'"{keil_path}" {flag} "{project_path}" -j0 -o "{log_file}"'
    
    print(f"Executing: {cmd}")
    # Keil 命令行总是返回非0值，所以我们不依赖 returncode，而是读日志
    subprocess.run(cmd, shell=True)

    # 读取并解析日志
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='gbk', errors='ignore') as f:
            content = f.read()
        
        # 提取 Error 和 Warning 数量
        summary_match = re.search(r"\"(.*)\" - (\d+) Error\(s\), (\d+) Warning\(s\).*", content)
        errors = int(summary_match.group(2)) if summary_match else -1
        warnings = int(summary_match.group(3)) if summary_match else -1
        
        return {
            "status": "success" if errors == 0 else "failed",
            "errors_count": errors,
            "warnings_count": warnings,
            "full_log": content[-2000:] # 只返回最后2000字，防止 Token 溢出
        }
    return {"status": "error", "message": "Log file not generated."}


def main():
    parser = argparse.ArgumentParser(description="调用 Keil UV4 命令行编译工程")
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        help="工程 .uvprojx 文件路径",
    )
    parser.add_argument(
        "-k",
        "--keil",
        default=None,
        help="UV4.exe 路径（可选，不填则使用脚本内默认路径）",
    )
    parser.add_argument(
        "-r",
        "--rebuild",
        action="store_true",
        help="全编译（传入该参数则使用 -r，否则使用 -b 增量编译）",
    )

    args = parser.parse_args()
    result = build_keil_project(
        project_path=args.project,
        keil_path=args.keil,
        rebuild=args.rebuild,
    )

    # 统一输出结果，便于后续脚本解析
    print(result)


if __name__ == "__main__":
    main()