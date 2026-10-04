# 来源与改写说明

来源为作者提供的飞书文章《Claude 写 PRD 很快，AI 产品为什么还是不敢上线？pmstack 让需求和评测终于对上了》，读取日期为 2026-10-04。

文章中出现了九个明确的命令名称；下表分别列出它们。Launch Readiness 与 Brief 在原文作为能力提及，本仓库将其补充为独立技能。研究作为泛称出现，未将其推定为一个命名 Skill。

| 原文出现方式 | 本仓库技能 | 保留与优化 |
| --- | --- | --- |
| `/voc` | `pm-voc` | 保留反馈聚类，增加出处、去重与样本偏差说明 |
| `/prd` | `pm-prd` | 保留六段式结构，增加需求编号、异常状态、验收项 |
| `/lint` | `pm-lint` | 保留反向评审，增加问题定位、严重程度和最小修复 |
| `/metrics` | `pm-metrics` | 保留北极星与反指标，增加分母、窗口、埋点和阈值状态 |
| `/premortem` | `pm-premortem` | 保留事前失败推演，增加触发器、负责人角色与回滚条件 |
| `/eval` | `pm-eval` | 保留需求转用例，统一独立 JSON 格式与证据映射 |
| `/run-eval` | `pm-run-eval` | 保留重复运行与证据，明确必须接入真实 runner |
| `/transcript-review` | `pm-transcript-review` | 保留记录复盘，区分决策、检索、工具、环境和评分问题 |
| `/loop` 链式步骤 | `pm-workflow` | 保留步骤衔接；改名以避免与定时循环命令混淆 |
| Launch Readiness 能力 | `pm-launch-readiness` | 能力补充，汇总证据与有条件上线建议 |
| Brief 能力 | `pm-brief` | 能力补充，将 PRD 整理为决策简报 |

## 版本差异

截至读取时，[上游 README](https://github.com/RyanAlberts/pmstack#upgrading-from-pmstack-1x)说明 pmstack 2.0 已移除旧版 PM 命令和评测 Harness，旧版可以从 `v1.2.0` 获取。因此未沿用文章的“安装最新版即可使用旧命令”说明。

本仓库根据文章的方法与产品经理需求独立撰写，使用自有 `pm-` 前缀。它不包含 Eval Studio、模型 Adapter 或自动发布系统；脚本只负责校验包结构与汇总既有运行结果。

未将文章中转述的第三方数据、作者个案结果或行业数值当作基准。示例全部重新构造并标明虚构，未公开客户资料或文章全文。
