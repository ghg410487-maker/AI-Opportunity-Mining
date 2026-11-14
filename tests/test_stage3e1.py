import csv
import tempfile
import unittest
from pathlib import Path

from edumine.baselines import LinearOvR, TfidfVectorizerLite, classification_metrics, t0_rule_predict
from edumine.competition import CachedNeedExtractor, FUNCTION_LABELS, RESULT2_HEADER, extract_need, judge_task2, run_tasks_2_to_5, validate_extraction


class Stage3E1Test(unittest.TestCase):
    def test_t0_is_not_opportunity(self):
        r={"采集批次号":"B","记录编号":"R1","来源网站名称":"x","来源链接":"u","内容":"AI学习工具产品发布，提供课程学习功能。","采集时间":"","热度指标（点赞数、评论数、收藏数、转发量等）":"{}"}
        e=extract_need(r); d=judge_task2(r,e)
        self.assertEqual(d["t0_label"],"EDUCATION_DIRECT")
        self.assertNotEqual(d["opportunity_status"],"1")

    def test_structured_extraction(self):
        r={"记录编号":"R2","来源网站名称":"论坛","来源链接":"u","内容":"老师希望减少重复批改，当前系统反馈滞后，需要AI生成个性化建议。"}
        e=extract_need(r)
        self.assertIn("老师",e["user"]); self.assertTrue(e["pain"]); self.assertTrue(e["evidence_excerpt"])
        self.assertEqual(validate_extraction(e,r),(True,"PASS"))

    def test_llm_fallback_rejects_ungrounded_evidence(self):
        r={"记录编号":"R3","来源网站名称":"论坛","来源链接":"u","内容":"这是一段足够长但没有规则关键词的普通描述，用来触发可选回退接口。"}
        def fake(_):return {"user":"用户","task":"任务","pain":"痛点","existing_solution":"","evidence_excerpt":"源文不存在的证据"}
        with tempfile.TemporaryDirectory() as d:
            e=CachedNeedExtractor(Path(d)/"cache.jsonl",fake).extract(r)
            self.assertTrue(e["validation_status"].startswith("LLM_REJECTED"))

    def test_baseline_fit(self):
        texts=["学生学习课程", "教师批改作业", "公司销售产品", "普通游戏娱乐"]
        y=["EDUCATION_DIRECT","EDUCATION_DIRECT","NON_EDUCATION","NON_EDUCATION"]
        v=TfidfVectorizerLite(max_features=100); X=v.fit_transform(texts); m=LinearOvR(epochs=8).fit(X,y)
        self.assertEqual(len(m.predict(X)),4); self.assertEqual(classification_metrics(y,y)["accuracy"],1)

    def test_result2_review_blocks_full_export(self):
        rows=[{"采集批次号":"B","记录编号":"R1","来源网站名称":"论坛","来源链接":"u","内容":"教师需要AI帮助，但具体问题尚不清楚。","采集时间":"","热度指标（点赞数、评论数、收藏数、转发量等）":"{}"}]
        with tempfile.TemporaryDirectory() as d:
            result=run_tasks_2_to_5(rows,Path(d))
            self.assertEqual(result["task2_processed"],1)
            with (Path(d)/"result2_resolved_subset.csv").open(encoding="utf-8-sig") as f:
                self.assertEqual(next(csv.reader(f)),list(RESULT2_HEADER))

    def test_function_label_domain(self):
        self.assertIn("文本生成",FUNCTION_LABELS)


if __name__=="__main__":unittest.main()
