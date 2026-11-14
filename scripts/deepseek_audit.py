import json
import os

OUT_DIR = "docs/research_stage3/stage3d2"
os.makedirs(OUT_DIR, exist_ok=True)

manifest = {
    "provider": "DeepSeek",
    "endpoint": "https://api.deepseek.com/v1/chat/completions",
    "exact_model_id": "deepseek-chat",
    "temperature": 0.1,
    "top_p": 1.0,
    "max_tokens": 4096,
    "seed": "unsupported",
    "response_format": "json_object",
    "historical_log_status": "NOT_RECOVERABLE",
    "historical_log_note": "42条T0试跑时的原始HTTP请求与响应未完整落盘，无法恢复具体Request ID。",
    "prompt_version": "T0_draft_v0.2",
    "prompt_sha256": "请运行前计算并填入",
}

with open(f"{OUT_DIR}/deepseek_run_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=4)

with open(f"{OUT_DIR}/deepseek_run_audit.md", "w", encoding="utf-8") as f:
    f.write("# DeepSeek T0 试判运行审计\n\n")
    f.write("## 一、模型与参数配置\n")
    for k, v in manifest.items():
        f.write(f"- **{k}**：{v}\n")
    f.write("\n## 二、历史缺失材料清单\n")
    f.write("- 原始 HTTP Request ID 与响应体：NOT_RECOVERABLE\n")
    f.write("- 精确 Token 消耗记录：历史批次由于未开启详细日志，无法复算\n")
    f.write("\n## 三、改进措施\n")
    f.write("- 后续 1984 条全量运行将强制开启本地 API 日志记录，保存所有请求与 Token 用量。\n")

print(f"✅ DeepSeek 运行审计已生成 -> {OUT_DIR}")