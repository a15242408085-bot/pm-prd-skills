# pm-prd-eval/v1

用于需求交接，不包含模型执行器。用例应转为团队 runner 的格式，运行后可转回此结果格式。

## Suite JSON

```json
{
  "schema_version": "pm-prd-eval/v1",
  "suite_id": "rag-citations-v1",
  "purpose": "regression",
  "execution": {
    "model_version": "待确定",
    "prompt_version": "待确定",
    "tool_version": "待确定",
    "data_version": "待确定"
  },
  "trials_per_task": 3,
  "gate": {"approved": false, "min_trial_pass_rate": 1.0},
  "tasks": [{
    "id": "CASE-001",
    "source_type": "synthetic",
    "requirement_ids": ["REQ-001"],
    "acceptance_ids": ["AC-001"],
    "critical": true,
    "input": "向有权限的用户展示引用",
    "environment": "每轮恢复独立的虚构租户和文档 fixture",
    "expected": "引用指向支持结论的真实文档片段",
    "forbidden": ["虚构文档或页码"],
    "grader": {"type": "human", "criteria": "核查来源、页码、权限和支持关系"}
  }]
}
```

`purpose` 为 capability 或 regression；`source_type` 为 real 或 synthetic。`grader.type` 为 code、model、human 或 hybrid，criteria 写可操作的判断规则。编号数组不可为空；同一 Suite 中 Task ID 唯一。未知执行版本可用于设计，但真实运行前必须固定。

阈值为 0～1 的比率。approved 表示团队已确认指标口径和阈值，不等于产品已经批准上线。critical 的任何已评分失败单独阻断质量门槛。

## Results JSON

```json
{
  "schema_version": "pm-prd-eval-results/v1",
  "suite_id": "rag-citations-v1",
  "run_id": "demo-001",
  "data_kind": "synthetic",
  "execution": {
    "model_version": "待确定",
    "prompt_version": "待确定",
    "tool_version": "待确定",
    "data_version": "待确定"
  },
  "records": [{
    "task_id": "CASE-001",
    "trial_index": 1,
    "status": "passed",
    "transcript": "demo://CASE-001/trial-1/transcript",
    "outcome": "demo://CASE-001/trial-1/outcome",
    "reason": "模拟结果；未调用模型"
  }]
}
```

`data_kind` 为 real 或 synthetic。真实数据须使用可核实证据定位，demo URI 只可用于模拟数据。

`status` 为 passed、failed、infra_error 或 ungraded。passed／failed 必须同时有 Transcript 与 Outcome 证据定位；其他状态必须有 reason。trial_index 从 1 起，不得超过 trials_per_task；一对 task_id + trial_index 只能出现一次。

执行版本和 suite_id 必须与 Suite 相同。修改 Task 或评分器时更新 suite_id；原运行记录不能直接用于新版本。

## 汇总口径

- 已评分通过率 = passed / (passed + failed)；无已评分项时为 null。
- 完成覆盖率 = 已评分项数 / 计划项数；missing、infra_error、ungraded 都未完成。
- 另列每项任务的通过数、失败数、运行错误、未评分和缺失次数。
- critical 已评分失败 → failed；否则不完整 → incomplete；完整但未批准门槛 → not_approved；批准且达到阈值 → passed，否则 failed。
- 模拟结果始终不能作为真实上线依据。汇总不是统计置信度估计，也不代替人工签字；不将单次样本比例称为 pass@k 或 pass^k。
