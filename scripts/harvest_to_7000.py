import os
import sys
import subprocess
import time

# 这是一个包含 100 个极其垂直、长尾的教育痛点关键词词库
KEYWORDS_POOL = [
    "AI辅导", "智能批改", "作业求助", "实验报告", "个性化学习", "错题本", "知识点讲解", 
    "AI备课", "教案生成", "课件制作", "论文润色", "文献阅读", "AI口语", "听力练习", 
    "教学设计", "课堂互动", "翻转课堂", "智能助教", "排错求助", "代码实操", 
    "虚拟仿真实验", "实验故障", "教育大模型", "学习机", "智慧课堂", "学情分析", 
    "自适应学习", "自动出题", "智能组卷", "考试分析", "家校沟通", "招生咨询", 
    "教育机器人", "编程启蒙", "STEAM教育", "教育知识图谱", "多模态教学", "AI班主任", 
    "学术写作", "文献综述", "AI心理辅导", "学生心理测评", "防作弊系统", "智慧图书馆",
    "校园安全监控", "招生推荐", "就业指导", "排课系统", "考勤系统", "课堂点名",
    "英语四六级", "考研辅导", "雅思托福", "数学解题", "物理仿真", "化学实验",
    "生物模型", "地理信息系统", "历史问答", "语文阅读理解", "作文批改", "古诗文背诵",
    "Python教学", "Java教学", "C++评测", "算法可视化", "数据结构图", "前端教学",
    "机器学习入门", "深度学习指导", "数据科学实战", "统计学科普", "高数答疑", "线代辅导",
    "课程推荐", "选课系统", "成绩预测", "毕业设计", "开题报告", "答辩PPT生成",
    "教师培训", "教学能力评估", "公开课点评", "微课制作", "说课稿", "板书生成",
    "听写测试", "英语作文", "物理错题", "化学方程式", "生物笔记", "政治主观题",
    "历史时间轴", "地理读图", "特教辅助", "手语翻译", "盲文转换", "自闭症干预"
]

BATCH_PREFIX = "SUPER" # 批次名前缀
TOTAL_KEYWORDS = len(KEYWORDS_POOL)
CHUNK_SIZE = 5 # 每次抓 5 个词

print(f"🚀 启动终极爆兵模式！共 {TOTAL_KEYWORDS} 个长尾关键词。")
print(f"预计将生成 {TOTAL_KEYWORDS // CHUNK_SIZE} 个批次，总抓取量极大，请保持网络畅通！")

part_num = 1
for i in range(0, TOTAL_KEYWORDS, CHUNK_SIZE):
    chunk = KEYWORDS_POOL[i:i+CHUNK_SIZE]
    query_str = ",".join(chunk)
    batch_name = f"{BATCH_PREFIX}_part{part_num}"
    
    print(f"\n[{part_num}/{TOTAL_KEYWORDS // CHUNK_SIZE}] 正在抓取：{query_str}")
    
    # 调用主程序，每次抓取 10 个平台，每个平台每个词 20 条
    cmd = [
        sys.executable, "scripts/build_result1.py",
        "--queries", query_str,
        "--batch", batch_name,
        "--limit", "20"
    ]
    
    subprocess.run(cmd)
    
    part_num += 1
    print(f"批次 {batch_name} 完成。休眠 3 秒防止被封 IP...")
    time.sleep(3)

print("\n🎉 全部 100 个关键词抓取完毕！请运行合并脚本处理海量数据！")