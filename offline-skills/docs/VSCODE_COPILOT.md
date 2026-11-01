# 在 VS Code Copilot 中使用

本指南针对 VS Code 中的 Copilot Agent。当前仓库是技能库的存放位置；将文件放进工作区后，还需要配置技能发现。本指南中的设置和指令是供目标项目合并的示例，不会因为读取本文自动生效。

## 1. 保留完整目录

将整个 `offline-skills/` 放入需要开发的项目根目录，并用 VS Code 打开该项目根目录：

```text
你的项目/
├── .vscode/
│   └── settings.json
├── .github/
│   └── copilot-instructions.md
├── PROJECT_RULES.md              # 目标项目已有的业务规则，如有
├── offline-skills/
│   ├── PROJECT_RULES.md          # 技能库的通用规则
│   └── skill-library/
│       ├── skills/
│       ├── alternatives/
│       └── runtime/
└── 业务代码/
```

不要只复制单个 `SKILL.md`，其参考资料、模板或脚本可能同样需要。保持现有结构也能保留本库运行适配器的相对位置。

## 2. 配置技能发现

在目标项目的 `.vscode/settings.json` 中合并以下设置，保留已有配置：

```json
{
  "chat.useAgentSkills": true,
  "chat.agentSkillsLocations": {
    "offline-skills/skill-library/skills": true
  }
}
```

这里注册的是 39 个主技能的目录。Copilot 按需加载技能正文，不需要一次执行所有流程。`planning-with-files` 留在 `alternatives/`，需要改选它时再单独配置，避免重复维护计划。

VS Code 也支持原生 `.github/skills/<名称>/SKILL.md` 位置；本库使用自定义目录是为了保留当前资源和适配器结构。`chat.agentSkillsLocations` 是编辑器设置，不会自动被 Copilot CLI 或 Copilot App 继承。这一方法针对 VS Code；其他客户端应单独接入。[VS Code 官方技能说明](https://github.com/microsoft/vscode-docs/blob/main/docs/agent-customization/agent-skills.md)、[设置参考](https://code.visualstudio.com/docs/agents/reference/ai-settings)。

## 3. 接入项目统一规则

在目标项目的 `.github/copilot-instructions.md` 中合并以下内容：

```markdown
使用技能前，先读取项目根目录的 PROJECT_RULES.md。
若没有该文件，先读取 offline-skills/PROJECT_RULES.md。

技能库位于 offline-skills/skill-library/。
正式使用只读取本地资料，不下载文档、安装依赖或自动更新工具。
缺少依赖时报告，不回退联网。

执行技能脚本时，根据实际文件位置解析路径，不机械复制相对命令。
从项目根目录调用包装器时，使用
offline-skills/skill-library/runtime/ 下的实际路径。
业务命令保持目标项目所需的工作目录；不要为了找到工具而切换到错误的项目根目录。
OpenSpec 必须通过 openspec_offline.py，不直接运行原生二进制。
浏览器测试必须使用 offline_python.py 和 browser_guard。
```

将技术栈、模块边界、业务不变量和测试命令集中记录在目标项目的 `PROJECT_RULES.md`。通用指令记录统一规则，技能提供按需工作方法，不把整份技能正文复制进通用指令。[两类自定义的职责](https://code.visualstudio.com/docs/agent-customization/agent-skills)。

## 4. 确认识别并调用

1. 打开命令面板，运行 `Chat: Open Customizations`，进入 **Skills** 查看技能及来源路径。
2. 新建 Copilot Agent 对话，输入 `/`，检查是否出现 `systematic-debugging` 等技能名称。
3. 先明确指定一个技能做小任务，再查看聊天中的文件读取和工具活动，确认读取的是本地离线副本。

例如：

```text
/systematic-debugging 排查这个接口偶发超时的问题，先定位原因。
```

```text
/python-design-patterns 检查任务调度模块的职责划分，提出保持行为不变的重构建议。
```

```text
/verification-before-completion 核对这次修改的验收条件，运行相关本地检查并报告结果。
```

也可以直接输入“使用 systematic-debugging 技能排查……”。技能被发现不保证模型对每个相关请求都自动调用，首次建议明确指定并检查实际行为。[官方调用与验证说明](https://github.com/microsoft/vscode-docs/blob/main/docs/agent-customization/agent-skills.md#verify-a-skill)。

如果菜单没有识别，可先让 Copilot 显式读取文件：

```text
请先读取 offline-skills/PROJECT_RULES.md，以及
offline-skills/skill-library/skills/systematic-debugging/SKILL.md，
然后按其中流程排查当前错误。只使用本地资料和已准备的工具。
```

同时检查 VS Code 打开的是否为目标项目根目录、设置是否被当前版本识别、路径和技能文件是否存在。打开新对话后重新查看；不要通过临时下载插件或工具来绕过封闭环境约束。

## 5. 脚本运行依赖与工作目录

阅读调试、设计、计划或审查指导本身不需要恢复大型运行依赖。实际运行 OpenSpec、Python 网页测试或 Hypothesis 时，先按 [README 的离线恢复说明](../README.md#依赖与离线恢复)准备制品，缺失时报告。

从目标项目根目录调用的路径示例：

```text
python offline-skills/skill-library/runtime/openspec_offline.py list --json
python offline-skills/skill-library/runtime/offline_python.py tests/local_browser_test.py
```

其中 `tests/local_browser_test.py` 是目标项目自己编写的测试，不是库中已存在的通用验收脚本。它应使用 `launch_local_browser`、`service_workers="block"` 的 context 和 `protect_context`。OpenSpec 会针对当前工作目录所定位的规格根操作，不能为了运行工具而在技能库目录误初始化业务规格。

## 6. 封闭网络的边界

技能文件、参考资料和本库指定的运行路径可以按离线方式使用。**这不等于标准 GitHub Copilot 自身可以在完全断网环境工作。** 标准服务仍需要相应认证及 Copilot 服务访问；如果环境也禁止这些连接，仅复制技能或修改设置无法解决模型服务接入。[GitHub 官方网络要求](https://docs.github.com/en/copilot/reference/copilot-allowlist-reference)。

本库不配置或验证公司的模型网关，也不控制 Copilot 自身的服务请求、遥测或所有原生子进程。技能文本中的“不联网”约束与实际网络隔离是不同层面的控制。封闭环境应事先具备获准使用的模型接入和依赖制品。

本文配置依据官方文档整理，未在用户的 VS Code 实例中实际启用或验收；菜单和可用设置取决于已安装版本及组织策略。官方链接供准备和查阅来源使用，技能正式执行时无需打开这些链接。
