#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤2：加班统计分析脚本
功能：基于git_history目录中的历史文件进行加班统计和分析
"""

import os
import platform
from datetime import datetime, timedelta
from collections import defaultdict

# 配置
GIT_HISTORY_DIR = "/Users/maker/Projects/overtime_reports/git_history"
OUTPUT_DIR = "/Users/maker/Projects/overtime_reports"
OVERTIME_START_HOUR = 18

# 白名单: 只统计这些项目
WHITELIST_PROJECTS = {
    "abc", "def", "ghi"
}

# 月薪表（按生效日期从新到旧排列）
SALARY_HISTORY = [
    {"date": "2013-04-01", "salary": 2000.00},
    {"date": "2017-08-01", "salary": 2500.00},
    {"date": "2018-04-01", "salary": 3000.00},
    {"date": "2019-04-01", "salary": 3500.00},
    {"date": "2020-04-01", "salary": 4000.00},
    {"date": "2021-08-01", "salary": 5000.00},
    {"date": "2021-04-01", "salary": 5500.00},
    {"date": "2022-04-01", "salary": 6000.00},
    {"date": "2023-04-01", "salary": 6500.00},
    {"date": "2024-04-01", "salary": 7000.00},
    {"date": "2025-04-01", "salary": 8000.00},
]

# 工作日计算 每月21.75天，每天8小时
MONTHLY_WORKING_DAYS = 21.75
DAILY_WORKING_HOURS = 8
MONTHLY_WORKING_HOURS = MONTHLY_WORKING_DAYS * DAILY_WORKING_HOURS  # 174小时/月

def get_hourly_rate(date_str):
    """根据日期获取时薪"""
    applicable_salary = None
    for salary_record in reversed(SALARY_HISTORY):
        if date_str >= salary_record["date"]:
            applicable_salary = salary_record["salary"]
            break

    if applicable_salary is None:
        applicable_salary = SALARY_HISTORY[0]["salary"]

    hourly_rate = applicable_salary / MONTHLY_WORKING_HOURS
    return hourly_rate

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
        print(f"加载文件: {filename}")

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
                elif line.startswith('# ' + '=' * 76):
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
                        elif lines[j].strip() == '' and j + i < len(lines):
                            # 空行后是提交信息
                            commit_msg = lines[j + 1].strip()
                            # 提交消息可能有4个空格缩进，去掉它
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

    print(f"去重后共收集到 {len(all_commits)} 条唯一提交记录")
    return list(all_commits.values())

def calculate_overtime_hours(commit_time_str):
    """计算加班小时数
    算法：提交时间 - 18:00, 按30分钟为单位向上取整
    """
    try:
        dt = datetime.strptime(commit_time_str.split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")
        
        overtime_start = datetime(dt.year, dt.month, dt.day, 18, 0, 0)
        time_diff = dt - overtime_start
        overtime_minutes = time_diff.total_seconds() / 60

        if overtime_minutes > 0:
            full_hours = int(overtime_minutes // 60)
            remaining_minutes = overtime_minutes % 60

            if remaining_minutes > 0:
                if remaining_minutes <= 30:
                    full_hours += 0.5
                else:
                    full_hours += 1.0

            return full_hours
    except Exception as e:
        pass
    return 0

def filter_overtime_commits(commits):
    """过滤出加班提交记录"""
    overtime_commits = []
    for commit in commits:
        overtime_hours = calculate_overtime_hours(commit["commit_date"])
        if overtime_hours > 0:
            commit["overtime_hours"] = overtime_hours
            date_str = commit["commit_date"].split()[0]
            commit["date"] = date_str
            overtime_commits.append(commit)
    return overtime_commits

def deduplicate_overtime_commits(commits):
    """去重逻辑 - 同一天如果最大加班小时数，返回去重后的唯一提交记录"""
    day_max_hours = {}
    day_last_commit = {}

    for commit in commits:
        date = commit["date"]
        hours = commit["overtime_hours"]

        if date not in day_max_hours or hours > day_max_hours[date]:
            day_max_hours[date] = hours

        if date not in day_last_commit:
            day_last_commit[date] = commit
        else:
            try:
                current_time = datetime.strptime(commit["commit_date"].split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")
                existing_time = datetime.strptime(day_last_commit[date]["commit_date"].split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")
                if current_time > existing_time:
                    day_last_commit[date] = commit
            except:
                pass

    # 只返回去重后唯一提交记录（每个日期一条）
    unique_commits = list(day_last_commit.values())

    return unique_commits, day_max_hours, day_last_commit

def generate_by_project_report(commits, day_max_hours):
    """生成按项目维度报告"""
    project_stats = defaultdict(lambda: {"days": set(), "hours": 0, "commits": [], "git_url": ""})
    project_day_max_hours= defaultdict(dict)
    project_day_last_commit = {}

    for commit in commits:
        project = commit["project"]
        date = commit["date"]
        hours = commit["overtime_hours"]

        if date not in project_day_max_hours[project] or hours > project_day_max_hours[project][date]:
            project_day_max_hours[project][date] = hours

        project_stats[project]["days"].add(date)
        project_stats[project]["commits"].append(commit)
        project_stats[project]["git_url"] = commit.get("git_url", "")

        # 记录每个项目每天的最后一天提交
        if project not in project_day_last_commit:
            project_day_last_commit[project] = {}
        if date not in project_day_last_commit[project]:
            project_day_last_commit[project][date] = {}
        else:
            try:
                current_time = datetime.strptime(commit["commit_date"].split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")
                existing_time = datetime.strptime(project_day_last_commit[project][date]["commit_date"].split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")
                if current_time > existing_time:
                    project_day_last_commit[project][date] = commit
            except:
                pass

    for project in project_stats:
        project_stats[project]["hours"] = sum(project_day_max_hours[project].values())

    total_days = len(day_max_hours)
    total_hours = sum(day_max_hours.values())

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("加班统计报告 (按项目)")
    report_lines.append("=" * 80)
    report_lines.append("【整体统计】")
    report_lines.append(f"总加班天数: {total_days} 天")
    report_lines.append(f"总加班小时数: {total_hours} 小时")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("【各项目详细统计】")
    report_lines.append("")
    report_lines.append("=" * 80)

    sorted_projects = sorted(project_stats.items(), key=lambda x: len(x[1]["days"]), reverse=True)

    for project, stats in sorted_projects:
        report_lines.append("")
        report_lines.append(f"项目名: {project}")
        report_lines.append(f"Git地址: {stats['git_url']}")
        report_lines.append(f"加班天数: {len(stats['days'])} 天")
        report_lines.append(f"加班小时数: {stats['hours']} 小时")
        report_lines.append("")
        report_lines.append("加班记录明细：")
        report_lines.append("-" * 80)

        # 按日期降序显示该项目的加班记录
        if project in project_day_last_commit:
            sorted_dates = sorted(project_day_last_commit[project].keys(), reverse=True)
            for date in sorted_dates:
                commit = project_day_last_commit[project][date]
                time_str = commit["commit_date"].split()[1][:5]
                hours = project_day_max_hours[project][date]

                report_lines.append(f"  [{date}] 提交时间: {time_str} | commitId: {commit['hash'][:12]} | 加班时长: {hours}小时 | 提交信息: {commit['commit_msg']}") 

        report_lines.append("")

    return "\n".join(report_lines)

def generate_by_day_report(day_last_commit):
    """生成按天维度的报告"""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("按天加班统计")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("-" * 80)
    report_lines.append("薪资历史记录")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append("生效日期         | 月薪(CNY)  | 年薪(CNY)   | 时薪(CNY/小时)")
    report_lines.append("-" * 80)

    for salary_record in SALARY_HISTORY:
        monthly_salary = salary_record["salary"]
        annual_salary = monthly_salary * 12
        hourly_rate = monthly_salary / MONTHLY_WORKING_HOURS
        report_lines.append(f"{salary_record['date']} | {monthly_salary:10,.2f} | {annual_salary:14,.2f} | {hourly_rate:15,.2f}")

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("加班记录详情")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    sorted_dates = sorted(day_last_commit.keys(), reverse=True)

    for date in sorted_dates:
        commit = day_last_commit[date]
        time_str = commit["commit_date"].split()[1].split("+")[0]
        hours = commit["overtime_hours"]

        hourly_rate = get_hourly_rate(date)
        overtime_pay = hours * hourly_rate * 1.5

        report_lines.append(f"{date} 最后提交项目: {commit['project']} | 提交时间: {time_str} | commitId: {commit['hash'][:12]} | 加班时长: {hours}小时 | 提交信息: {commit['commit_msg']}")

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("按财年统计（4.1-次年3.31）")
    report_lines.append("=" * 80)
    report_lines.append("")

    fiscal_year_stats = {}
    for date, commit in day_last_commit.items():
        year, month, day = map(int, date.split('-'))
        if month >= 4:
            fiscal_year = year
        else:
            fiscal_year = year - 1

        if fiscal_year not in fiscal_year_stats:
            fiscal_year_stats[fiscal_year] = {"days": 0, "hours": 0, "pay": 0}
        fiscal_year_stats[fiscal_year]["days"] += 1
        fiscal_year_stats[fiscal_year]["hours"] += commit["overtime_hours"]
        hourly_rate = get_hourly_rate(date)
        fiscal_year_stats[fiscal_year]["pay"] += commit["overtime_hours"] * hourly_rate * 1.5

    sorted_fiscal_years = sorted(fiscal_year_stats.keys(), reverse=True)
    for fiscal_year in sorted_fiscal_years:
        stats = fiscal_year_stats[fiscal_year]
        fiscal_year_end_date = f"{fiscal_year + 1}-03-31"
        year_salary = None
        for salary_record in SALARY_HISTORY:
            if fiscal_year_end_date >= salary_record["date"]:
                year_salary = salary_record["salary"]
            else:
                break
        if year_salary is None:
            year_salary = SALARY_HISTORY[0]["salary"]
        year_hourly_rate = year_salary / MONTHLY_WORKING_HOURS
        year_annual_salary = year_salary * 12

        report_lines.append(f"{fiscal_year}财年 ({fiscal_year}-04-01 至{(fiscal_year + 1)-03-31}): 加班天数 {stats['days']} 天，加班小时数 {stats['hours']} 小时，加班费 {stats['pay']:,.2f} 元")
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("薪资统计")
        report_lines.append("=" * 80)
        report_lines.append("")
        

    total_days = len(day_last_commit)
    total_hours = sum(commit["overtime_hours"] for commit in day_last_commit.values())
    total_pay = 0
    for date, commit in day_last_commit.items():
        hourly_rate = get_hourly_rate(date)
        total_pay += commit["overtime_hours"] * hourly_rate * 1.5

    report_lines.append(f"总加班天数: {total_days} 天")
    report_lines.append(f"总加班小时数: {total_hours} 小时")
    report_lines.append(f"总加班费: ¥{total_pay:.2f}")

    return "\n".join(report_lines)

def main():
    print("=" * 80)
    print("步骤2: 加班统计分析")
    print("=" * 80)
    print(f"Git历史目录: {GIT_HISTORY_DIR}")
    print()

    # 加载Git历史文件
    all_commits = load_git_history_files()
    print(f"共收集到 {len(all_commits)} 条提交记录")
    print()

    print("过滤加班提交...")
    overtime_commits = filter_overtime_commits(all_commits)
    print(f"找到 {len(overtime_commits)} 条加班提交记录")

    print("去重统计...")
    overtime_commits, day_max_hours, day_last_commit = deduplicate_overtime_commits(overtime_commits)
    print()

    # 生成报告...
    by_project_report = generate_by_project_report(overtime_commits, day_max_hours)
    by_day_report = generate_by_day_report(day_last_commit)

    # 写入报告文件（不包含主机名，因为统计的是所有电脑的数据）
    report_by_project_path = os.path.join(OUTPUT_DIR, "overtime_by_project.txt")
    report_by_day_path = os.path.join(OUTPUT_DIR, "overtime_by_day.txt")

    with open(report_by_project_path, 'w', encoding='utf-8') as f:
        f.write(by_project_report)

    with open(report_by_day_path, 'w', encoding='utf-8') as f:
        f.write(by_day_report)

    print()
    print("=" * 80)
    print("分析完成!")
    print("=" * 80)
    print(f"报告已生成：")
    print(f"  - {report_by_project_path}")
    print(f"  - {report_by_day_path}")

if __name__ == "__main__":
    main()
