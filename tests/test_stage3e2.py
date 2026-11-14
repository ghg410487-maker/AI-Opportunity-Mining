import unittest
from edumine.stage3e2 import evidence_level, judge_task2_v2, review_root_cause

class Stage3E2Tests(unittest.TestCase):
    def rec(self,text):return {'记录编号':'X','来源网站名称':'S','来源链接':'u','内容':text}
    def test_evidence_levels(self):
        self.assertEqual(evidence_level(''),'EMPTY_CONTENT')
        self.assertEqual(evidence_level('短标题'),'TITLE_LIKE')
    def test_supply_not_authentic_demand(self):
        r=self.rec('本产品发布AI教学平台，功能包括自动生成教案，赋能教师。')
        d=judge_task2_v2(r)
        self.assertEqual(d['dimension_scores']['demand_authenticity'],0)
        self.assertTrue(d['flags']['supply_only'])
    def test_direct_demand(self):
        r=self.rec('一线教师反馈批改作业耗时、负担重，我们需要AI自动批改工具。')
        d=judge_task2_v2(r)
        self.assertEqual(d['dimension_scores']['demand_authenticity'],2)
        self.assertGreaterEqual(d['dimension_scores']['problem_clarity'],1)
    def test_root_cause_multilabel(self):
        s={'education_relevance':1,'problem_clarity':0,'demand_authenticity':0,'ai_core':0,'feasibility':1,'unmet_degree':0}
        primary,causes=review_root_cause(s,'短标题')
        self.assertEqual(primary,'TRUE_INDETERMINATE')
        self.assertIn('TEXT_INSUFFICIENT',causes)

if __name__=='__main__':unittest.main()
