# 仓库分发版

使用说明、命令工作目录和依赖边界见 [../README.md](../README.md)，技能索引见 [../CATALOG.md](../CATALOG.md)。

本目录来自第二版离线技能库，保留 40 个入口及其相对资源、许可证、补丁、审查和测试资料。`AUDIT_REPORT.md` 和 `REAUDIT_2026-11-01.md` 记录完整本地制品的复审事实；文中原始归档和完整运行 ZIP 不随 Git 提交。

仓库版只附轻量适配器与验证依赖。大型 OpenSpec、Python 工具包通过父目录 `tools/restore_runtime.py` 从已经准备的固定本地 ZIP 恢复；不在线获取。静态审查不需要恢复原始上游或大型制品，此时报告的 before_findings 为空，当前副本的检查照常执行。
