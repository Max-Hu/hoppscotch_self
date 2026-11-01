# 离线开发技能库

从 13 个固定提交的上游整理而来：**39 个主入口 + 1 个备选入口**，覆盖需求与变更记录、实现计划、Python、重构、调试、审查、PostgreSQL、HTMX 和网页验收。已剔除不满足要求的 Playwright CLI 备选项。

这是技能源码与审查记录目录。技能在正式使用时只读取本地资料，不自动获取文档、安装依赖、更新工具或联系远端服务。通用依赖仍可能含网络代码；本库的包装器不是系统防火墙。范围和已知限制见[复审记录](skill-library/REAUDIT_2026-11-01.md)。

## 从哪里开始

1. 阅读[完整技能索引](CATALOG.md)，只选当前任务需要的入口。
2. 阅读 [PROJECT_RULES.md](PROJECT_RULES.md)，将目标项目的技术选择和业务不变量集中记录在那里。
3. 告诉代理读取具体 `SKILL.md`，例如“按照 `skill-library/skills/systematic-debugging/SKILL.md` 排查”。此目录未向任何宿主全量注册 40 个技能。

**VS Code Copilot 用户：** 请按 [Copilot 接入指南](docs/VSCODE_COPILOT.md)配置技能目录、项目规则和调用方式。下载本目录不等于已经在 Copilot 中注册；技能离线也不等于 Copilot 服务可以断网使用。

本 README 以下命令均从 `offline-skills/` 内执行；Copilot 接入指南另行给出从目标项目根目录调用的路径。路径中的 `python` 必须是本机已准备的解释器。不要把项目根目录已有的规则覆盖掉，也不要把本目录的规则直接施加到仓库的 Hoppscotch 部署文件。

| 工作 | 推荐入口 |
| --- | --- |
| 需求、设计、任务、归档 | OpenSpec 的 explore / propose / apply / archive |
| 复杂实施计划 | writing-plans → executing-plans；简单修改直接实施 |
| Python 实现与重构 | python-design-patterns / async-python-patterns / python-testing-patterns |
| 故障与完成验证 | systematic-debugging / verification-before-completion |
| 代码审查 | code-review-excellence；敏感变更按需 differential-review |
| 页面与验收 | frontend-design / htmx / web-design-guidelines / webapp-testing |
| 替代计划入口 | planning-with-files；避免维护第二套重复任务记录 |

## 仓库里包含什么

`skill-library/skills/`、`alternatives/` 包含正文和完整的技能相对引用资源；`patches/` 保存离线改动；`audit/` 保存审查理由和哈希；`tools/` 是本地验证工具；`runtime/` 是适配脚本；`tests/` 是实际冒烟测试和最近结果。

上游固定提交见 `skill-library/sources.lock.json`，逐项对应见 `skills.lock.json`。各技能的许可证随目录保留，详见 [NOTICE.md](NOTICE.md)。源码原件、在线下载工具、旧版 ZIP、下载缓存、业务配置和个人会话均未上传。

## 依赖与离线恢复

**仅阅读技能和运行静态审查不需要大型运行依赖。** 验证器所需的纯 Python PyYAML 已随库提供：

```text
python -X utf8 skill-library/tools/audit_library.py
python -X utf8 tools/verify_distribution.py
```

OpenSpec 实际运行、Python 网页测试和 Hypothesis 测试需要额外制品。它们体积较大，未提交到 Git。本地完整运行包为 `skills-offline-runtime-2026-11-01-r2.zip`，约 174.5 MiB；此仓库不提供下载链接，也不自动从互联网补齐。

将已准备的该 ZIP 搬入目标环境后，执行本地恢复脚本：

```text
python -X utf8 tools/restore_runtime.py --archive /path/to/skills-offline-runtime-2026-11-01-r2.zip
python skill-library/runtime/openspec_offline.py --version
python skill-library/runtime/offline_python.py path/to/local_browser_test.py
python -X utf8 skill-library/tests/test_offline_library.py
```

恢复器先核对完整 ZIP 的固定 SHA-256，再仅提取运行依赖，不覆盖技能、规则和适配器，不接受其他版本，不执行下载。Windows/Linux x64 的制品面向 CPython 3.12；解释器、浏览器和 Linux 系统库需预先准备。可选 Node 可视化检查使用预装 Node，可设置 `OFFLINE_NODE_EXECUTABLE`；没有 Node 时该项会明确跳过。

浏览器测试必须通过 `offline_python.py` 执行，使用 `launch_local_browser`、禁止 service worker 的 context 和 `protect_context`。OpenSpec 必须通过 `openspec_offline.py`，不直接运行原始二进制。缺少依赖时报告，不临时安装。

已有 Windows 本地验证：40 个入口静态检查通过，14 项测试通过、无跳过。测试不代表 Linux 已实机验证，也不代表所有原生进程已做零外联认证。详见[审查报告](skill-library/AUDIT_REPORT.md)和[测试结果](skill-library/tests/results.json)。
