#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析最近一年提交记录脚本
功能：从git_history记录中统计最近一年的提交记录，去重后按时间倒序
"""

import os
from datetime import datetime, timedelta

# 配置
GIT_HISTORY_DIR = "/Users/maker/Projects/overtime_reports/git_history"
OUTPUT_DIR = "/Users/maker/Projects/overtime_reports"
WHITELIST_PROJECTS = {
    "abc", "def", "ghi"
}

def load_git_history_files():
    """加载git_history目录中的所有历史文件，支持多台电脑数据合并和去重"""
    all_commits = {}
    # 使用字典以commit hash为key进行去重

    if not os.path.exists(GIT_HISTORY_DIR):
        print(f"错误: Git历史目录不存在: {GIT_HISTORY_DIR}")
        return list(all_commits.values())

    files = os.listdir(GIT_HISTORY_DIR)
    txt_files = [f for f in files if f.endswith('.txt')]

    print(f"找到 {len(txt_files)} 个历史文件")

    for filename in txt_files:
        filepath = os.path.join(GIT_HISTORY_DIR, filename)
        print(f"读取文件: {filename}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 解析元数据
            project_name = None
            git_url = "未知"
            hostname = None

            for line in lines:
                if line.startswith('# Project:'):
                    project_name = line.split(':', 1)[1].strip()
                elif line.startswith('# Git URL:'):
                    git_url = line.split(':', 1)[1].strip()
                elif line.startswith('# Hostname:'):
                    hostname = line.split(':', 1)[1].strip()
                elif line.startswith('# ' + "=" * 76):
                    break  # 元数据结束

            # 检查项目是否在白名单中
            if project_name not in WHITELIST_PROJECTS:
                print(f"    跳过项目: {project_name} (不在白名单中)")
                continue

            # 解析提交记录, 使用commit hash去重
            # 原始git log格式: commit hash\nAuthor: name <email>\nDate: date\n   commit message
            duplicate_count = 0
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # 跳过空行和注释行
                if not line or line.startswith('#'):
                    i += 1
                    continue

                # 解析完整git log格式
                if line.startswith('commit '):
                    commit_hash = line[7:].strip()

                    # 重置Author行
                    author_name = ""
                    author_email = ""
                    commit_date = ""
                    commit_msg = ""

                    j = i + 1
                    while j < len(lines):
                        if lines[j].strip().startswith('Author:'):
                            author_line = lines[j].strip()[8:].strip()  # 去掉"Author: "
                            # 解析 "name <email>" 格式
                            if '<' in author_line and '>' in author_line:
                                author_name = author_line[:author_line.index('<')].strip()
                                author_email = author_line[author_line.index('<')+1:author_line.index('>')].strip()
                            else:
                                author_name = author_line
                        elif lines[j].strip().startswith('Date:'):
                            commit_date = lines[j].strip()[6:].strip()  # 去掉"Date: "
                        elif lines[j] == '' and j + i < len(lines):
                            # 空行后是提交信息
                            commit_msg = lines[j + 1].strip()
                            # 如果消息可能有"空格前缀"，去掉它
                            if commit_msg.startswith('    '):
                                commit_msg = commit_msg[4:]
                            break
                        j += 1

                    if commit_hash and author_name and commit_date:
                        commit_data = {
                            "hash": commit_hash,
                            "author_name": author_name,
                            "author_email": author_email,
                            "commit_date": commit_date,
                            "commit_msg": commit_msg,
                            "project": project_name,
                            "git_url": git_url,
                            "hostname": hostname
                        }

                        # 使用commit hash作为唯一标识进行去重
                        if commit_hash not in all_commits:
                            all_commits[commit_hash] = commit_data
                        else:
                            duplicate_count += 1

                    i = j + 1  # 跳过提交信息
                else:
                    i += 1

            if duplicate_count > 0:
                print(f"    发现 {duplicate_count} 条重复提交（已去重）")

        except Exception as e:
            print(f"读取文件 {filename} 失败: {e}")

    print(f"去重后共收到 {len(all_commits)} 条唯一提交记录")
    return list(all_commits.values())

def filter_recent_commits(commits, days=365):
    """过滤出最近N天的提交记录"""
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_commits = []

    for commit in commits:
        try:
            # 解析提交日期
            commit_date_str = commit["commit_date"].split('+')[0].strip()
            commit_date = datetime.strptime(commit_date_str, "%Y-%m-%d %H:%M:%S")

            if commit_date >= cutoff_date:
                recent_commits.append(commit)
        except Exception as e:
            pass

    return recent_commits

def generate_report(commits):
    """生成最近一年提交记录报告"""
    # 按提交时间排序
    sorted_commits = sorted(commits, key=lambda x: x["commit_date"], reverse=True)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("最近一年提交记录概览")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"提交记录总数: {len(sorted_commits)}")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("提交记录明细（按时间倒序）")
    report_lines.append("")
    
    for commit in sorted_commits:
        date_str = commit["commit_date"].split()[0]
        time_str = commit["commit_date"].split()[1].split('+')[0]
        
        report_lines.append(f"{date_str} {time_str} | {commit['project']} | {commit['hash'][:12]} | {commit['commit_msg']}")
        
    report_lines.append("")
    return "\n".join(report_lines)

def main():
    print("=" * 80)
    print("分析最近一年的提交记录")
    print("=" * 80)
    print(f"Git历史目录: {GIT_HISTORY_DIR}")
    print()

    # 加载Git历史文件
    all_commits = load_git_history_files()
    print(f"共收集到 {len(all_commits)} 条提交记录")
    print()

    print("过滤最近一年的提交记录...")
    recent_commits = filter_recent_commits(all_commits, days=365)
    print(f"找到 {len(recent_commits)} 条最近一年的提交记录")
    print()

    # 生成报告
    report = generate_report(recent_commits)

    # 写入报告文件
    report_path = os.path.join(OUTPUT_DIR, "recent_commits.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print()
    print("=" * 80)
    print("分析完成!")
    print("=" * 80)
    print(f"报告已生成: {report_path}")

if __name__ == "__main__":
    main()
