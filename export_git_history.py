#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤1：导出git提交历史脚本
功能：扫描所有项目，导出每个项目中包含maker的git提交历史
"""

import os
import subprocess
import platform
from datetime import datetime

# 配置
PROJECTS_DIR = "/Users/maker/Projects"
# 白名单：只统计这些项目
WHITELIST_PROJECTS = {
    "abc", "def", "ghi"
}
AUTHOR_FILTER = "maker"
GIT_HISTORY_DIR = "/Users/maker/Projects/overtime_reports/git_history"

def get_all_projects():
    """获取所有项目目录（仅白名单中的项目）"""
    items = os.listdir(PROJECTS_DIR)
    projects = []
    for item in items:
        # 只处理白名单中的项目
        if item not in WHITELIST_PROJECTS:
            continue
        item_path = os.path.join(PROJECTS_DIR, item)
        if os.path.isdir(item_path) and not item.endswith('.sh'):
            # 检查是否有 .git 仓库
            git_dir = os.path.join(item_path, '.git')
            if os.path.exists(git_dir):
                projects.append([item, item_path])
    return projects

def get_git_url(project_path):
    """获取项目的 git 远程地址"""
    try:
        cmd = ["git", "-C", project_path, "config", "--get", "remote.origin.url"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        pass
    return "未知"

def export_project_commits(project_path, project_name, output_file):
    """导出项目的git提交历史（使用原始git log格式）"""
    try:
        git_url = get_git_url(project_path)

        # 获取所有包含maker的提交记录，使用完整git log格式
        cmd = [
            "git", "-C", project_path, "log",
            "--all",
            "--pretty=format:commit %H%nAuthor: %an <%ae>%nDate:    %aI%n    %s%n",
            f"--author=.*{AUTHOR_FILTER}.*"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and result.stdout.strip():
            # 写入文件，包含元数据和原始git log输出
            with open(output_file, "w", encoding="utf-8") as f:
                # 写入元数据
                f.write(f"# Project: {project_name}\n")
                f.write(f"# Git URL: {git_url}\n")
                f.write(f"# Hostname: {platform.node().replace('.local', '')}\n")
                f.write(f"# Export Time: {datetime.now().isoformat()}\n")
                f.write(f"# Format: 完整git log 格式 (commit hash\\nAuthor: name <email>\\nDate: date\\n\\n   commit message)\n")
                f.write("# " + "=" * 76 + "\n")
                f.write(result.stdout)

            # 计算数量（通过统计"commit "开头的行数）
            commit_count = result.stdout.count("commit ")
            return commit_count
        else:
            return 0
    except Exception as e:
        print(f"获取项目 {project_name} 的提交记录失败: {e}")
        return 0

def main():
    # 获取电脑唯一标识（主机名）
    hostname = platform.node().replace('.local', '')

    print("=" * 80)
    print("步骤1: 导出Git提交历史")
    print("=" * 80)
    print(f"当前电脑标识: {hostname}")
    print(f"历史文件目录: {GIT_HISTORY_DIR}")
    print()

    # 确保git history目录存在
    os.makedirs(GIT_HISTORY_DIR, exist_ok=True)

    print("开始扫描项目...")
    projects = get_all_projects()
    print(f"找到 {len(projects)} 个项目")
    print()

    total_commits = 0
    for project_name, project_path in projects:
        print(f"处理项目: {project_name}")

        # 导出为文本文件，文件名包含项目名和电脑标识
        output_file = os.path.join(GIT_HISTORY_DIR, f"{project_name}_{hostname}.txt")

        commit_count = export_project_commits(project_path, project_name, output_file)

        if commit_count > 0:
            print(f"  -> {commit_count} 条提交记录到 {output_file}")
            total_commits += commit_count
        else:
            print(f"  项目 {project_name} 没有包含maker的提交记录")

    print()
    print("=" * 80)
    print("导出完成!")
    print("=" * 80)
    print(f"总共提交记录数: {total_commits}")
    print(f"历史文件目录: {GIT_HISTORY_DIR}")
    print()
    print("下一步: 运行步骤2（analyze_overtime.py）进行加班分析")

if __name__ == "__main__":
    main()
