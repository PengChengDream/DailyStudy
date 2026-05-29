# 主持人打开一扇空门后，为什么换门不是 50 对 50？

日期：2026-05-29

答案版：[2026-05-29-answers.md](https://github.com/PengChengDream/DailyStudy/blob/main/history/2026-05-29-answers.md)


## 1. 智商题：三门问题

- 题目：三扇门后有一辆车和两只羊。你先选一扇门，主持人知道答案并打开另一扇有羊的门。此时换门是否更优？
- 考察点：条件概率、信息泄露、策略分析

## 2. 经典 ML/DL：类别极不均衡时为什么 AUC 可能比 Accuracy 更有用？

- 题目：在正负样本极不均衡的二分类任务里，Accuracy、Precision/Recall、AUC 分别容易踩什么坑？
- 考察点：分类评估、排序指标、数据不均衡

## 3. 热门技术：Agent 的 memory 应该存什么，不应该存什么？

- 题目：设计一个面向工作流的 Agent，长期记忆、短期上下文和外部知识库分别应该承担什么职责？
- 考察点：Agent、Memory、隐私

## 4. 热门技术：多模态模型为什么需要视觉 token 和文本 token 对齐？

- 题目：视觉编码器接到 LLM 前，常见的 projector、Q-Former 或 cross-attention 分别在解决什么问题？
- 考察点：多模态、表示对齐、视觉语言模型

## 5. 近 7 天新技术：刚刚，全球首个“事件级预测”具身智能世界模型来了！

- 题目：量子位 2026-05-29 报道了 WALL-WM 这类“事件级预测”具身智能世界模型。面试中如果让你解释它，为什么“按事件建模”可能比“按固定帧预测”更适合机器人？
- 考察点：具身智能、世界模型、事件级建模、多模态动作生成

## 6. 编程题（ML）：实现多分类交叉熵损失

- 链接：[Deep-ML 134: Multi-Class Cross-Entropy Loss](https://www.deep-ml.com/problems/134)
- 面试场景：深度学习基础面试中常见，用来考察数值稳定性和向量化。
- 函数签名：`softmax_cross_entropy(logits, labels)`
- 题目：给定 logits，形状为 (n, c)，以及每个样本的类别下标 labels，返回平均交叉熵损失和 logits 梯度。
- 样例：
  - `logits=[[2,1,0]], labels=[0] -> loss≈0.4076, grad≈[[-0.3348,0.2447,0.0900]]`
- 约束：使用 NumPy；需要减去每行最大值保证稳定；参考解法 30 行以内。
