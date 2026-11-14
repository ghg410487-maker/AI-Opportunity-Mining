import csv, hashlib, json, tempfile, unittest
from pathlib import Path
from edumine.core import analyze, audit, connect, deduplicate, import_file, normalized_text, report
from edumine.normalization import classify_short, clean_content, normalize_all, parse_heat_metrics

class EduMineTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.db=connect(self.root/"test.db"); self.csv=self.root/"B15.csv"
        rows=[
          {"record_id":"R1","source_name":"forum","source_url":"https://x.test/a","published_at":"2026-01-01","collected_at":"2026-01-02","content":"教师希望使用人工智能自动生成形成性反馈，减少重复批改时间并保留个性化建议。","scene_primary":"S1","e_type":"E1","quality_level":"Q3","review_status":"HUMAN_CONFIRMED"},
          {"record_id":"R2","source_name":"news","source_url":"https://x.test/a","published_at":"bad-date","collected_at":"2026-01-02","content":"教师希望使用人工智能自动生成形成性反馈，减少重复批改时间并保留个性化建议。","scene_primary":"S1","e_type":"E2","quality_level":"Q2","review_status":"MACHINE_PRECLASSIFIED"},
          {"record_id":"R3","source_name":"forum","source_url":"","published_at":"2026-01-03","collected_at":"","content":"<script>window.bad=true</script>","scene_primary":"","e_type":"","quality_level":"Q0","review_status":""},
          {"record_id":"R4","source_name":"paper","source_url":"https://x.test/b","published_at":"2026-01-04","collected_at":"2026-01-05","content":"学生需要在虚拟实验环境中得到即时操作提示，并能重复练习危险实验流程与关键步骤。","scene_primary":"S3","e_type":"E3","quality_level":"Q4","review_status":"HUMAN_CONFIRMED"},]
        with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
        self.before=hashlib.sha256(self.csv.read_bytes()).hexdigest()
    def tearDown(self): self.db.close(); self.tmp.cleanup()
    def test_pipeline(self):
        first=import_file(self.db,self.csv); second=import_file(self.db,self.csv)
        self.assertEqual((first["raw_rows"],first["success_rows"]),(4,4)); self.assertTrue(second["protected"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM records").fetchone()[0],4)
        self.assertEqual(self.db.execute("SELECT original_record_id FROM records WHERE record_id='R1'").fetchone()[0],"R1")
        self.assertEqual(hashlib.sha256(self.csv.read_bytes()).hexdigest(),self.before)
        a=audit(self.db); self.assertIn("SCRIPT_RESIDUE",a["by_type"]); self.assertIn("DUPLICATE_URL",a["by_type"])
        d=deduplicate(self.db); self.assertGreaterEqual(d["by_type"]["URL_EXACT"],1); self.assertGreaterEqual(d["by_type"]["CONTENT_SHA256"],1)
        stats=analyze(self.db); self.assertEqual(stats["scenes"]["S1"],2); self.assertEqual(stats["evidence_types"]["E1"],1)
        self.assertEqual(report(self.db,self.root/"reports")["files"],9)

    def test_csv_chinese_field_mapping(self):
        p=self.root/"real.csv"
        with p.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["采集批次号","记录编号","来源网站名称","来源链接","内容","采集时间","热度指标（点赞数、评论数、收藏数、转发量等）"]); w.writeheader(); w.writerow({"采集批次号":"B10","记录编号":"B10-X1","来源网站名称":"教育论坛","来源链接":"https://example.test/1","内容":"测试字段映射正文内容足够长，用来确认中文列能够无损进入内部结构。","采集时间":"2026-01-01","热度指标（点赞数、评论数、收藏数、转发量等）":"{}"})
        import_file(self.db,p); r=self.db.execute("SELECT * FROM records WHERE record_id='B10-X1'").fetchone()
        self.assertEqual((r["batch_id"],r["source_name"],r["original_record_id"]),("B10","教育论坛","B10-X1"))

    def test_jsonl_import_and_invalid_line(self):
        p=self.root/"B16.jsonl"; p.write_text(json.dumps({"record_id":"J1","source_name":"x","source_url":"https://x.test/j","content":"JSONL 正文内容足够长，用于验证逐行对象能够被正常导入且编号不丢失。","collected_at":"2026-01-01"},ensure_ascii=False)+"\n{bad json}\n",encoding="utf-8")
        result=import_file(self.db,p)
        self.assertEqual((result["raw_rows"],result["success_rows"],result["invalid_rows"]),(2,1,1))

    def test_empty_content_audit(self):
        p=self.root/"empty.csv"
        with p.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["record_id","source_name","source_url","content","collected_at"]); w.writeheader(); w.writerow({"record_id":"E0","source_name":"x","source_url":"https://x.test/e","content":"","collected_at":"2026-01-01"})
        import_file(self.db,p,"B17"); self.assertIn("EMPTY_CONTENT",audit(self.db,"B17")["by_type"])

    def test_html_cleaning(self):
        self.assertEqual(normalized_text("<p>教师&nbsp;反馈</p>"),"教师反馈")

    def test_abnormal_time_audit(self):
        p=self.root/"time.csv"
        with p.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["record_id","source_name","source_url","content","collected_at","published_at"]); w.writeheader(); w.writerow({"record_id":"T0","source_name":"x","source_url":"https://x.test/t","content":"用于时间异常专项测试的正文内容，长度超过短文本阈值以隔离时间规则。","collected_at":"not-a-date","published_at":"not-a-date"})
        import_file(self.db,p,"B18"); result=audit(self.db,"B18")
        self.assertIn("ABNORMAL_PUBLISHED_AT",result["by_type"]); self.assertIn("ABNORMAL_COLLECTED_AT",result["by_type"])

    def test_python_literal_heat_to_json_preserves_values(self):
        result=parse_heat_metrics("{'stars': 29540, 'views': 0, 'shares': None}","GitHub")
        metrics={x["metric_name"]:x for x in result["metrics"]}
        self.assertEqual(result["source_format"],"PYTHON_LITERAL"); self.assertEqual(metrics["stars"]["value"],29540)
        self.assertEqual(metrics["views"]["status"],"ZERO"); self.assertEqual(metrics["shares"]["status"],"NULL")

    def test_script_cleaning_and_comparison_storage(self):
        cleaned,actions=clean_content("window.webAbTest={'x':1}")
        self.assertEqual(cleaned,""); self.assertEqual(actions[0]["action"],"REMOVE_SCRIPT_ONLY_CONTENT")
        import_file(self.db,self.csv); normalize_all(self.db)
        row=self.db.execute("SELECT n.raw_content,n.cleaned_content,n.cleaning_actions FROM normalizations n JOIN records r ON r.pk=n.record_pk WHERE r.record_id='R3'").fetchone()
        self.assertIn("window.bad",row["raw_content"]); self.assertNotIn("window.bad",row["cleaned_content"]); self.assertTrue(row["cleaning_actions"])

    def test_distinct_user_expressions_are_retained(self):
        a="老师批改作文太慢，希望系统帮助提供反馈。"; b="学生希望获得个性化练习推荐和错题解释。"
        self.assertNotEqual(clean_content(a)[0],clean_content(b)[0])

    def test_cleaned_duplicate_and_distinct_expression_relations(self):
        p=self.root/"users.csv"; rows=[
          {"record_id":"U1","source_name":"论坛","source_url":"https://u.test/1","content":"<p>老师批改作文太慢，希望系统帮助提供细致反馈并减少重复劳动。</p>","collected_at":"2026-01-01"},
          {"record_id":"U2","source_name":"论坛","source_url":"https://u.test/2","content":"老师批改作文太慢，希望系统帮助提供细致反馈并减少重复劳动。","collected_at":"2026-01-01"},
          {"record_id":"U3","source_name":"论坛","source_url":"https://u.test/3","content":"学生希望获得个性化练习推荐、错题讲解以及适合自己的学习节奏。","collected_at":"2026-01-01"}]
        with p.open("w",encoding="utf-8",newline="") as f: w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
        import_file(self.db,p,"B19"); normalize_all(self.db); deduplicate(self.db,content_source="cleaned")
        pairs={tuple(r) for r in self.db.execute("SELECT a.record_id,b.record_id FROM duplicate_relations x JOIN records a ON a.pk=x.left_pk JOIN records b ON b.pk=x.right_pk WHERE x.run_id LIKE 'dedup-cleaned-%'")}
        self.assertIn(("U1","U2"),pairs); self.assertNotIn(("U1","U3"),pairs); self.assertNotIn(("U2","U3"),pairs)

    def test_short_text_status(self):
        self.assertEqual(classify_short("教师必看！5款AI工具让备课效率翻倍    知乎专栏","教师必看！5款AI工具让备课效率翻倍 知乎专栏","教育论坛"),"TITLE")
        self.assertEqual(classify_short("我觉得反馈太慢。","我觉得反馈太慢。","教育论坛"),"MEANINGFUL_SHORT_COMMENT")

if __name__ == "__main__": unittest.main()
