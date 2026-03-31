# meal_for_365
=======
=======

# 🍽️ 康复饮食 · 365天静态菜谱推送

> 飞书 Webhook · 每晚 20:00 推送次日菜谱 · 完全本地运行 · 无需任何 AI API

## 工作原理

```
【一次性准备】
运行 generate_365.py
  → 调用 Claude API 生成全部365天菜谱
  → 保存为 meals_365.json（约 300KB）
  → 提交到 GitHub 仓库

【每日运行（完全离线）】
每晚 20:00 GitHub Actions 触发
  → send_meal.py 读取 meals_365.json
  → 根据明天是一年中第几天取对应菜谱
  → 发送飞书消息
  → 完成（无任何 API 调用）
```

**日常运行完全不需要 Anthropic API Key，只需要飞书 Webhook。**

---

## 部署步骤

### 第一步：生成365天菜谱（只做一次）

**需要：Anthropic API Key**（只在这一步用到）

```bash
# 在本地运行
pip install requests
export ANTHROPIC_API_KEY="sk-ant-xxx"
python generate_365.py
```

运行约需 **10-15 分钟**（36批，每批生成10天）。
支持**断点续传**：如果中途中断，重新运行会从断点继续，不重新生成已完成的部分。

运行完成后会生成 `meals_365.json` 文件（约 300KB）。

### 第二步：上传到 GitHub

仓库结构：
```
your-repo/
├── generate_365.py   ← 生成用，之后不再需要
├── send_meal.py      ← 每日推送主脚本
├── meals_365.json    ← 365天菜谱数据（主角）
└── .github/
    └── workflows/
        └── send_meal.yml
```

### 第三步：配置飞书机器人

群聊 → 设置 → 群机器人 → 添加机器人 → 自定义机器人 → 复制 Webhook URL

### 第四步：配置 GitHub Secrets

仓库 → Settings → Secrets and variables → Actions → New repository secret

| Secret 名 | 值 |
|-----------|-----|
| `FEISHU_WEBHOOK` | 飞书机器人完整 Webhook URL |

> 注意：日常运行不需要 ANTHROPIC_API_KEY，只有重新生成菜谱时才需要。

### 第五步：启用并测试

Actions → 启用 → 手动触发一次 → 查看飞书是否收到明日菜谱

---

## 超过365天怎么办？

`send_meal.py` 使用 `day_of_year % 365` 自动循环。
第366天会回到第1天的菜谱，以此类推，永远不会报错。

**如果你想刷新菜谱（一年后）：** 重新运行 `generate_365.py` 生成新的 `meals_365.json`，替换旧文件提交即可。

---

## 优势总结

| 特性 | 说明 |
|------|------|
| 无 API 依赖 | 日常运行零成本，不依赖网络服务 |
| 超稳定 | 菜谱不会因为 API 变化或额度不足而失败 |
| 快速 | 读本地文件，推送耗时 < 1 秒 |
| 可审查 | meals_365.json 可以直接打开检查所有菜谱 |

---


