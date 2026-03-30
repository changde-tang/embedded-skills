import xml.etree.ElementTree as ET
import argparse
import shutil
import os

# FileType 映射
EXT_TO_FILETYPE = {
    ".c":   "1",
    ".cpp": "1",
    ".s":   "2",
    ".asm": "2",
    ".lib": "3",
    ".txt": "4",
    ".h":   "5",
    ".hpp": "5",
    ".inc": "5",
}

def get_filetype(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return EXT_TO_FILETYPE.get(ext, "1")


def backup(uvprojx_path):
    backup_path = uvprojx_path + ".bak"
    shutil.copy2(uvprojx_path, backup_path)
    print(f"[Backup] {backup_path}")


def indent_xml(elem, level=0):
    """给 ElementTree 加缩进，让写回的 XML 人类可读"""
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent
    if not level:
        elem.tail = "\n"


# ──────────────────────────────────────────────
# 核心操作
# ──────────────────────────────────────────────

def cmd_list(args):
    """列出工程中所有 Group 和文件"""
    tree = ET.parse(args.project)
    root = tree.getroot()

    for target in root.findall(".//Target"):
        target_name = target.find("TargetName").text
        print(f"\n[Target] {target_name}")
        for group in target.findall(".//Group"):
            group_name = group.find("GroupName").text
            print(f"  [Group] {group_name}")
            for f in group.findall("Files/File"):
                fname = f.find("FileName").text
                fpath = f.find("FilePath").text
                print(f"    - {fname}  ({fpath})")


def cmd_add(args):
    """添加文件到指定 Group（Group 不存在则自动创建）"""
    tree = ET.parse(args.project)
    root = tree.getroot()

    for target in root.findall(".//Target"):
        groups_node = target.find("Groups")
        if groups_node is None:
            groups_node = ET.SubElement(target, "Groups")

        # 查找或创建 Group
        group_node = None
        for g in groups_node.findall("Group"):
            if g.find("GroupName").text == args.group:
                group_node = g
                break

        if group_node is None:
            print(f"[Info] Group '{args.group}' not found, creating it.")
            group_node = ET.SubElement(groups_node, "Group")
            gname_node = ET.SubElement(group_node, "GroupName")
            gname_node.text = args.group

        # 确保有 Files 节点
        files_node = group_node.find("Files")
        if files_node is None:
            files_node = ET.SubElement(group_node, "Files")

        # 检查文件是否已存在
        file_name = os.path.basename(args.file)
        for existing in files_node.findall("File"):
            if existing.find("FilePath").text == args.file:
                print(f"[Skip] '{args.file}' already exists in group '{args.group}'.")
                return

        # 添加文件节点
        file_node = ET.SubElement(files_node, "File")
        fn_node = ET.SubElement(file_node, "FileName")
        fn_node.text = file_name
        ft_node = ET.SubElement(file_node, "FileType")
        ft_node.text = get_filetype(args.file)
        fp_node = ET.SubElement(file_node, "FilePath")
        fp_node.text = args.file

        print(f"[Added] '{args.file}' -> Group '{args.group}'")

    backup(args.project)
    indent_xml(root)
    tree.write(args.project, encoding="utf-8", xml_declaration=True)
    print("[Saved]", args.project)


def cmd_remove(args):
    """从工程中移除指定文件（按 FilePath 匹配）"""
    tree = ET.parse(args.project)
    root = tree.getroot()
    removed = False

    for files_node in root.findall(".//Files"):
        for file_node in files_node.findall("File"):
            fp = file_node.find("FilePath")
            if fp is not None and fp.text == args.file:
                files_node.remove(file_node)
                print(f"[Removed] '{args.file}'")
                removed = True

    if not removed:
        print(f"[Not found] '{args.file}' not found in project.")
        return

    backup(args.project)
    indent_xml(root)
    tree.write(args.project, encoding="utf-8", xml_declaration=True)
    print("[Saved]", args.project)


def cmd_add_group(args):
    """新建一个空 Group"""
    tree = ET.parse(args.project)
    root = tree.getroot()

    for target in root.findall(".//Target"):
        groups_node = target.find("Groups")
        if groups_node is None:
            groups_node = ET.SubElement(target, "Groups")

        for g in groups_node.findall("Group"):
            if g.find("GroupName").text == args.group:
                print(f"[Skip] Group '{args.group}' already exists.")
                return

        group_node = ET.SubElement(groups_node, "Group")
        gname_node = ET.SubElement(group_node, "GroupName")
        gname_node.text = args.group
        print(f"[Created] Group '{args.group}'")

    backup(args.project)
    indent_xml(root)
    tree.write(args.project, encoding="utf-8", xml_declaration=True)
    print("[Saved]", args.project)


def cmd_remove_group(args):
    """删除一个 Group（含其下所有文件）"""
    tree = ET.parse(args.project)
    root = tree.getroot()
    removed = False

    for target in root.findall(".//Target"):
        groups_node = target.find("Groups")
        if groups_node is None:
            continue
        for g in groups_node.findall("Group"):
            if g.find("GroupName").text == args.group:
                groups_node.remove(g)
                print(f"[Removed] Group '{args.group}' and all its files.")
                removed = True

    if not removed:
        print(f"[Not found] Group '{args.group}' not found.")
        return

    backup(args.project)
    indent_xml(root)
    tree.write(args.project, encoding="utf-8", xml_declaration=True)
    print("[Saved]", args.project)


def _get_include_path(tree):
    """获取 IncludePath 节点列表"""
    paths = []
    for vc in tree.findall(".//VariousControls"):
        ip = vc.find("IncludePath")
        if ip is not None and ip.text:
            paths.extend(ip.text.split(";"))
    return paths


def _set_include_path(tree, paths):
    """设置 IncludePath"""
    for vc in tree.findall(".//VariousControls"):
        ip = vc.find("IncludePath")
        if ip is not None:
            ip.text = ";".join(paths)
            return


def cmd_add_include_path(args):
    """添加 include 路径"""
    tree = ET.parse(args.project)
    root = tree.getroot()

    paths = _get_include_path(tree)
    original_count = len(paths)

    for new_path in args.path:
        if new_path not in paths:
            paths.append(new_path)
            print(f"[Added] Include path: '{new_path}'")
        else:
            print(f"[Skip] Include path already exists: '{new_path}'")

    if len(paths) == original_count:
        print("[Info] No changes made.")
        return

    _set_include_path(tree, paths)
    backup(args.project)
    indent_xml(root)
    tree.write(args.project, encoding="utf-8", xml_declaration=True)
    print("[Saved]", args.project)


def cmd_remove_include_path(args):
    """移除 include 路径"""
    tree = ET.parse(args.project)
    root = tree.getroot()

    paths = _get_include_path(tree)
    original_count = len(paths)

    for path_to_remove in args.path:
        if path_to_remove in paths:
            paths.remove(path_to_remove)
            print(f"[Removed] Include path: '{path_to_remove}'")
        else:
            print(f"[Not found] Include path: '{path_to_remove}'")

    if len(paths) == original_count:
        print("[Info] No changes made.")
        return

    _set_include_path(tree, paths)
    backup(args.project)
    indent_xml(root)
    tree.write(args.project, encoding="utf-8", xml_declaration=True)
    print("[Saved]", args.project)


def cmd_list_include_paths(args):
    """列出所有 include 路径"""
    tree = ET.parse(args.project)
    root = tree.getroot()

    paths = _get_include_path(tree)
    if paths:
        print("\n[Include Paths]")
        for p in paths:
            print(f"  - {p}")
    else:
        print("[Info] No include paths found.")


# ──────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Keil .uvprojx 工程文件修改工具",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-p", "--project", required=True, help=".uvprojx 文件路径")

    sub = parser.add_subparsers(dest="command", required=True)

    # list
    sub.add_parser("list", help="列出所有 Group 和文件")

    # add
    p_add = sub.add_parser("add", help="添加文件到 Group")
    p_add.add_argument("-f", "--file", required=True, help="文件路径（建议相对路径）")
    p_add.add_argument("-g", "--group", required=True, help="目标 Group 名称")

    # remove
    p_rm = sub.add_parser("remove", help="从工程中移除文件")
    p_rm.add_argument("-f", "--file", required=True, help="要移除的文件路径（与工程中 FilePath 一致）")

    # add-group
    p_ag = sub.add_parser("add-group", help="新建空 Group")
    p_ag.add_argument("-g", "--group", required=True, help="新 Group 名称")

    # remove-group
    p_rg = sub.add_parser("remove-group", help="删除 Group（含其下所有文件）")
    p_rg.add_argument("-g", "--group", required=True, help="要删除的 Group 名称")

    # list-include-paths
    sub.add_parser("list-include-paths", help="列出所有 include 路径")

    # add-include-path
    p_aip = sub.add_parser("add-include-path", help="添加 include 路径")
    p_aip.add_argument("-i", "--path", required=True, nargs="+", help="要添加的路径（可多个）")

    # remove-include-path
    p_rip = sub.add_parser("remove-include-path", help="移除 include 路径")
    p_rip.add_argument("-i", "--path", required=True, nargs="+", help="要移除的路径（可多个）")

    dispatch = {
        "list":                  cmd_list,
        "add":                   cmd_add,
        "remove":                cmd_remove,
        "add-group":             cmd_add_group,
        "remove-group":          cmd_remove_group,
        "list-include-paths":    cmd_list_include_paths,
        "add-include-path":      cmd_add_include_path,
        "remove-include-path":   cmd_remove_include_path,
    }

    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()