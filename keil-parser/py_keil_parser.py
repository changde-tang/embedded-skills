import xml.etree.ElementTree as ET
import argparse
import json

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
        "source_files": []
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