from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from edumine.baselines import T0_LABELS, LinearOvR, TfidfVectorizerLite, classification_metrics, stratified_folds, t0_rule_predict
from edumine.competition import RESULT2_HEADER, FUNCTION_LABELS, INDUSTRY_LABELS, load_result1, run_tasks_2_to_5

DATA=ROOT/'data/frozen/result1_Final_All.csv'
EXP=ROOT/'experiments/stage3e1'; RES=ROOT/'results/stage3e1'; DOC=ROOT/'docs/research_stage3/stage3e1'
for p in (EXP,RES,DOC):p.mkdir(parents=True,exist_ok=True)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def load_owner_labels():
    a=read(ROOT/'docs/research_stage3/stage3d/stage3d5/t0_owner_adjudication_v0_3.csv')
    b=read(ROOT/'docs/research_stage3/stage3d/stage3d9/owner_adjudication_26_final.csv')
    rows=[]
    for x in a: rows.append({'record_id':x['record_id'],'text':x['content_snapshot'],'label':x['final_label'],'source_layer':'pilot_owner_v0.3'})
    for x in b: rows.append({'record_id':x['record_id'],'text':x['original_evidence']+' '+x['supplement_text'],'label':x['owner_final_label'],'source_layer':'formal_owner_stage3d9'})
    assert len(rows)==40 and len({x['record_id'] for x in rows})==40
    return rows

def cv_model(rows,kind):
    y=[x['label'] for x in rows]; folds=stratified_folds(y,3); pred=['']*len(rows)
    for fold,test in enumerate(folds):
        train=[i for i in range(len(rows)) if i not in set(test)]
        vec=TfidfVectorizerLite((2,4),6000); Xtr=vec.fit_transform([rows[i]['text'] for i in train]); Xte=vec.transform([rows[i]['text'] for i in test])
        model=LinearOvR(loss='log' if kind=='logreg' else 'hinge',epochs=45,lr=.16 if kind=='logreg' else .08,seed=20261114+fold)
        model.fit(Xtr,[y[i] for i in train])
        for i,p in zip(test,model.predict(Xte)):pred[i]=p
    return pred,classification_metrics(y,pred)

labels=load_owner_labels(); y=[x['label'] for x in labels]
pred_rule=[t0_rule_predict(x['text']) for x in labels]
pred_lr,m_lr=cv_model(labels,'logreg'); pred_svm,m_svm=cv_model(labels,'svm')
metrics={'evaluation_scope':'40 owner-adjudicated development/calibration cases; NOT an unbiased final test set','class_distribution':dict(Counter(y)),'rule':classification_metrics(y,pred_rule),'tfidf_logistic_regression_3fold':m_lr,'tfidf_linear_svm_3fold':m_svm,'label_set':list(T0_LABELS),'limitations':['All 40 cases participated in guideline calibration or adjudication.','UNKNOWN has zero support; its per-class metrics are descriptive zeros.','Small and imbalanced data; metrics are baseline diagnostics only.']}
(EXP/'t0_baseline_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
with (EXP/'t0_oof_predictions.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['record_id','owner_label','rule_prediction','tfidf_logreg_oof','tfidf_svm_oof','evaluation_scope'])
    for x,a,b,c in zip(labels,pred_rule,pred_lr,pred_svm):w.writerow([x['record_id'],x['label'],a,b,c,x['source_layer']])

records=load_result1(DATA); run=run_tasks_2_to_5(records,RES)
resolved=read(RES/'result2_resolved_subset.csv')
compat={'official_headers_expected':list(RESULT2_HEADER),'resolved_subset_header_exact':list(resolved[0])==list(RESULT2_HEADER) if resolved else False,'resolved_subset_rows':len(resolved),'full_input_rows':len(records),'full_coverage':len(resolved)==len(records),'legal_opportunity_values':sorted({x['是否构成机会'] for x in resolved}),'function_values_valid':all((not x['功能类别']) or x['功能类别'] in FUNCTION_LABELS for x in resolved),'industry_values_valid':all((not x['所属行业']) or x['所属行业'] in INDUSTRY_LABELS for x in resolved),'review_mapping':'BLOCK_EXPORT','full_official_result2_ready':run['official_full_export_ready'],'blocker_count':run['official_export_blockers']}
(EXP/'official_csv_compatibility.json').write_text(json.dumps(compat,ensure_ascii=False,indent=2),encoding='utf-8')

manifest={'run_id':'stage3e1-20261114-v1','run_date':'2026-11-14','frozen_input':str(DATA.relative_to(ROOT)),'frozen_input_sha256':sha(DATA),'frozen_input_rows':len(records),'algorithms':{'t0_rule':'keyword_rule_v1','tfidf':'char_2_4gram_max6000','logistic_regression':'dependency_free_ovr_sgd_logloss_epochs45','linear_svm':'dependency_free_ovr_sgd_hinge_epochs45','task2':'six_dimension_rule_v1','task3':'tfidf_char_kmeans_lite','task4':'five_dimension_minmax_weighted','task5':'top5_rule_plan_generator'},'paid_api_calls':0,'llm_extraction':{'implemented_interface':'rule output includes llm_used/cache-ready fields','calls_this_run':0,'policy':'rule first; optional LLM only for REVIEW with schema validation and cache'},'task2':run,'t0_metrics':metrics,'official_csv_compatibility':compat,'outputs_sha256':{}}
for p in sorted(list(EXP.glob('*'))+list(RES.glob('*'))):
    if p.is_file():manifest['outputs_sha256'][str(p.relative_to(ROOT))]=sha(p)
(RES/'run_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

report=f"""# 阶段3E-1真实数据实验报告

## 运行结论

- 冻结输入：`data/frozen/result1_Final_All.csv`，SHA256 `{manifest['frozen_input_sha256']}`，读取{len(records)}条，未修改原文件。
- Task 2：实际逐条处理{run['task2_processed']}条；内部状态分布 `{json.dumps(run['status_distribution'],ensure_ascii=False)}`。
- 结构化抽取：{run['task2_processed']}条，包含用户、任务、痛点、现有方案、证据和来源ID；本轮全部使用规则抽取，付费API/LLM调用为0。
- Task 3：对内部机会状态=1的{run['task3_opportunity_records']}条聚为{run['task3_clusters']}簇。
- Task 4：生成{run['task4_rows']}条主题评分；分数由程序公式计算。
- Task 5：生成{run['task5_recommendations']}个推荐及策划案草稿。

## T0基线性能

评估集为40条负责人已裁决的开发/校准样本，**不是无偏最终测试集**，也不称为完整金标准。

| 基线 | Accuracy | Macro-F1 |
|---|---:|---:|
| 关键词规则 | {metrics['rule']['accuracy']:.4f} | {metrics['rule']['macro_f1']:.4f} |
| TF-IDF + Logistic Regression（3折OOF） | {m_lr['accuracy']:.4f} | {m_lr['macro_f1']:.4f} |
| TF-IDF + Linear SVM（3折OOF） | {m_svm['accuracy']:.4f} | {m_svm['macro_f1']:.4f} |

UNKNOWN在40条中支持数为0；类别明显不平衡。上述数字只用于确认代码可运行和建立基线，不用于宣称最终性能。

## 官方result2兼容性

- 内部映射：`1→官方1`、`0→官方0`、`REVIEW→阻断正式全量导出`。
- 已决子集表头和值域通过检查：{compat['resolved_subset_header_exact'] and compat['function_values_valid'] and compat['industry_values_valid']}。
- 全量正式result2当前是否可导出：{compat['full_official_result2_ready']}；阻断记录数：{compat['blocker_count']}。
- 未把任何REVIEW改成1，也未把已决子集冒充全量正式提交文件。

## 质量边界

T0只判断教育相关性。`EDUCATION_DIRECT`不能直接转成机会=1；Task 2还必须检查问题明确性、需求真实性、AI核心性、可行性和未满足程度。机器规则结果是实验输出，不覆盖人工标注，也不是金标准。
"""
(DOC/'stage3e1_experiment_report.md').write_text(report,encoding='utf-8')

plan="""# 2026-11-20倒排执行计划（阶段3E-1调整版）

## 决策

- 取消144条全面交叉复标作为强制前置条件；stage3D-10准备文件完整保留，可在风险分层复核时使用。
- 竞赛交付主线转为Task 2—5端到端闭环、官方CSV合规、系统MVP和可复现实验。

## 里程碑

| 日期 | 交付 | 验收 |
|---|---|---|
| 11月14日 | Task 2最小真实闭环 | 1984条逐条处理；六维判别；结构化抽取；REVIEW严格阻断；T0三基线可复现 |
| 11月15日 | 聚类和评分初版 | 仅机会=1入簇；result3可追溯；result4可重算；主题人工抽查 |
| 11月16日 | 系统MVP | 查询、筛选、推荐、证据链、策划案下载；接口联调 |
| 11月17日 | 算法改进和错误分析 | REVIEW风险分层；基线对照；聚类稳定性；评分敏感性 |
| 11月18日 | 提交材料预审 | 四CSV、论文、源码、截图、运行说明、AI使用披露、匿名检查 |
| 11月19日 | 冻结 | 仅修阻断缺陷；保存哈希和复现日志 |
| 11月20日 | 正式交付 | 上传并保存凭证 |

## 11月15日前的阻断项

1. REVIEW记录必须通过人工或增强算法定稿，才能生成全量官方result2。
2. 规则抽取对隐含需求和反讽文本能力有限，需抽查高价值簇与REVIEW边界。
3. Task 3/4当前为基础算法；主题命名和权重需要负责人确认及稳定性/敏感性分析。
"""
(DOC/'delivery_countdown_plan.md').write_text(plan,encoding='utf-8')
print(json.dumps({'t0_metrics':{k:{'accuracy':v['accuracy'],'macro_f1':v['macro_f1']} for k,v in [('rule',metrics['rule']),('logreg',m_lr),('svm',m_svm)]},'task2':run,'compatibility':compat},ensure_ascii=False,indent=2))
