# Open Bid Kit Pro

[![Validate Plugin](https://github.com/FB208/OpenBidKit_Yibiao/actions/workflows/validate.yml/badge.svg)](https://github.com/FB208/OpenBidKit_Yibiao/actions/workflows/validate.yml)

**全流程AI智能标书制作平台** — 融合六大开源标书工具精华，一站式完成招标解读、标书生成、合规检查、文档排版。

---

## 核心能力

| 能力 | 来源 | 说明 |
|------|------|------|
| AI标书生成引擎 | OpenBidKit_Yibiao | 招标解析、内容生成、知识库 |
| 21项合规检查 | BidMaster-Pro | 全维度合规审核 |
| 14步自动流水线 | BiaoShu-SKILL | 全自动标书生成流程 |
| 8行业支持+自检测 | BiaoShu-SKILL | 智能识别行业类型 |
| 专业文档排版 | docSword | 章节编号、样式、题注 |
| 多维审查 | Smart-Tender | 财政/风格/政策/文号/完整性 |
| 简洁3步工作流 | good-autobid | 需求→大纲→终稿 |
| 商机监控 | BidMaster-Pro | 自动抓取招投标公告 |
| RAG知识库 | BidMaster-Pro | 语义重排+向量检索 |
| AI去痕 | BiaoShu-SKILL | 降低内容重复率 |
| OCR扫描件解析 | BidMaster-Pro | 扫描版PDF文字提取 |
| 多模型切换 | BidMaster-Pro | 接入DeepSeek/OpenAI/Ollama等 |

## 插件结构

```
open-bid-kit/
├── .codex-plugin/plugin.json    # Codex 插件清单
├── skills/SKILL.md              # 标书制作技能（核心）
├── scripts/
│   ├── bid-agent.py             # CLI标书工具（提取/预览）
│   ├── preview-server.py        # 浏览器预览服务器
│   └── notion-sync.py           # Notion知识库同步
├── references/
│   ├── bid-workflows.md         # 标书工作流参考
│   ├── compliance-checklist.md  # 21项合规检查清单
│   └── industry-guides.md       # 8大行业标书指南
├── .env.example                 # 环境配置模板
├── .github/workflows/           # CI验证
└── assets/
```

## 安装

### 作为Codex插件安装

该插件已注册到Codex个人市场，在Codex中即可发现并安装。

### 开发安装

```bash
# 克隆插件仓库
git clone https://github.com/FB208/OpenBidKit_Yibiao.git
cd OpenBidKit_Yibiao

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env
# 编辑 .env 填入你的API密钥
```

## 使用

### 在Codex中使用

安装插件后，Codex agent 会自动加载标书制作技能。你可以直接说：

- "帮我解析这份招标文件，提取技术评分要求"
- "根据招标要求生成标书提纲"
- "对标书进行21项合规检查"
- "帮我检查投标文件的废标风险"

### 命令行工具

```bash
# 提取招标文件关键信息
python scripts/bid-agent.py extract bidding.md

# 生成HTML预览
pip install markdown
python scripts/bid-agent.py preview bidding.md

# 启动预览服务器（浏览器中查看）
python scripts/preview-server.py --port 8899

# Notion知识库同步
python scripts/notion-sync.py info
python scripts/notion-sync.py pull
python scripts/notion-sync.py push
```

### 启动易标桌面客户端

```bash
# Windows
scripts/launch-app.bat

# PowerShell
powershell -ExecutionPolicy Bypass scripts/launch-app.ps1
```

## 技术栈

- **Codex Plugin**: 提供标书制作技能
- **Python 3.8+**: CLI工具和预览服务器
- **Node.js 18+**: 易标桌面客户端
- **markdown**: HTML预览渲染
- **Notion API**: 知识库同步（可选）

## 许可证

AGPL-3.0

## 致谢

本插件基于以下优秀开源项目：

- [OpenBidKit_Yibiao (易标)](https://github.com/FB208/OpenBidKit_Yibiao) — AI标书工具箱
- [BidMaster-Pro](https://github.com/guangshu100/BidMaster-Pro) — 全流程智能招投标平台
- [BiaoShu-SKILL](https://github.com/Get00/BiaoShu-SKILL) — 通用标书生成
- [docSword](https://github.com/15831944/docSword) — 文档利器
- [Smart-Tender](https://github.com/xxi-cc/Smart-Tender) — 智能招投标系统
- [good-autobid](https://github.com/ImGoodBai/good-autobid) — AI标书生成器
