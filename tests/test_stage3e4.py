import unittest

from edumine.stage3e4 import build_official_result2, validate_result2, validate_task34


class Stage3E4Tests(unittest.TestCase):
    def setUp(self):
        self.master = [{"采集批次号": "B1", "记录编号": "R1"}]
        self.machine = [{"record_id": "R1", "opportunity_status": "REVIEW"}]
        self.stable = [{"record_id": "R1", "opportunity_confidence": "0.7"}]

    def test_owner_gate_blocks(self):
        rows, errors = build_official_result2(self.master, self.machine, self.stable, [], {"approval_status": "PENDING_APPROVAL"}, {"教学辅助"}, {"教育"})
        self.assertIsNone(rows); self.assertEqual(errors, ["owner_approval_not_approved"])

    def test_review_requires_record_decision(self):
        approval = {"approval_status": "APPROVED_BY_OWNER", "record_decisions": []}
        rows, errors = build_official_result2(self.master, self.machine, self.stable, [], approval, {"教学辅助"}, {"教育"})
        self.assertIsNone(rows); self.assertIn("R1:review_unresolved", errors)

    def test_approved_record_builds(self):
        approval = {"approval_status": "APPROVED_BY_OWNER", "record_decisions": [{"record_id": "R1", "final_label": "1", "decision_basis": "owner", "official_confidence": "0.8", "function_category": "教学辅助", "industry": "教育"}]}
        rows, errors = build_official_result2(self.master, self.machine, self.stable, [], approval, {"教学辅助"}, {"教育"})
        self.assertFalse(errors); self.assertEqual(rows[0]["是否构成机会"], "1")

    def test_result2_rejects_duplicate_and_illegal(self):
        rows = [{"记录编号": "R1", "是否构成机会": "REVIEW", "机会置信度": "2", "功能类别": "x", "所属行业": "x"}] * 2
        errors = validate_result2(rows, ["R1"], {"教学辅助"}, {"教育"})
        self.assertTrue(any("duplicate" in x for x in errors)); self.assertTrue(any("illegal_label" in x for x in errors))

    def test_task34_rejects_non_opportunity(self):
        r2 = [{"记录编号": "R1", "是否构成机会": "0"}]
        r3 = [{"主题簇编号": "C1", "簇内机会记录": "R1", "簇内机会记录数": "1", "功能类别": "教学辅助", "所属行业": "教育"}]
        r4 = [{"主题簇编号": "C1"}]
        errors = validate_task34(r2, r3, r4, {"教学辅助"}, {"教育"})
        self.assertIn("C1:references_non_opportunity", errors)


if __name__ == "__main__": unittest.main()
