# 翻译产物功能测试

本目录用于验证 Java-to-C++ 翻译产物的运行时语义，而不仅是语法、编译和链接能力。

## 评估原则

仓库中的 28 个 Java 项目均已有 smoke tests，目前共 121 个测试方法、至少 336 条显式断言，并已在 Java 侧全部通过。C++ 功能测试应从这些测试移植，保持输入、预期输出、异常条件和边界条件一致。

统计时同时报告以下指标：

- 测试驱动构建成功率：能够与翻译产物共同编译、链接的项目比例。
- 严格测试通过率：$N_{passed}/N_{planned}$。测试驱动构建失败、崩溃和超时均计为失败，避免只统计可运行项目造成幸存者偏差。
- 条件测试通过率：$N_{passed}/N_{executed}$，用于观察已经执行的用例质量。
- 项目完全通过率：全部计划用例均通过的项目数除以项目总数。

## API 适配

不同模型可能为同一 Java API 选择不同但合理的 C++ 表示。例如 `Date` 可能翻译为 `std::time_t` 或 `std::tm*`，对象参数可能翻译为指针或引用。因此，公平的跨模型评估需要分成两层：

1. 固定的语义用例，定义与 Java 测试一致的输入和预期结果。
2. 每种产物 API 的薄适配层，只转换类型和调用形式，不改变断言和期望值。

若测试驱动因缺少适配层而无法构建，应标记为 `test_build_failed`，不能直接解释为翻译产物本身编译失败。论文正式统计前，应人工审查适配层，确保它没有修复或绕过翻译逻辑。

## 运行示例

```powershell
& $python approach\v4_7\scripts\evaluate_functional_tests.py `
  --project Cookie `
  --result-dir output\v4_7\Cookie\deepseek\runs\20260907_ablation_rep2_g0_bs5\result `
  --output output\v4_7\experiments\functional_tests\cookie.json
```

当前首批测试覆盖 `Cookie`、`OrGroupFilter` 和 `RateLimiterBuilder`。`Cookie_test.cpp` 等价覆盖原 Java smoke test 的 6 组行为，并直接适配使用 `std::time_t` 和指针参数的 Cookie API；其他 API 形态应增加薄适配层后再作跨模型比较。`RateLimiterBuilder` 的 Java null 参数用例在 C++ 中改为类型级检查，因为目标接口以非空引用表达相同约束。

baseline 的 API 适配测试放在 `adapters/<strategy>/<model>/` 下，不覆盖统一测试源。评估器可通过
`--test-source <path>` 显式选择适配源；适配源只能转换类型、命名空间和调用形式，不能补充翻译产物缺失的实现，也不能修改断言的语义。

## 附加测试

`additional/` 保存后续补充的测试，和原有功能测试独立统计。运行时显式指定
`--suite additional`；不传该参数时仍只执行原测试，因此 repair 闭环及既有实验口径不受影响。

repair 默认仍只执行原始 `base` 套件。若希望原测试通过后继续执行附加测试并把失败反馈
给 repair Agent，可向 `approach/main.py` 或批处理脚本传入
`--repair-test-suites base,additional`。
