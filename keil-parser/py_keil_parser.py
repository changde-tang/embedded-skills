import xml.etree.ElementTree as ET
import argparse
import json


def _get_text(parent, tag, default=None):
    """安全获取子节点文本，不存在则返回默认值"""
    node = parent.find(tag)
    return node.text if node is not None else default


def get_project_context(uvprojx_path):
    """
    Skill: 解析工程配置，告知 Agent 宏定义、包含路径和文件列表
    """
    tree = ET.parse(uvprojx_path)
    root = tree.getroot()
    
    context = {
        "target_name": "",
        "defines": "",
        "include_paths": [],
        "source_files": [],
        "target_info": {}
    }

    # 解析宏定义和包含路径 (C/C++ 选项卡内容)
    for target in root.findall(".//Target"):
        context["target_name"] = target.find("TargetName").text
        # 查找 CAds 节点 (C/C++ Settings)
        defines = target.find(".//Cads/VariousControls/Define")
        if defines is not None: context["defines"] = defines.text

        inc_paths = target.find(".//Cads/VariousControls/IncludePath")
        if inc_paths is not None and inc_paths.text:
            context["include_paths"] = inc_paths.text.split(';')

        # 解析 TargetOption / TargetCommonOption
        target_common = target.find(".//TargetOption/TargetCommonOption")
        if target_common is not None:
            ti = {}
            # 芯片基本信息
            ti["device"] = _get_text(target_common, "Device")
            ti["vendor"] = _get_text(target_common, "Vendor")
            ti["pack_id"] = _get_text(target_common, "PackID")
            ti["pack_url"] = _get_text(target_common, "PackURL")
            ti["cpu"] = _get_text(target_common, "Cpu")
            # 文件路径
            ti["register_file"] = _get_text(target_common, "RegisterFile")
            ti["sfd_file"] = _get_text(target_common, "SFDFile")
            ti["flash_driver_dll"] = _get_text(target_common, "FlashDriverDll")
            # 编译输出
            ti["output_name"] = _get_text(target_common, "OutputName")
            ti["output_directory"] = _get_text(target_common, "OutputDirectory")
            ti["listing_path"] = _get_text(target_common, "ListingPath")
            # 烧录/镜像选项
            ti["create_executable"] = _get_text(target_common, "CreateExecutable")
            ti["create_lib"] = _get_text(target_common, "CreateLib")
            ti["create_hex_file"] = _get_text(target_common, "CreateHexFile")
            ti["hex_format_selection"] = _get_text(target_common, "HexFormatSelection")
            # 调试信息
            ti["debug_information"] = _get_text(target_common, "DebugInformation")
            ti["browse_information"] = _get_text(target_common, "BrowseInformation")
            # AfterMake 里的 UserProg1 通常是 fromelf 命令
            after_make = target_common.find("AfterMake")
            if after_make is not None:
                ti["after_make_user_prog1"] = _get_text(after_make, "UserProg1Name")

            context["target_info"] = ti

        # 查找所有源文件
        for file in target.findall(".//File"):
            file_name = file.find("FileName").text
            file_path = file.find("FilePath").text
            context["source_files"].append({"name": file_name, "path": file_path})

    return context


def main():
    """
    命令行入口：
    - 支持传入多个 .uvprojx 路径（可变参数）
    - 直接在控制台输出解析结果（JSON）
    """
    parser = argparse.ArgumentParser(description="解析 Keil .uvprojx 工程配置")
    parser.add_argument("uvprojx_paths", nargs="+", help="一个或多个 .uvprojx 路径")
    args = parser.parse_args()

    results = {}
    for uvprojx_path in args.uvprojx_paths:
        results[uvprojx_path] = get_project_context(uvprojx_path)

    print(json.dumps(results, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()