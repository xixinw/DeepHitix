# Open Source Compliance Plan

> 本文不是法律意见，是项目开源治理执行清单。

## 已确认许可证事实

Hermes Agent：
- License: MIT
- Copyright (c) 2025 Nous Research

DeepSeek-Reasonix：
- License: MIT
- Copyright (c) 2026 Reasonix Contributors

MIT 允许使用、复制、修改、发布、再授权和商用，但必须保留版权声明和许可证文本。

## 基本策略

1. 第一阶段只借鉴架构思想，不复制 Reasonix 代码。
2. 如果从 Hermes fork 或复制文件，保留原 copyright 和 MIT 声明。
3. 如果未来复制/改写 Reasonix 代码，必须在文件头和 THIRD_PARTY_NOTICES 标注。
4. 不使用会造成官方混淆的名称和文案。
5. 发布前跑依赖许可证扫描。

## 必备文件

根目录必须包含：

- LICENSE
- NOTICE.md
- THIRD_PARTY_NOTICES.md
- ATTRIBUTION.md
- TRADEMARKS.md
- SECURITY.md
- PRIVACY.md
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md

## README 第一屏声明

建议写：

This project is an independent open-source project inspired by Hermes Agent and DeepSeek-Reasonix. It is not affiliated with, endorsed by, or officially maintained by Nous Research, DeepSeek, or Reasonix.

中文：
本项目是独立开源项目，借鉴 Hermes Agent 和 DeepSeek-Reasonix 的部分设计思想，不代表 Nous Research、DeepSeek 或 Reasonix 官方。

## 文件头规则

### 从 Hermes 派生的文件

```python
# Derived from NousResearch/hermes-agent
# Original license: MIT
# Copyright (c) 2025 Nous Research
# Modifications Copyright (c) 2026 DeepSeek Native Agent Contributors
```

### 从零写的文件

```python
# Copyright (c) 2026 DeepSeek Native Agent Contributors
# SPDX-License-Identifier: MIT
```

### 从 Reasonix 改写/复制的文件

只有在确实使用其代码时才写：

```python
# Derived from esengine/DeepSeek-Reasonix
# Original license: MIT
# Copyright (c) 2026 Reasonix Contributors
# Modifications Copyright (c) 2026 DeepSeek Native Agent Contributors
```

## 品牌风险规避

避免：
- Hermes Official
- DeepSeek Official
- Reasonix Hermes
- DeepSeek-Hermes Official
- 暗示官方授权或背书

推荐：
- DeepSeek Native Agent（暂定）
- 副标题说明 inspired by，而不是 official fork

## 依赖许可证扫描

Python：
- pip-licenses
- pip-audit

Node：
- license-checker
- npm audit

CI 检查：
- 禁止引入 GPL/AGPL 依赖，除非单独审批
- 依赖许可证变更必须进入 PR checklist

## 隐私与安全

- 不内置任何 API Key
- 不上传用户 telemetry 到项目方服务器
- telemetry 默认只记录 token/cost/meta，不记录 prompt 正文
- 日志中脱敏 API key/token/secret
- 用户可关闭 telemetry
- 明确日志路径和清理方法

## 发布前 Checklist

- [ ] LICENSE 存在
- [ ] NOTICE.md 存在
- [ ] THIRD_PARTY_NOTICES.md 存在
- [ ] ATTRIBUTION.md 存在
- [ ] README 非官方声明存在
- [ ] Derived files 保留文件头
- [ ] 依赖 license scan 通过
- [ ] secret scan 通过
- [ ] API key 不进示例配置
- [ ] DeepSeek 服务条款责任说明存在
- [ ] benchmark 文案没有夸大“最低成本”
