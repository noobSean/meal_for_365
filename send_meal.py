#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合痔康复饮食 · 次日三餐定时推送
推送方式：飞书 Webhook
推送时间：每晚 20:00，推送次日菜谱
数据来源：meals_365.json（本地预生成，无需 AI，完全离线运行）
"""

import os
import json
import datetime
import requests

FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
MEALS_FILE = "meals_365.json"


# ─── 读取菜谱 ─────────────────────────────────────────────
def load_meals() -> list[dict]:
    with open(MEALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_tomorrow_meal(meals: list[dict]) -> tuple[dict, datetime.date]:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    # 以明天是一年中的第几天来循环索引（支持超过365天继续循环）
    day_of_year = tomorrow.timetuple().tm_yday  # 1-366
    index = (day_of_year - 1) % len(meals)
    return meals[index], tomorrow


# ─── 飞书消息 ─────────────────────────────────────────────
HEALTH_TIPS = [
    ("💧", "全天饮水不少于 2000ml，温水为主，早起一杯温水激活肠道"),
    ("🚶", "饭后慢走 15 分钟，促进胃肠蠕动，避免久坐久站"),
    ("🥦", "蔬菜总量不低于 500g，优先高水分品种（丝瓜/冬瓜/娃娃菜）"),
    ("⏰", "培养晨起排便习惯，如厕时间控制在 5 分钟内，切勿久蹲"),
    ("🛁", "便后温水坐浴 10 分钟，水温 38-40°C，促进局部血液循环"),
    ("🌙", "23 点前入睡，充足睡眠促进伤口愈合与体力恢复"),
    ("🍎", "可加餐 1-2 次，推荐香蕉/苹果/火龙果等润肠水果"),
]

FORBIDDEN = "🚫 禁忌：辣椒·花椒·胡椒·生葱蒜·油炸·酒精·浓茶·咖啡"


def build_message(meal: dict, tomorrow: datetime.date) -> str:
    date_str = tomorrow.strftime("%Y年%m月%d日")
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekdays[tomorrow.weekday()]
    tip_icon, tip_text = HEALTH_TIPS[tomorrow.weekday() % len(HEALTH_TIPS)]

    def block(icon, label, m):
        return (
            f"{icon} {label}\n"
            f"【{m['name']}】\n"
            f"蛋白质：{m['protein']}\n"
            f"蔬菜主食：{m['veg']}\n"
            f"烹饪：{m['cook']}\n"
            f"提示：{m['tip']}"
        )

    return f"""🍽 混合痔康复饮食 · 明日菜谱
📅 {date_str} {weekday}

{block("🌅", "早　餐", meal["breakfast"])}

{block("☀️", "午　餐", meal["lunch"])}

{block("🌙", "晚　餐", meal["dinner"])}

━━━━━━━━━━━━
{tip_icon} 今日健康提示：{tip_text}
{FORBIDDEN}
🥘 烹饪原则：清蒸 / 炖煮 / 少油炒（每餐用油 ≤5ml）"""


# ─── 发送飞书 ─────────────────────────────────────────────
def send_feishu(text: str) -> bool:
    try:
        resp = requests.post(
            FEISHU_WEBHOOK,
            json={"msg_type": "text", "content": {"text": text}},
            timeout=10,
        )
        result = resp.json()
        if result.get("code") == 0 or result.get("StatusCode") == 0:
            print("✅ 飞书消息发送成功")
            return True
        print(f"❌ 飞书返回错误：{result}")
        return False
    except Exception as e:
        print(f"❌ 发送异常：{e}")
        return False


# ─── 主入口 ───────────────────────────────────────────────
def main():
    if not FEISHU_WEBHOOK:
        print("❌ 未配置 FEISHU_WEBHOOK")
        return

    meals = load_meals()
    meal, tomorrow = get_tomorrow_meal(meals)

    print(f"📅 推送 {tomorrow} 的菜谱（第 {meal['day']} 天套餐）")
    text = build_message(meal, tomorrow)
    print("📤 预览：\n" + text)
    print("━" * 40)

    send_feishu(text)


if __name__ == "__main__":
    main()
