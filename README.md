# code-walkthrough-ppt-video

把已有 IT 系统源码转换为可直接交付的产品讲解 HTML PPT 或中文讲解视频。技能启动后会先要求用户选择一种输出形式，再进入对应流水线，不要求目标系统能够成功运行。

## 两种输出

| 模式 | 主要产物 | 适合场景 | 核心规格 |
|---|---|---|---|
| HTML PPT | HTML deck、图片、页面蓝图、源码追溯表 | 汇报、评审、客户演示、交付文档 | 1920x1080，纯白咨询风格，可键盘放映 |
| 中文视频 | MP4、SRT、Markdown 解说稿 | 产品传播、异步培训、项目介绍 | 1920x1080、30fps、硬字幕、最长 10 分钟 |

PPT 模式使用浅色界面重绘、咨询版式与可测量的截图标注；视频模式使用 Remotion、微软云扬中文配音、分镜动画与分块渲染。两种模式都要求技术结论能够追溯到源码，并使用仿真数据保护敏感信息。

## 对话启动方式

安装后可以直接提出：

```text
请基于这个项目源码做一份产品讲解材料，源码在 D:\projects\demo。
```

技能首先询问：

```text
请选择本次输出类型：
1. HTML PPT
2. 中文讲解视频
```

确认后才会扫描源码。若需要两种产物，请指定先后顺序，技能会先完成一种，再复用勘察结果制作另一种。

## 安装到 Codex

从 GitHub 直接克隆到个人技能目录：

```bash
git clone https://github.com/sharptoolbox/code-walkthrough-ppt-video.git ~/.codex/skills/code-walkthrough-ppt-video
```

Windows PowerShell 本地安装：

```powershell
Copy-Item -Recurse -Force .\code-walkthrough-ppt-video "$env:USERPROFILE\.codex\skills\code-walkthrough-ppt-video"
```

## 安装到 Claude Code

安装为个人技能：

```bash
git clone https://github.com/sharptoolbox/code-walkthrough-ppt-video.git ~/.claude/skills/code-walkthrough-ppt-video
```

也可以安装到单个项目：

```bash
git clone https://github.com/sharptoolbox/code-walkthrough-ppt-video.git .claude/skills/code-walkthrough-ppt-video
```

Windows PowerShell 本地安装：

```powershell
Copy-Item -Recurse -Force .\code-walkthrough-ppt-video "$env:USERPROFILE\.claude\skills\code-walkthrough-ppt-video"
```

安装后新开一个会话，让工具重新发现 `SKILL.md`。其他兼容 Agent Skills 目录规范的工具，也可以通过复制整个目录完成安装。

## 环境依赖

PPT 模式需要 Python 3.9+、Pillow，以及 Chrome 或 Edge。可以运行：

```bash
python "<skill>/ppt/scripts/shoot_page.py" --check
```

视频模式额外需要 Node.js、Remotion 4、ffmpeg、`edge-tts` 和 Pillow。运行环境检查：

```bash
python "<skill>/video/scripts/check_env.py"
```

视频依赖装配：

```bash
bash "<skill>/video/scripts/setup_remotion.sh" "<video-project-dir>"
```

Windows 用户可以在 Git Bash 或 WSL 中运行视频侧的 Bash 脚本。PPT 侧 Python 脚本可直接在 PowerShell 中使用。

## 目录结构

```text
code-walkthrough-ppt-video/
├── SKILL.md                 统一入口、模式选择与公共质量规则
├── README.md                安装、依赖和使用说明
├── LICENSE                  MIT 许可证
├── NOTICE                   第三方组件声明
├── agents/openai.yaml       Codex 技能列表元数据
├── ppt/
│   ├── WORKFLOW.md          PPT 完整工作流
│   ├── assets/              deck、UI、图表与架构模板
│   ├── references/          PPT 规范文档
│   └── scripts/             截图、组装和质检脚本
└── video/
    ├── WORKFLOW.md          视频完整工作流
    ├── assets/              视频 UI 骨架
    ├── references/          视频规范文档
    ├── project/             Remotion 工程模板
    └── scripts/             配音、分镜、渲染和验收脚本
```

## 设计原则

源码只读，产物写入独立目录。真实截图和用户手册优先，缺少时才按源码重绘。每个重要结论必须能定位到源码文件与行号；没有证据的技术能力不写入成品。所有演示数据使用仿真值，并在成品中说明重绘界面的性质和当前能力边界。

## 许可证

本仓库主体使用 MIT License。PPT 模板中附带的 Apache ECharts 5.x 使用 Apache License 2.0，原始许可证位于 `ppt/assets/templates/LICENSE-Apache-2.0.txt`，详情见 `NOTICE`。
