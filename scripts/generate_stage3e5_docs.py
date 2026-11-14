from __future__ import annotations
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/research_stage3/stage3e5';E=ROOT/'experiments/stage3e5';P=ROOT/'experiments/datasets/stage3e5';D.mkdir(parents=True,exist_ok=True)
SRC=Path(r'E:\xwechat_files\wxid_r4to3bbty1yu22_ff68\msg\file\2026-11')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,fields=None):
    fields=fields or list(rows[0]);
    with Path(p).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
s=json.loads((E/'stage3e5_summary.json').read_text(encoding='utf-8'));m1=s['metrics']['v1'];m2=s['metrics']['v2']
def pct(x):return f'{100*x:.2f}%'

boundary=read(P/'human_positive14_boundary_review.csv');write(D/'human_positive14_boundary_review.csv',boundary)
q=read(P/'review601_stage3e5_private.csv');qpub=[{'record_id':x['record_id'],'v2_original_label':x['v2_original_label'],'evidence_level':x['evidence_level'],'source_name':x['source_name'],'disposition_group':x['disposition_group'],'human126_overlap':x['human126_overlap'],'human126_label':x['human126_label'],'owner_approval_status':x['stage3e5_review_status'],'final_official_label':''} for x in q];write(D/'review601_latest_queue.csv',qpub)
w=read(P/'narrow_exclusion27_owner_workbench_private.csv');wpub=[{'record_id':x['record_id'],'source_name':x['source_name'],'evidence_level':x['evidence_level'],'content_sha256':x['content_sha256'],'human126_label':x['human126_label'],'proposed_rule_label':x['proposed_label'],'owner_final_label':'','owner_final_reason':'','approval_status':'PENDING_APPROVAL'} for x in w];write(D/'owner_pending_narrow27.csv',wpub)

docs={
'human126_ingestion_report.md':f'''# 126条人工评价接入报告

四份正式输入均已实际读取。84条提交CSV SHA256为`{s['input84_sha256']}`，与指定值一致；84行、7列，eval_id与record_id各84个唯一。它们全部属于锁定126，且与原42条零重叠。

郭收到的XLSX SHA256为`{s['xlsx_sha256']}`。XLSX与此前发放CSV格式不同，但84个ID和可比不可修改字段一致，差异数为0。样本身份仍以锁定manifest为准。84条统计说明SHA256为`E18EA621204A1C01653EA7646172EC7D08A03DF216BE18A52EE585F5A56D874A`；5簇解释报告SHA256为`B3A05FDB20FF0C597924B4CC1FB8DAD7B63F912AE1D6269544FB30DBC04B5369`。

合并层保留原始`VERIFIED`，另以派生字段规范化为`COMPLETED`。合并结果为14条机会、98条非机会、14条INSUFFICIENT；私有派生文件SHA256为`{s['combined_sha256']}`。原42、原84、XLSX和锁定manifest均未修改。
''',
'v1_v2_weighted_human_evaluation.md':f'''# v1/v2人工评价

## 三个口径

1. 完整126条状态：14机会、98非机会、14证据不足，可判覆盖率112/126={pct(112/126)}。
2. 112条可判记录的选择性评价：REVIEW保持弃权，不把它并入0。
3. 设计加权估计：使用锁定manifest的sample_weight。仅在“层内抽样可代表对应层、且可判缺失机制可接受”的前提下解释；14条不可判集中于空正文，因此不能宣称无偏总体性能。

| 指标 | v1 | v2 |
|---|---:|---:|
| TP/FP/TN/FN（仅机器已判1/0） | 12/29/28/1 | 4/8/28/2 |
| REVIEW中人工1/0 | 1/41 | 8/62 |
| 选择性覆盖率（112） | {pct(m1['selective_coverage_112'])} | {pct(m2['selective_coverage_112'])} |
| 条件Precision | {pct(m1['conditional_precision'])} | {pct(m2['conditional_precision'])} |
| 条件Recall | {pct(m1['conditional_recall'])} | {pct(m2['conditional_recall'])} |
| 条件F1 | {pct(m1['conditional_f1'])} | {pct(m2['conditional_f1'])} |
| 设计加权条件Precision | {pct(m1['weighted_conditional_precision'])} | {pct(m2['weighted_conditional_precision'])} |
| 设计加权条件Recall | {pct(m1['weighted_conditional_recall'])} | {pct(m2['weighted_conditional_recall'])} |
| 设计加权条件F1 | {pct(m1['weighted_conditional_f1'])} | {pct(m2['weighted_conditional_f1'])} |

v2的未弃权Precision略升，但覆盖率由62.5%降到37.5%，且8条人工机会被置于REVIEW；不能把“更少输出”解释成算法全面提升。v1/v2均使用了原42条作规则开发校准，指标存在开发集偏倚，不是完全独立泛化性能。

新增84条揭示的新模式：v1非机会层出现1个人工机会和13个空内容不可判；v1 REVIEW层42条中41条明确为0、1条为1。REVIEW并非机会池，但也不能整体归0。
''',
'insufficient14_sensitivity.md':'''# 14条INSUFFICIENT与敏感性分析

14条均保持独立状态。v1中13条预测0、1条预测1；v2中13条预测0、1条REVIEW。13条新增不可判主要是空正文、占位符或极短标题，缺失具有明显选择性。

在112条可判样本上报告的指标只适用于“人工可判记录”。情景分析而非真实标签：

- 若14条全部真实为0，v1的Precision从29.27%降至28.57%，Recall仍为92.31%；v2的已判子集指标不变，另增加1个REVIEW负例。
- 若14条全部真实为1，v1 Precision为30.95%、Recall降至48.15%；v2 Precision仍33.33%、Recall降至21.05%，另增加1个REVIEW正例。

这两个极端场景只展示缺失影响范围，不能当作统计置信区间。空正文集中在原机器0层，使简单删除INSUFFICIENT可能高估或低估整体表现。
''',
'positive14_boundary_review.md':'''# 14条人工正例边界审核

独立审核表见`human_positive14_boundary_review.csv`，保留郭原始标签与理由，负责人字段为空。

优先裁决四条供给方自述案例：`SUPER_part10-S00275`、`B12-S00181`、`B11-S00550`、`B12-S00013`。统一问题是：教育任务清楚，但痛点与效果主要由供给方陈述，缺少用户反馈。建议把“候选机会相关性”和“需求真实性/证据强度”分层：如AI为核心且任务、问题明确，可保留候选1，同时将D3证据等级标为供给方自述；若AI只是普通可视化或数字化工具，应判0。

Codex未修改任何人工标签。最终变更只能写入独立负责人裁决列。
''',
'cluster5_official_review_ingestion.md':f'''# 郭5簇正式审核接入

正式CSV SHA256为`{s['cluster_review_sha256']}`。5个cluster_id唯一，机器记录合计42；人工汇总12机会、29非机会、1证据不足，与42条审核完全一致。机器字段和原result3/result4未修改。

- C001：4/7，改名候选，单一来源风险。
- C002：3/14，改名候选，并与C001检查重叠。
- C003：1/7，暂停独立高价值主题，可作单条案例。
- C004：0/5，正式暂停已确认机会推荐。
- C005：4/9另1条不足，需拆分后再做语义聚类验证。

这些意见只形成“人工支持关系”，不能通过删除29条负例后改写旧簇规模来伪装正式聚类。正式Task3仍需从最终result2的机会1集合重新计算。
''',
'machine_ranking_vs_human_support.md':'''# 机器排名与人工支持对照

| 簇 | 机器分 | 人工确认率 | 结论 |
|---|---:|---:|---|
| C001 | 6.28 | 4/7=57.1% | 机器最低分但确认率最高；单一来源 |
| C002 | 94.38 | 3/14=21.4% | 机器最高分但大多数被否定 |
| C003 | 34.28 | 1/7=14.3% | 主题不成立 |
| C004 | 46.40 | 0/5=0% | 暂停推荐 |
| C005 | 63.35 | 4/9=44.4%，另1不足 | 语义混杂，需拆分 |

机器分与人工确认度明显不一致。该观察说明现有Task4分数衡量机器特征组合，而不是经过人工验证的机会真实性；样本只有5簇，不能报告相关性显著性或外推普遍规律。
''',
'review601_stage3e5_report.md':f'''# 601条最新处置

601条v2 REVIEW集合未改变，负责人已批准方案C路线，但尚未批准任何具体记录的最终0/1。因此当前负责人批准数为0，仍待批准601。

新126人工结果提供了额外校准：31条宽供给规则与人工重叠12条，其中11个0、1个1；3条泛化规则重叠3条，为2个0、1个1。两条宽规则仍不可自动执行。

收窄27条全部具有非空冻结内容和内容SHA256；与126人工重叠9条，9条均为0。这使规则证据比阶段3E-4更强，但仍只是负责人审批候选。逐条状态见`review601_latest_queue.csv`，所有正式标签为空。
''',
'narrow27_rule_review.md':'''# 27条收窄排除规则复核

27条逐条保留来源、证据等级、冻结内容SHA256和私有证据摘录。规则定义仍为：已进入供给宣传候选，且当前文本无强痛点信号。

复核结果：27/27有非空内容；9条命中126人工评价且全部为0；未发现新增人工正例冲突。建议负责人审批时逐条确认“AI产品供给描述”与“明确用户痛点/行动”是否确实缺失。未批准前全部保持REVIEW。

公开审批表`owner_pending_narrow27.csv`不含第三方正文；私有工作台包含短证据摘录及内容哈希，保存在Git忽略目录。
''',
'high_impact_evidence_report.md':'''# 高影响补证报告

沿用阶段3E-4的27条高影响队列和5条公开原始页试验。本轮126人工结果没有授权将补证未完成项自动二值化。5条页面均可访问，但恢复信息主要支持产品用途，未充分建立D3真实需求。

优先顺序保持：直接用户求助/机构行动证据优先于产品功能自述；标题和短正文优先补取；与人工正例相似的教师、学生具体任务优先。补证只进入独立增量层，不回写冻结主表。
''',
'owner_pending_decisions.md':'''# 负责人待审批清单

1. 审批27条收窄供给规则候选的逐条0/REVIEW结论。
2. 统一裁决4条供给方自述人工正例的边界口径，并决定是否保留“候选1+低D3证据”等分层表达。
3. 决定剩余574条REVIEW的补证与人工批次，不允许全局默认0。
4. 批准官方机会置信度语义和生成方法。
5. 审批C001/C002改名、C003/C004暂停、C005拆分；正式聚类仍须等待最终result2。

机器可用表：`owner_pending_narrow27.csv`和`human_positive14_boundary_review.csv`。所有负责人最终字段为空。
''',
'task234_final_linkage_readiness.md':'''# Task2/3/4正式联动准备

阶段3E-4导出器和重算入口保持不变。正式result2仍要求1984全覆盖、唯一ID、合法0/1、0—1置信度、附件1类别、审批版本和输入/输出哈希。

当前601条没有获批二值结论，因此正式result2不可发布。Task3不能用旧42条簇删负例代替重算；必须读取正式result2中的全部机会1。Task4再以正式Task3主题评分。C004不会被强制保留。

赵的v1实验接口继续不变。新数据交接必须携带文件路径、SHA256、schema版本、审批版本和`submission_ready`标志。
''',
'branch_and_zhao_integration_status.md':'''# 分支与赵的集成状态

核验时远端状态：`main=bdaa4db`，`dev=38b62fb`。用户提供的`integration/stage3e4@8458abd`已不是远端当前尖端；实际远端`integration/stage3e4=473ef57`，共同基线为`bab6db8`。

integration分支包含赵的Web、提交包和切换脚本等大量独立变更；dev新增阶段3E-4审批门控。两者存在真实分支分叉，本轮未合并、未覆盖赵的接口。向赵交付阶段3E-5时应以新的dev提交哈希为算法资料版本，并由赵选择性合入报告/接口，不应把整个研究分支直接覆盖integration。
''',
'stage3e5_acceptance_and_tests.md':'''# 阶段3E-5验收与测试

15项真实数据检查全部通过：84文件哈希、126双ID、14/98/14分布、原始状态保留、XLSX/CSV身份一致、601集合及待批状态、27条唯一且未审批、14条不足、14条正例、5簇12/29/1、正式result2不存在、冻结主表哈希、阶段3E-4导出器保留。

复现命令：

```powershell
python scripts/run_stage3e5.py
python scripts/validate_stage3e5.py
python scripts/generate_stage3e5_docs.py
```

私有逐条映射、人工理由和证据摘录位于Git忽略目录；公开报告只保留必要统计和不含第三方原文的审批表。
'''
}
for n,t in docs.items():(D/n).write_text(t,encoding='utf-8')
files=sorted(p for p in D.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt')
(D/'SHA256SUMS.txt').write_text('\n'.join(f'{sha(p)}  {p.relative_to(ROOT).as_posix()}' for p in files)+'\n',encoding='utf-8')
print(json.dumps({'docs':len(docs),'public_csv':3,'sha_entries':len(files)},ensure_ascii=False))
