import os
import sys
import subprocess

# 40 个极其垂直的教育 AI 痛点关键词矩阵
KEYWORDS = [
    "AI辅导", "智能批改", "作业求助", "实验报告", "个性化学习", "错题本", "知识点讲解", 
    "AI备课", "教案生成", "课件制作", "论文润色", "文献阅读", "AI口语", "听力练习", 
    "教学设计", "课堂互动", "翻转课堂", "智能助教", "排错求助", "代码实操", 
    "虚拟仿真实验", "实验故障", "教育大模型", "学习机", "智慧课堂", "学情分析", 
    "自适应学习", "自动出题", "智能组卷", "考试分析", "家校沟通", "招生咨询", 
    "教育机器人", "编程启蒙", "STEAM教育", "教育知识图谱", "多模态教学", "AI班主任", 
    "学术写作", "文献综述"
]

BATCH_NAME = "MEGA01" # 如果你跑完了想继续抓，改成 MEGA02, MEGA03...

def run_harvest():
    print(f"准备启动巨量采集，批次号: {BATCH_NAME}")
    
    # 为了方便 API 不被封，我们把 40 个词分成 8 组，每组 5 个词
    chunk_size = 5
    for i in range(0, len(KEYWORDS), chunk_size):
        chunk = KEYWORDS[i:i+chunk_size]
        query_str = ",".join(chunk)
        print(f"\n正在抓取关键词组: {query_str}")
        
        # 调用底层的抓取脚本
        cmd = [
            sys.executable, "scripts/build_result1.py",
            "--queries", query_str,
            "--batch", f"{BATCH_NAME}_part{i//chunk_size + 1}",
            "--limit", "20" # 每个词在每个平台抓 20 条
        ]
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode != 0:
            print(f"⚠️ 关键词组 {query_str} 抓取出现异常，请留意网络。")
            
    print("\n✅ 巨量采集完成！请前往 results/ 目录查看新增的批次数据。")

if __name__ == "__main__":
    run_harvest()