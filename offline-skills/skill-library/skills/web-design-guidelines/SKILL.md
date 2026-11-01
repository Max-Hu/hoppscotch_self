---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility",
  "audit design", "review UX", or "check my site against best practices".
metadata:
  author: vercel
  version: 1.0.0
  argument-hint: <file-or-pattern>
---

## Offline edition

Read the project's central `PROJECT_RULES.md` before use. This is an adapted,
pinned upstream skill. Use only local files, installed tools, local Git history,
and explicitly designated loopback test services. Do not fetch citations,
install packages, update tools, contact remote MCP services, or use remote Git.
Reference URLs and API examples are documentation, not authorization to connect.
Missing dependencies must fail closed with a local prerequisite report.
The original source and exact patch are retained in this library for review.

# Web Interface Guidelines

Review files for compliance with Web Interface Guidelines.

## How It Works

1. Read the bundled `references/web-interface-guidelines.md`
2. Read the specified files (or prompt user for files/pattern)
3. Check against all rules in the bundled guidelines
4. Output findings in the terse `file:line` format

## Guidelines Source

Read `references/web-interface-guidelines.md`, pinned with this skill. Do not use WebFetch or refresh rules at runtime.

## Usage

When a user provides a file or pattern argument:
1. Read `references/web-interface-guidelines.md`
2. Read the specified files
3. Apply all rules from the bundled guidelines
4. Output findings using the format specified in the guidelines

If no files specified, ask the user which files to review.
