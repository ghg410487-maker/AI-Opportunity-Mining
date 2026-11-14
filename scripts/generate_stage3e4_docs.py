from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'docs/research_stage3/stage3e4'; E=ROOT/'experiments/stage3e4'; D.mkdir(parents=True,exist_ok=True)
PDF=Path(r'E:\xwechat_files\wxid_r4to3bbty1yu22_ff68\msg\file\2026-11\本科组赛题：AI应用场景的智能挖掘与机会评估系统.pdf')
BASE=PDF.parent
official={
 'problem_pdf':PDF,
 'result1_template':BASE/'result1.csv','result2_template':BASE/'result2.csv','result3_template':BASE/'result3.csv','result4_template':BASE/'result4.csv',
 'attachment1':BASE/'附件1.xlsx','attachment2':BASE/'附件2.xlsx'}
def sh(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
manifest={k:{'path':str(v),'exists':v.exists(),'sha256':sh(v) if v.exists() else ''} for k,v in official.items()}
(E/'official_material_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

docs={
'official_task2_rule_verification.md':'''# 官方 Task 2 规则核验

核验日期：2026-11-14。官方PDF、result1—result4模板、附件1类别表和附件2来源表均已找到并逐项核验。

## 逐项结论

| 问题 | 官方位置 | 准确结论 | 当前状态/对601条影响 |
|---|---|---|---|
| 机会1标准 | PDF第3页，Task 2 | 真实业务痛点或不足；AI方案能改善；回应真实业务需求；具有工程价值。另要求真实需求、AI核心性和技术可行性。 | v2的D1—D6可作内部证据框架，但不能把T0教育相关性直接当机会。 |
| 0的含义 | PDF第3页 | 未达到机会判定标准；纯教程、科普、广告、AI噱头直接判0。 | 必须有适用规则/证据，不能仅因内部REVIEW而写0。 |
| 证据不足能否归0 | PDF未明确授权 | 官方只规定二值输出和阈值自定义，没有写“无法认定=0”。 | 601条不能自动归0。方案B需负责人书面解释。 |
| 不确定样本 | PDF未规定REVIEW字段 | REVIEW是项目内部治理状态，不是官方值域。 | 正式导出前必须形成逐记录合法1/0。 |
| 置信度 | PDF第4页模板说明 | 0—1，越高越可能为机会；未规定小数位。 | 现有部分内部置信度含“决策把握度”语义，正式映射需审批。 |
| 0时类别 | PDF第4页示例 | 示例中功能类别、所属行业留空。 | 导出器强制0行两列留空。 |
| 是否全覆盖 | PDF第3页及result2模板 | 要求将清洗后的全部记录输出到result2。 | 必须覆盖冻结result1的1984个唯一ID。 |
| 正文缺失可否删除 | 未见授权 | 官方没有允许从result2删除已进入result1的记录。 | 仍须保留并审慎判定，不能静默排除。 |

附件1核验得到16个功能类别、30个行业类别；导出器按该合法值域校验。另发现冻结result1列名与官方空模板存在“采集时间/发布时间”等差异，这是Task 1正式提交前的独立合规事项，不在本轮改写冻结主表。
''',
'review601_analysis.md':'''# 601条REVIEW审计

真实运行确认：601个record_id唯一，与v2的REVIEW集合完全一致，也全部存在于1984条冻结主表。原v2标签未改写。

| 互斥分组 | 数量 |
|---|---:|
| 优先补取正文 | 439 |
| D3/D6共同缺失 | 100 |
| 供给宣传排除候选 | 31 |
| 泛化问题排除候选 | 3 |
| AI核心性不清 | 16 |
| 其他边界复核 | 12 |
| 合计 | 601 |

逐条审计层位于`experiments/stage3e4/review601_audit.csv`，只含结构字段和D1—D6信号，不含第三方完整原文。所有`proposed_official_label`为空，审批状态均为`PENDING_APPROVAL`。

三级处置：A类34条只作为规则候选；B类439条按可访问性和潜在结果影响分级补证；C类128条及A/B未解决项保留不确定性。证据缺失不等于反面证据。
''',
'exclusion_rules_evaluation.md':'''# 排除规则评估

| 规则 | 命中 | 郭42重叠 | 人工结果 | 结论 |
|---|---:|---:|---|---|
| 供给宣传队列（宽规则） | 31 | 7 | 1机会/6非机会 | 有真实机会冲突，不可自动使用 |
| 供给宣传且无强痛点信号（收窄） | 27 | 5 | 0机会/5非机会 | 值得负责人批准为小范围候选，但样本支持仍小 |
| 泛化问题队列 | 3 | 3 | 1机会/2非机会 | 冲突明显，不建议批准自动排除 |

收窄规则精确定义：记录已进入既有“供给宣传候选”层，且当前文本没有强痛点信号。它仍只能生成“建议0”，不能覆盖可能缺失的用户证据。错误风险包括产品README同时包含真实求助、标题/短正文截断痛点、以及供给材料确实回应明确任务。

逐条命中及人工冲突见`experiments/stage3e4/exclusion_rule_evaluation.csv`。42条用于开发校准，不能再用于独立性能声明。
''',
'priority_evidence_recovery.md':'''# 优先补证与小规模真实试验

从601条中筛得27条高影响记录：D2问题明确性与D4 AI核心性至少为1，且已有D3信号或强痛点信号。来源分布为GitHub、B站、掘金等，覆盖标题、短文和实质正文等级。

本轮对5条公开GitHub原始页进行了合规访问，5/5可访问；均记录实际URL、2026-11-14获取日期与`ORIGINAL_GITHUB_README_OR_ABOUT`类型。恢复内容强化了产品/项目用途信息，但没有充分建立独立的D3真实需求证据，因此没有据此改写标签。

其余22条保持`PENDING`。逐条队列在`experiments/stage3e4/priority_evidence_recovery.csv`。本轮不将网络页面全文写入公开Git，也不回写冻结主表。
''',
'human42_false_negative_analysis.md':'''# 郭42条中的8条v2潜在漏判分析

郭确认的12条机会中，v2仅保留4条为1，另8条进入REVIEW。共同特征是D1、D2、D4通常较强，但D3/D6在当前片段中为0；其中一条还受到总分/最小维度阈值影响。

主要原因不是已发现反面证据，而是v2把“缺少独立需求佐证”机械地当作阻断。供给说明与真实需求必须分开，但直接求助、明确教学任务或可观察痛点不应因缺少第三方材料自动失效。建议：把“文本未呈现D3/D6”和“已证实D3/D6不成立”分开编码；直接用户问题证据允许支持D3，但不外推商业价值。

8条专项表位于`experiments/stage3e4/human42_false_negative_8.csv`。这是开发误差审计，不是总体Recall、Accuracy或Macro-F1。
''',
'result2_policy_decision_package.md':'''# result2二值政策审批包

## 方案对照

| 方案 | 可立即合法导出 | 优点 | 风险/负担 |
|---|---|---|---|
| A 严格证据认证 | 否：1383条已有1/0，601条阻断 | 最可追溯，真实性风险最低 | 需补证/裁决601条，截止期压力最大 |
| B 有条件保守二值 | 仅负责人书面批准官方语义解释后 | 最快形成1984条 | 官方未明确“证据不足=0”；假阴性风险高，8/12人工机会已被v2阻断 |
| C 规则排除+重点补证+人工裁决 | 当前仍否；批准后分批收敛 | 风险、工期、可追溯性较平衡 | 仍需人工；不能保证一次消除全部REVIEW |

推荐方案C。第一批建议负责人审阅27条“供给宣传且无强痛点”候选；若逐条/按明确版本规则批准，理论上剩余未决574条。同步优先核验27条高影响记录；本轮5条原始页访问成功，但0条获得足以自动结束D3的证据。泛化问题规则不批准自动排除。

## 负责人审批区（当前均待批）

- 选用方案：`PENDING_APPROVAL`
- 规则版本：`stage3e4_policy_pending_v1`
- 适用record_id集合：`PENDING_APPROVAL`
- 是否允许保守二值：`PENDING_APPROVAL`
- 置信度语义映射：`PENDING_APPROVAL`
- 审批人/时间/依据：空
- 剩余风险：601条仍无正式二值；42条开发样本不能代表全量

机器可读审批模板：`owner_result2_approval_template.json`。必须填写逐记录决定和依据，不能使用全局默认吞并REVIEW。
''',
'official_export_validation.md':'''# 官方导出验证

新增`scripts/export_official_stage3e4.py`，按record_id合并冻结主表、版本化机器判断、负责人决定；校验官方表头、1984覆盖、唯一性、二值、0—1置信度、类别值域及0行空类别。

真实运行状态：`BLOCKED`。审批文件为`PENDING_APPROVAL`，601条仍未决；未写出正式`result2.csv`。即使全部审批完成，程序也只先写`result2_candidate_approved.csv`，仍需验收后由提交流程采用正式文件名。

重要阻断：现有内部`opportunity_confidence`未完全证明是官方要求的“成为机会概率”，负责人需批准置信度转换或逐记录值。模板缺失、表头不符、审批未通过、任一REVIEW未决、重复ID或非法类别都会硬阻断。
''',
'task234_consistency_report.md':'''# Task 2/3/4版本一致性

新增`scripts/recompute_task34_stage3e4.py`。它只接受已批准且校验通过的result2候选，读取其中全部机会1，再生成独立Task3/4候选目录；不覆盖历史42条/5簇、40组聚类实验或90行评分实验。

校验包括：result3只引用result2机会1、cluster_id唯一、簇内计数可重算、类别合法；result4主题集合与result3完全一致。新result3使用官方表头`来源覆盖/簇内机会记录`，不沿用历史非官方列名。

当前因正式result2不存在，真实Task3/4重算入口已准备但未运行。原C004继续作为历史基线，在已确认推荐视图暂停；新流程不强行保留C004。候选主题名标记`needs_theme_review`，需郭审核语义与重复命名后才能宣称有效。
''',
'stage3e4_zhao_integration_contract.md':'''# 赵的Stage3E-4集成契约

## 当前可读（实验/历史）

- `data/frozen/result1_Final_All.csv`：1984冻结底表。
- `results/stage3e1/`：v1机器判断和历史Task3/4。
- `results/stage3e2/`：v2实验判断。
- `docs/research_stage3/stage3e3/`：郭42聚合、聚类/评分实验报告。
- `experiments/stage3e4/stage3e4_run_summary.json`：无原文聚合状态。

## 当前不可作为正式提交

全量result2、基于最终机会集合的result3/result4、人工验证的高价值排名。Web系统继续保持v1.1稳定接口，不切换。

## 批准后的切换

负责人审批JSON → `export_official_stage3e4.py`生成候选 → 哈希/Schema验收 → `recompute_task34_stage3e4.py`生成Task3/4候选 → 主题人工审查 → 提交目录发布。切换时需传递文件SHA256、schema、数据/算法/审批版本和`submission_ready=true`；回滚只需恢复上一版本清单，不覆盖历史文件。
''',
'stage3e4_tests.md':'''# Stage3E-4测试与复现

执行命令：

```powershell
python scripts/run_stage3e4.py
python -m unittest tests.test_stage3e4 -v
python scripts/validate_stage3e4.py
python scripts/export_official_stage3e4.py --template "E:\\xwechat_files\\wxid_r4to3bbty1yu22_ff68\\msg\\file\\2026-11\\result2.csv"
```

单元测试5项全部通过：审批门控、逐记录决定、合法批准构建、重复/非法标签、Task3引用非机会阻断。真实数据验证13项全部通过：冻结主表1984唯一及哈希、601集合、未预填标签、审批待定、正式文件不存在、8条专项误差、27条高优先补证、汇总一致、郭42与源队列/v2哈希未变、补证状态未夸大、Task3/4入口存在。合计18项通过。

导出命令按预期以非零状态阻断，证明未批准规则不会生成正式结果。尚未执行“已批准版本重复运行一致性”，因为当前没有获批输入；这不是伪造通过项，待审批后执行。原始证据核验状态校验目前依赖审批数据结构，后续应在证据增量层加入快照哈希时扩展。
''',
'remaining_blockers.md':'''# 剩余阻断与责任

1. **负责人**：批准A/B/C政策；若选C，批准具体规则版本与record_id集合；不得口头全局映射。
2. **负责人/郭**：完成高影响记录与剩余锁定84条盲审；42条只能作开发校准。
3. **负责人**：批准官方机会置信度语义和生成方式。
4. **数据工程**：审批后生成候选result2并重复运行哈希校验；当前阻断601条。
5. **郭/负责人**：审核新Task3主题语义、独立来源和重复命名。
6. **赵**：仅在`submission_ready=true`清单发布后切换系统；当前保持v1.1。
7. **Task1提交负责人**：处理冻结result1与官方模板列名差异，不能修改冻结研究主表本体。

截止风险：若不批准任何小范围规则且不补完人工复核，11月20日前无法合法生成全量result2，也不能生成版本一致的正式result3/result4。
''',
'stage3e4_acceptance_report.md':'''# 阶段3E-4验收报告

状态：**工程准备完成，正式提交被审批门控阻断**。

- 官方原件全部找到并核验；冻结主表SHA256保持`44C75335...FF0A52`。
- 601条队列与v2 REVIEW集合精确一致，六组数量439/100/31/3/16/12；未写任何正式标签。
- 供给宣传宽规则和泛化问题规则均与人工正例冲突；收窄27条规则只建议审批，不自动执行。
- 5条公开原始GitHub页面访问成功，但没有足以自动解决D3的新增证据；27条高优先队列已建立。
- 郭12条机会中8条被v2转为REVIEW，显示当前D3/D6门控有系统性漏判风险。
- 非破坏性result2导出和Task3/4重算入口已完成；正式result2未生成，Task3/4未越权重算。
- 18项自动检查通过；审批后重复运行一致性仍待执行。

推荐负责人批准方案C，并先审27条收窄规则候选与27条高影响补证队列。现阶段不能宣称正式result2/result3/result4完成。
'''
}
for name,text in docs.items(): (D/name).write_text(text,encoding='utf-8')

files=sorted([p for p in D.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt']+[p for p in E.iterdir() if p.is_file()])
(D/'SHA256SUMS.txt').write_text('\n'.join(f"{sh(p)}  {p.relative_to(ROOT).as_posix()}" for p in files)+'\n',encoding='utf-8')
print(json.dumps({'documents':len(docs),'manifest':str(E/'official_material_manifest.json'),'sha_entries':len(files)},ensure_ascii=False))
