import subprocess
import os
import re
import argparse


def parse_build_loghtm(log_path):
    """解析构建日志 HTML，提取 error 和 warning 数量"""
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # 查找 "X Error(s), Y Warning(s)" 模式
        match = re.search(r'(\d+)\s+Error\(s\)[,\s]+(\d+)\s+Warning\(s\)', content, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))
        # 备选：查找单独的 Error 和 Warning 计数
        errors = re.search(r'(\d+)\s+Error\(s\)', content, re.IGNORECASE)
        warnings = re.search(r'(\d+)\s+Warning\(s\)', content, re.IGNORECASE)
        err_count = int(errors.group(1)) if errors else 0
        warn_count = int(warnings.group(1)) if warnings else 0
        return err_count, warn_count
    except Exception:
        return -1, -1


def find_build_loghtm(project_dir):
    """在工程目录下查找构建日志文件 (*build_log*.htm)"""
    objects_dir = os.path.join(project_dir, "Objects")

    # 优先在 Objects 目录查找
    if os.path.exists(objects_dir):
        for f in os.listdir(objects_dir):
            if "build_log" in f and f.endswith(".htm"):
                return os.path.join(objects_dir, f)

    # 找不到则在工程目录递归搜索
    for root, _, files in os.walk(project_dir):
        for f in files:
            if "build_log" in f and f.endswith(".htm"):
                return os.path.join(root, f)
    return None


def build_keil_project(project_path, keil_path=None, rebuild=False):
    """
    Skill: 调用 Keil 命令行编译工程
    :param project_path: .uvprojx 文件路径
    :param keil_path: UV4.exe 的路径，如果不提供则尝试默认路径
    :param rebuild: True 为全编译 (-r), False 为增量编译 (-b)
    """

    if not keil_path:
        keil_path = r"D:\application\keil_v5\UV4\UV4.exe"

    if not os.path.exists(project_path):
        return {"status": "error", "message": f"Project file not found: {project_path}"}

    project_dir = os.path.dirname(os.path.abspath(project_path))
    flag = "-r" if rebuild else "-b"
    cmd = f'"{keil_path}" {flag} "{project_path}"'

    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True)

    # 检查 .build_log.htm 是否生成
    log_path = find_build_loghtm(project_dir)
    if log_path:
        errors, warnings = parse_build_loghtm(log_path)
        return {"status": "success", "log_path": log_path, "errors": errors, "warnings": warnings}
    return {"status": "failed"}


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