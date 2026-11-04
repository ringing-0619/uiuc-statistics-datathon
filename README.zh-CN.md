# UIUC Statistics Datathon

[English](README.md) | 简体中文

基于 UIUC Statistics Datathon 团队项目改造的呼叫中心预测演示，使用独立生成的合成数据，支持本地复现。

**Python · pandas · NumPy · scikit-learn · openpyxl**

## 项目概览

- **预测任务**：预测日级与半小时级呼入量，同时估计通话处理时间（CCT）和放弃率，展示需求规划的分析流程。
- **日级建模**：按组训练梯度提升模型，使用日历特征，并结合历史残差校准和可配置的规划偏置。
- **日内分配**：通过按星期估计并归一化的时段分布，将日呼入量分配至每天 48 个半小时时段；CCT 和放弃率使用独立分布与历史水平启发式估计。
- **时间回测**：对两个历史月份分别重新训练日呼入量模型，各折仅使用验证月之前的数据。MAE、WAPE 保留在内存中，评估范围限于日级呼入量。

## 运行合成数据演示

已使用 Python 3.13 验证。在仓库根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py --demo
```

Windows 使用 `.venv\Scripts\activate` 激活环境。

演示会为四个虚构分组独立生成输入，并输出至 `outputs/demo/synthetic_forecast.csv`。无需比赛文件或凭据；依赖安装后可离线运行，不连接实验追踪服务或上传产物。添加 `--evaluate` 可执行回测，指标不会打印或保存。

## 验证

**18 项回归测试**覆盖数据生成可复现性、按时间划分训练与验证集、Excel 输入、输出校验及隐私保护。导出前检查日历覆盖完整性、指标有限且非负、放弃率范围及放弃通话数一致性。

```bash
python -B -m unittest discover -s tests -v
```

## 数据与使用边界

公开仓库不包含比赛原始记录、衍生业务统计、已训练产物或原始提交文件。合成数据结果用于验证软件行为，不代表比赛预测精度或实际业务收益；本仓库不宣称比赛分数或排名。

[运行指南（英文）](docs/user-guide.md) · [方法与局限（英文）](docs/methodology.md) · [数据政策与许可边界（英文）](docs/data_policy.md)
