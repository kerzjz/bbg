 # Bloomberg Terminal Free (Open-Terminal)

[![Version](https://img.shields.io/badge/version-1.0--beta-blue)](https://github.com/kerzjz/bbg)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Win%20%7C%20Mac%20%7C%20Linux%20%7C%20Termux-lightgrey)](https://github.com/kerzjz/bbg)

Modifications Copyright (c) 2026 Ker ZJZ
These modifications are also‑licensed under the MIT‑License.
Original code: bloomberg‑terminal‑app

采用经典 Bloomberg 终端视觉风格，基于 Python [Textual](https://github.com/Textualize/textual) 框架构建，零订阅即可在命令行中实时查看全球股票、外汇、贵金属、期货及加密货币行情，并集成财经 RSS 新闻聚合。

---

## ✨ 核心特性

| 功能模块 | 说明 |
|---------|------|
| **全球资产覆盖** | 支持 A 股（沪/深）、港股、美股、外汇、贵金属（金/银/铂/钯）、期货、基金及加密货币 |
| **实时行情查询** | 接入新浪财经等公开数据源，提供实时报价（Quote）、K 线图（Chart）、买卖盘（Depth）及 Tick 数据 |
| **财经新闻聚合** | 内置 RSS 订阅引擎，支持虎嗅、华尔街见闻、新时空等主流财经媒体 |
| **经典终端体验** | 仿 Bloomberg Terminal 交互逻辑与配色方案，支持命令历史（↑↓ 键回溯）、快捷键操作 |
| **零配置启动** | 自动检测并安装依赖，首次运行无需手动配置环境 |
| **跨平台兼容** | 完美支持 Windows、macOS、Linux 及 Android Termux 环境（含 Termux 专用无依赖安装模式） |

---

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- 网络连接（用于获取实时行情数据）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/kerzjz/bbg.git
cd bbg

# 2. 运行主程序（依赖将自动安装）
python main.py
```

> **Termux 用户**：程序会自动检测 Termux 环境并跳过 `mini-racer` 等不兼容依赖，采用无依赖模式安装 `akshare`。

---

## 📖 使用指南

启动后，在底部命令行输入指令即可交互。基本语法格式为：

```
<代码> <地区> <市场> <功能>
```

### 常用命令示例

| 命令 | 说明 |
|------|------|
| `HELP` | 显示帮助信息 |
| `CLS` | 清屏 |
| `EXIT` / `QUIT` | 退出终端 |
| `AAPL US QUOTE` | 查询苹果公司美股实时报价 |
| `600000 SH DES` | 查询浦发银行（A股）基本信息 |
| `XAU GB QUOTE` | 查询现货黄金报价 |
| `USDCNY GB CHART` | 查询美元/人民币 K 线图 |
| `RSS LIST` | 查看可用 RSS 新闻源 |
| `RSS HUXIU 10` | 获取虎嗅最新 10 条新闻 |

### 支持的市场代码

| 代码 | 市场 |
|------|------|
| `US` | 美股 |
| `SH` | 上海 A 股 |
| `SZ` | 深圳 A 股 |
| `HK` | 港股 |
| `GB` | 全球外汇/贵金属 |
| `BA` | 区块链/加密货币 |

### 功能指令

| 指令 | 作用 |
|------|------|
| `DES` / `INFO` | 基本信息与描述 |
| `QUOTE` | 实时报价与买卖盘 |
| `CHART` / `GP` | ASCII 字符 K 线图 |
| `TICK` | Tick 级别数据 |
| `DEPTH` | 订单簿深度 |

---

## 🏗️ 项目结构

```
bbg/
├── main.py              # 主程序入口，Textual TUI 应用框架
├── modules/
│   ├── stocks.py        # 股票/外汇/贵金属/期货数据获取与解析
│   └── rss.py           # RSS 新闻聚合模块
├── styles.tcss          # Textual CSS 样式定义（Bloomberg 经典主题）
├── requirements.txt     # Python 依赖列表
├── LICENSE              # Apache 2.0 许可证
└── README.md            # 本文件
```

---

## 🔧 技术栈

- **[Textual](https://textual.textualize.io/)** — 现代化 Python TUI 框架，提供响应式布局与组件系统
- **[Rich](https://github.com/Textualize/rich)** — 富文本渲染、表格与 Markdown 支持
- **[AkShare](https://www.akshare.xyz/)** — 开源金融数据接口库（A 股及期货数据）
- **[Plotext](https://github.com/piccolomo/plotext)** — 终端内 ASCII 图表绘制
- **新浪财经 API** — 港股、美股、外汇及贵金属实时行情

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request。在贡献代码前，请确保：

1. 代码遵循 PEP 8 规范
2. 新增功能附带必要的错误处理与超时机制
3. 保持终端风格的视觉一致性

---

## ⚠️ 免责声明

本项目仅用于学习研究目的，所提供数据来源于公开互联网接口，不构成任何投资建议。金融市场有风险，决策需谨慎。

---

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 开源许可证。

---

**© 2026 Ker ZJZ Global Economic** — Third-party APIs & Open-Source Components belong to their respective owners.
