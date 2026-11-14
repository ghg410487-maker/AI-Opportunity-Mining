import unittest
from edumine.stage3e3 import hybrid_vectors,kendall_tau,rand_index,silhouette_proxy
class Stage3E3Tests(unittest.TestCase):
    def test_hybrid(self):
        x=hybrid_vectors(['教师批改作业耗时，需要人工智能自动批改','普通新闻文本'])
        self.assertEqual(len(x),2);self.assertAlmostEqual(sum(v*v for v in x[0].values()),1,places=6)
    def test_rank_metrics(self):
        self.assertEqual(kendall_tau(['a','b','c'],['a','b','c']),1)
        self.assertEqual(kendall_tau(['a','b','c'],['c','b','a']),-1)
        self.assertEqual(rand_index([0,0,1],[1,1,0]),1)
    def test_silhouette_shape(self):
        self.assertIsInstance(silhouette_proxy([{0:1},{0:.9},{1:1},{1:.9}],[0,0,1,1]),float)
if __name__=='__main__':unittest.main()
