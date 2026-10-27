# 参考解说明

参考程序枚举公开规模内所有整数体积向量，并按题面规则做独立校验。

- C1-log-ratio：先分别累加酸量 A 与碱量 B，再检查 A、B 为正且有限，按 `6.35 + log10(B/A)` 计算；对应 `test_log_ratio_direction`、`test_nonfinite_reject_sentinel`。
- C2-integer-feasibility：逐个检查体积守恒、库存上限、预算和 pH 容差；对应 `test_max_volume_boundary`、`test_budget_boundary`、`test_infeasible_reject_absent`。
- C3-deterministic-tie：候选键为 `(total_cost_cents, volume_vector)`，Python 元组比较直接实现输入顺序的词典序；对应 `test_cost_tie_lexicographic`、`test_deterministic_bytes`。
- C4-contract-safety：JSON 解析使用重复键拒绝钩子，所有校验在写文件前完成，最后只用同目录临时文件和原子替换；对应 `test_invalid_duplicate_key`、`test_extra_key_reject`、`test_boolean_numeric_reject`、`test_late_invalid_preserves_old`。

pH 输出使用十进制 `ROUND_HALF_UP` 保留两位；参考解不读取测试、评分或报告目录。
