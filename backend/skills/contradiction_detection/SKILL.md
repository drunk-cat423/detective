---
name: contradiction_detection
description: 检测便签、时间线、已知信息之间的矛盾点。
version: 1.0.0
tools_required:
  - search_notes
  - get_timeline
  - get_known_infos
---

# 矛盾检测技能

当用户要求检测矛盾或怀疑信息不一致时，请按以下步骤操作：

1. 调用 `get_timeline` 获取所有时间线事件，提取时间-事件对。
2. 调用 `get_known_infos` 获取已知信息。
3. 调用 `search_notes`（可选关键词如“矛盾”、“冲突”）获取相关便签。
4. 检查以下三类矛盾：
   - 时间冲突：同一时间某人出现在不同地点。
   - 陈述不一致：同一事实有不同的说法。
   - 逻辑矛盾：例如 A 说从未见过 B，但 C 说 A 和 B 曾一起出现。
5. 输出发现的矛盾点，若无矛盾则回复“未发现明显矛盾”。

输出格式：
【矛盾点1】
- 类型：时间冲突
- 描述：...