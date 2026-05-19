# Git Overtime Report

程序员加班代码提交记录统计工具，用于收集劳动仲裁和劳动纠纷中的加班证据。通过分析 Git 提交历史，自动统计加班时间并计算加班费。

## 功能特点

- **多项目支持**：支持同时统计多个项目的加班记录
- **多电脑数据合并**：支持导入多台电脑的 Git 历史记录，自动去重
- **加班智能计算**：按 18:00 后提交计算加班时长，按 30 分钟单位向上取整
- **多维度统计**：按项目、按天、按财年等多个维度统计加班
- **加班费计算**：根据薪资历史自动计算应得加班费
- **提交记录导出**：生成详细的提交记录报告

## 工作流程

```
┌─────────────────────┐
│ export_git_history  │  步骤1: 导出 Git 提交历史
│   (步骤一)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   git_history 目录   │  保存导出的历史文件
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  analyze_overtime   │  步骤2: 加班统计分析
│   (步骤二)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ overtime_by_project.txt            │  按项目统计报告
│ overtime_by_day.txt                 │  按天统计报告
└─────────────────────────────────────┘
```

## 脚本说明

### 1. export_git_history.py（步骤一）

**功能**：扫描本地项目目录，导出包含指定作者的 Git 提交历史。

**配置项**：
```python
PROJECTS_DIR = "/Users/maker/Projects"      # 项目根目录
WHITELIST_PROJECTS = {"abc", "def", "ghi"}   # 白名单项目
AUTHOR_FILTER = "maker"                       # 作者过滤关键字
GIT_HISTORY_DIR = "/Users/maker/Projects/overtime_reports/git_history"
```

**输出**：在 `git_history` 目录下生成 `{项目名}_{主机名}.txt` 文件。

### 2. analyze_overtime.py（步骤二）

**功能**：基于导出的历史文件进行加班统计和分析。

**主要功能**：
- 加载并合并多台电脑的 Git 历史记录
- 自动去重（按 commit hash）
- 加班时长计算（提交时间 - 18:00，按 30 分钟向上取整）
- 按项目维度统计加班天数和小时数
- 按天维度统计，并计算加班费（1.5倍时薪）
- 按财年（4.1 - 次年 3.31）汇总统计

**配置项**：
```python
GIT_HISTORY_DIR = "/Users/maker/Projects/overtime_reports/git_history"  # 历史文件目录
OUTPUT_DIR = "/Users/maker/Projects/overtime_reports"                   # 报告输出目录
OVERTIME_START_HOUR = 18                                                # 加班开始时间
WHITELIST_PROJECTS = {"abc", "def", "ghi"}                              # 白名单项目
SALARY_HISTORY = [...]                                                  # 薪资历史记录
```

**输出**：
- `overtime_by_project.txt` - 按项目维度的加班统计报告
- `overtime_by_day.txt` - 按天维度的加班统计报告（含加班费计算）

### 3. analyze_recent_commits.py

**功能**：分析最近一年的所有提交记录。

**输出**：
- `recent_commits.txt` - 最近一年提交记录明细（按时间倒序）

## 使用方法

### 步骤一：导出 Git 历史

```bash
python export_git_history.py
```

### 步骤二：分析加班统计

```bash
python analyze_overtime.py
```

### 查看提交记录

```bash
python analyze_recent_commits.py
```

## 数据格式

导出的历史文件采用以下格式：

```
# Project: abc
# Git URL: https://github.com/xxx/abc.git
# Hostname: my-macbook
# Export Time: 2025-05-19T23:00:00
# Format: 完整git log 格式 (commit hash\nAuthor: name <email>\nDate: date\n\n   commit message)
# ============================================================================
commit abc123...
Author: maker <maker@example.com>
Date:   2025-05-19T20:30:00+08:00

    修复登录bug
```

## 注意事项

1. **修改配置**：使用前请根据实际路径修改脚本中的配置项
2. **白名单机制**：只会统计白名单中的项目，可按需添加
3. **多电脑使用**：在不同电脑上运行步骤一，将生成的文件放到同一 `git_history` 目录，步骤二会自动合并去重
4. **加班定义**：默认以 18:00 作为加班开始时间，可在配置中修改
5. **时薪计算**：月薪按每月 21.75 个工作日、每天 8 小时计算

## 适用场景

- 劳动仲裁：作为加班事实的客观证据
- 劳动纠纷：提供详细的加班记录
- 个人记录：统计工作时长，了解工作状态
