#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性生成365天菜谱并保存为 meals_365.json
运行一次即可，之后 send_meal.py 直接读取该文件
用法：GEMINI_API_KEY=你的秘钥 python generate_365.py
"""

import os
import json
import time
import google.generativeai as genai

# 获取 Gemini API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OUTPUT_FILE = "meals_365.json"
BATCH_SIZE = 10   # 每次生成10天


# ─── 季节提示 ──────────────────────────────────────────────
def season_hint(day_num: int) -> str:
    if 60 <= day_num <= 151:
        return "春季：荠菜、豌豆苗、莴苣、春笋（煮熟）、嫩豆腐"
    elif 152 <= day_num <= 243:
        return "夏季：冬瓜、丝瓜、苦瓜、绿豆、薏仁、黄瓜（炒熟）"
    elif 244 <= day_num <= 334:
        return "秋季：银耳、雪梨、百合、莲藕、山药、芋头"
    else:
        return "冬季：山药、白萝卜、南瓜、莲藕、黑木耳（煮软）"


# ─── 生成一批菜谱 ──────────────────────────────────────────
def generate_batch(start_day: int, used_names: list[str]) -> list[dict] | None:
    end_day = min(start_day + BATCH_SIZE - 1, 365)
    count = end_day - start_day + 1
    season = season_hint(start_day)

    used_str = "、".join(used_names[-120:]) if used_names else "无"

    prompt = f"""你是康复饮食营养师，请为第 {start_day} 到第 {end_day} 天（共{count}天）生成每日三餐菜谱。

【核心要求】
- 荤素搭配，清淡为主，高蛋白（鱼/虾/蛋/豆腐优先）
- 粪便柔软：高纤维+高水分蔬菜，润肠食材（木耳菜/山药/银耳/莲藕）
- 绝对禁忌：辣椒、花椒、胡椒、大量生葱蒜、油炸、腌制、酒精、浓茶
- 烹饪方式：清蒸/炖煮/少油炒，用油≤5ml每餐
- 季节参考（{season}）

【已用主菜名（绝对不能重复）】
{used_str}

【输出要求】
严格返回 JSON 数组，{count}个对象：
[
  {{
    "day": {start_day},
    "breakfast": {{"name": "菜名+主食", "protein": "蛋白来源", "veg": "蔬菜", "cook": "烹饪要点", "tip": "营养提示"}},
    "lunch":     {{"name": "菜名+主食", "protein": "蛋白来源", "veg": "蔬菜", "cook": "烹饪要点", "tip": "营养提示"}},
    "dinner":    {{"name": "菜名+主食", "protein": "蛋白来源", "veg": "蔬菜", "cook": "烹饪要点", "tip": "营养提示"}},
    "dish_names": ["主菜1", "主菜2", "..."]
  }}
]"""

    try:
        # 使用 Gemini 模型，配置为强制输出 JSON 格式
        model = genai.GenerativeModel(
            'gemini-1.5-flash', # 推荐使用 1.5 Pro 获取最佳的遵循指令能力和逻辑推理
            generation_config={"response_mime_type": "application/json"}
        )
        
        response = model.generate_content(prompt)
        raw = response.text.strip()
        
        batch = json.loads(raw)
        return batch

    except Exception as e:
        print(f"  ❌ 批次失败（第{start_day}-{end_day}天）：{e}")
        return None


# ─── 主流程 ────────────────────────────────────────────────
def main():
    if not GEMINI_API_KEY:
        print("❌ 请设置 GEMINI_API_KEY 环境变量")
        return
        
    # 初始化 Gemini 配置
    genai.configure(api_key=GEMINI_API_KEY)

    all_meals: list[dict] = []
    used_names: list[str] = []

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            all_meals = json.load(f)
        for m in all_meals:
            used_names.extend(m.get("dish_names", []))
        print(f"📂 检测到已有进度：{len(all_meals)} 天，从第 {len(all_meals)+1} 天继续")

    start = len(all_meals) + 1

    if start > 365:
        print("✅ 365天菜谱已全部生成！")
        return

    total_batches = (365 - start) // BATCH_SIZE + 1
    batch_count = 0

    for day in range(start, min(start + 50, 366), BATCH_SIZE):
        batch_count += 1
        end = min(day + BATCH_SIZE - 1, 365)
        print(f"🔄 生成第 {day}-{end} 天（批次 {batch_count}/{total_batches}）...")

        batch = generate_batch(day, used_names)
        if batch is None:
            print("  ⚠️  重试一次...")
            time.sleep(5)
            batch = generate_batch(day, used_names)

        if batch is None:
            print("  ❌ 跳过此批次，保存当前进度")
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_meals, f, ensure_ascii=False, indent=2)
            break # 遇到连续失败建议跳出循环，避免浪费 API 调用

        for item in batch:
            # 确保防御性编程，防止 API 返回的对象缺少 dish_names
            used_names.extend(item.get("dish_names", []))
            all_meals.append(item)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_meals, f, ensure_ascii=False, indent=2)

        print(f"  ✅ 已保存 {len(all_meals)}/365 天")
        print(f"  ☕ 等待中，保护免费额度...")
        time.sleep(6) # 避免触发 API 频率限制

    print(f"\n🎉 完成！共生成 {len(all_meals)} 天菜谱，保存至 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()