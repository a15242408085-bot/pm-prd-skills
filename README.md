# PM PRD Skills

把用户反馈写成能评审、能验收的 PRD。面向中文产品经理，也覆盖 RAG、聊天机器人和 Agent 的失败边界。

11 个可复用的 Agent Skills，采用 MIT 协议。无需专用平台；模型服务按所用工具计费。

## Skill 功能

| Skill | 一句话功能 | 主要产物 |
| --- | --- | --- |
| `pm-voc` | 整理用户反馈，找到有证据的核心问题。 | 用户信号与问题优先级 |
| `pm-prd` | 把需求写成含边界、异常和验收标准的 PRD。 | 六段式 PRD |
| `pm-lint` | 找出 PRD 的遗漏、矛盾和不可验收项。 | 评审问题与修改建议 |
| `pm-metrics` | 定义成功指标、统计口径和质量护栏。 | 指标与埋点方案 |
| `pm-premortem` | 提前推演失败，补上预警、降级和回滚条件。 | 风险清单 |
| `pm-eval` | 把验收标准和真实坏案例转成 AI 评测集。 | JSON 评测设计 |
| `pm-run-eval` | 协调已有评测工具运行，汇总真实结果。 | 运行证据与结果报告 |
| `pm-transcript-review` | 复盘 AI 执行记录，区分产品、工具和评分问题。 | 失败归因与修复项 |
| `pm-launch-readiness` | 汇总需求、评测和风险证据，给出上线建议。 | GO / NO-GO / CONDITIONAL |
| `pm-brief` | 把 PRD 压缩成便于决策和同步的一页摘要。 | 决策简报 |
| `pm-workflow` | 串联以上步骤，减少反复交代背景。 | 连贯的需求交付包 |

只写 PRD 时，先用 `pm-prd`，再用 `pm-lint`。需要指标时加 `pm-metrics`；AI 功能再加评测。

## 安装与使用

每个 `skills/<name>/` 都是完整的技能目录。复制整个目录，保留其中的模板、参考文件和脚本。格式遵循 [Agent Skills 规范](https://agentskills.io/specification)。

### Claude Code

在终端执行，安装到个人技能目录。也可将目标换成项目内的 `.claude/skills/`。

```sh
git clone https://github.com/a15242408085-bot/pm-prd-skills.git
cd pm-prd-skills
mkdir -p ~/.claude/skills
cp -R skills/pm-* ~/.claude/skills/
```

安装后调用 `/pm-prd`、`/pm-lint` 等。技能目录与调用方式见 [Claude Code 官方文档](https://code.claude.com/docs/en/skills)。已有同名技能时，先对比本地修改，再复制。

### 其他支持 Agent Skills 的工具

把所需技能目录复制到该工具支持的技能目录；通过技能选择器或自然语言调用。工具的技能路径和调用语法以其官方说明为准。

普通聊天工具可直接附上 `SKILL.md` 和它引用的资源，再提供需求材料。文件附件不能自动赋予工具执行评测的能力。

### 直接试一条需求

```text
/pm-prd
我们要为企业 RAG 知识库增加引用溯源。
回答需展示文档来源和 PDF 页码，并能点击查看证据。
来源无权限、没有证据、文档更新或引用服务超时，都要有处理方式。
用户规模、性能目标和上线日期尚未确定，请明确标记待确认。
输出 Markdown PRD，不要编造数据。
```

```text
/pm-lint
评审刚生成的 PRD。重点检查范围、租户隔离、引用准确性、异常状态和验收标准。
```

```text
/pm-workflow
依据这些反馈依次完成问题整理、PRD、自检、指标和风险推演。
只产出需求文档，暂不运行模型评测。
```

## 优化了什么

- 保留六段式 PRD，给需求、验收项、风险和用例分配稳定编号，便于追溯。
- 将事实、假设和待确认项分开；没有来源的数据和阈值不作为已确定要求。
- 为关键流程补齐空、加载、错误、超时、无权限、拒答和人工接管状态。
- 指标写明公式、分母、窗口、来源与护栏，避免只写“提升体验”。
- AI 评测覆盖正常、失败和相邻案例；检查实际 Outcome，避免只看模型声称完成。
- 运行缺失、环境错误和评分不完整单独报告；严重失败不能被平均分掩盖。
- 保留现有公司模板与用户授权范围，按任务选步骤，不强制跑整条链。

## 示例与验证

[RAG 引用溯源示例](examples/rag-citations/README.md)包含虚构反馈、PRD、评测集和模拟运行记录，展示 `SRC → REQ → AC → CASE` 的关系。

```sh
python3 scripts/validate_pack.py
python3 -m unittest discover -s tests -v
python3 skills/pm-run-eval/scripts/summarize_eval.py \
  --suite examples/rag-citations/suite.json \
  --results examples/rag-citations/results-demo.json
```

辅助脚本仅需 Python 3.10+ 标准库。结果汇总器读取已有记录，不调用模型。示例运行记录是模拟数据，不代表产品通过真实测试。真实评测须接入团队已有 runner / adapter，并记录版本与证据。

本仓库的 JSON 格式名为 `pm-prd-eval/v1`，用于需求交接和结果汇总，**不宣称兼容 pmstack 或第三方 Harness**；接入时按目标工具转换。

## 来源与许可

根据作者的[飞书文章](https://clnj9a21z5.feishu.cn/wiki/AyhiwfDKdiEkW1kQdHgcfG1Cnpf)整理并独立重写。原文命令与新技能的对应关系、能力补充及版本差异见 [来源说明](docs/source-mapping.md)。

上游 [RyanAlberts/pmstack](https://github.com/RyanAlberts/pmstack) 已在 2.0 中移除旧版 PM 命令；本文技能包独立维护，未复制上游代码、Skill 正文或运行框架，也不是其官方中文版本。

本仓库原创技能、模板、脚本与虚构示例采用 [MIT License](LICENSE)。飞书文章与外部链接内容保留各自权利。
