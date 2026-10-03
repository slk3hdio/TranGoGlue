# CoreCov缺失模块的行为测试补充

本套件检查9个CoreCov缺失模块，保留原base与additional套件，不修改生产代码或翻译产物。新增用例先在Java原实现上验证，再通过独立C++测试源评估相同输入与断言。

## 用例与核心入口映射

| 模块 | 本轮新增Java用例 | 核心入口和验证行为 | C++对应套件 |
| --- | ---: | --- | --- |
| Base32Codec | 2 | encode/decode：空输入、小写解码 | functional_tests/corecov/Base32Codec_test.cpp |
| Hashids | 2 | encodeFromHex/decodeToHex：前缀与十六进制往返；encode/decode：零和大整数 | functional_tests/corecov/Hashids_test.cpp |
| HttpParser | 2 | readLine(InputStream)、parseHeaders(InputStream)：LF、末行、重复请求头顺序 | functional_tests/corecov/HttpParser_test.cpp |
| HttpURL | 2 | setUserinfo/getUser/getPassword/setPassword、setQuery：凭据更新与查询转义 | functional_tests/corecov/HttpURL_test.cpp |
| CsvWorkbook | 2 | createSheet(String)、getSheet、getSheetAt、活动页与可见页接口 | functional_tests/corecov/CsvWorkbook_test.cpp |
| Head | 2 | 构造、名称列表、字段名和强制标志；空字符串合法 | functional_tests/corecov/Head_test.cpp |
| Draft_6455 | 2 | getCloseHandshakeType、reset、copyInstance、getMaxFrameSize：双向关闭与配置保留 | functional_tests/corecov/Draft_6455_test.cpp |
| UndeclaredThrowableStrategy | 1 | transform：合法异常包装类下返回独立TransformingClassGenerator | 本轮仅Java；尚未为不同C++ ASM类型表示编写薄适配 |
| RateLimiterExecutor | 0（复用3个） | preExecute、preExecuteAsync：同步拒绝、异步拒绝与取消回调 | 复用functional_tests/additional/RateLimiterExecutor_test.cpp（2个） |

新增15个Java参考用例、14个对应C++用例；另复用已有3个Java/2个C++限流用例。UndeclaredThrowableStrategy通过子类合法暴露protected入口，不使用反射改写状态，不吞异常。

## 验证与数据隔离

在仓库根目录运行 `& $python paper_data/run_corecov_supplement.py`。日志、JUnit 结果及各模型独立 C++ 报告保存在脚本配置的实验输出目录中。

- Java参考侧启用断言，编译或JUnit失败时不执行对应C++用例。
- C++只做类型/调用形式适配；Head布尔getter的get/is命名等价适配不补实现。
- 编译失败、链接失败和执行断言失败均保留原始日志，不能互相混称。
- 不将新套件混入历史base分母，不重跑LLM，也不恢复用户终止的repair。
- 这些是行为覆盖映射，不是动态方法覆盖率。仍需完成核心方法全集和执行追踪才能计算CoreCov；不得凭存在测试就填100。
- 本轮未覆盖HttpURL全部构造/转义重载、CsvWorkbook全部Workbook接口、Draft_6455帧编解码及UndeclaredThrowableStrategy真实异常字节码变换。未覆盖不表示不能编写，应保留待办，不将表中的“—”解释为无法测试。

## 已发现的语义问题

Head原base测试把Java的null名称用C++空字符串表示，但原Java接受空字符串；二者不等价。本轮新增“空字符串合法”断言，原base暂不改写，历史结果需单独审计，不能因原用例通过而认定此边界正确。

## 本轮执行结果

- 9模块Java参考侧：15个新增与3个复用用例，共18个全部通过。
- 8模块×3模型的C++独立评估：24份报告、48个计划用例，严格通过14个。
- 6个组合全通过；3个组合可构建但执行失败；15个组合测试驱动无法编译或链接。
- Head/GPT、Head/Qwen各通过1/2，新“空字符串合法”用例均被产物错误拒绝；Head/DeepSeek缺失getter实现导致链接失败。
- Base32Codec/Qwen未完成新增用例执行，状态保留为test_failed，不能作为小写解码或空输入的有效通过证据。
- 原master_runs.csv、论文TS和CoreCov数值未更改。本轮结果必须以新套件单独解释，尚不能宣称9模块全方法覆盖已补齐。

## 2026-09-29独立补跑与动态覆盖

执行 `paper_data/run_corecov_supplement.py --force --output-dir output/v4_7/experiments/corecov_supplement_rerun_20260929` 已完成。9模块Java补充测试全部通过；C++24组合、48计划用例仍为14通过，6组合全通过、3组合运行失败、15组合构建失败。原报告保留，未请求LLM或重启被终止的repair。

另执行 `paper_data/measure_corecov_supplement.py`，使用JaCoCo 0.8.14，在原Java实现上运行base、additional及本次补充套件，不采用吞异常的extra_tests。逐方法记录在上述目录的 `coverage_summary.json`，完整JUnit日志和XML在 `coverage/<模块>/`。

| 模块 | 方法命中/总数 | 动态方法覆盖 | 构造器命中/总数 |
| --- | ---: | ---: | ---: |
| Base32Codec | 6/6 | 100% | 3/3 |
| Hashids | 28/29 | 96.55% | 1/1 |
| HttpParser | 5/5 | 100% | 0/0 |
| HttpURL | 13/26 | 50% | 3/19 |
| CsvWorkbook | 8/61 | 13.11% | 1/1 |
| Head | 0/0 | 不适用 | 1/1 |
| Draft_6455 | 6/48 | 12.50% | 4/7 |
| RateLimiterExecutor | 4/4 | 100% | 1/1 |
| UndeclaredThrowableStrategy | 1/2 | 50% | 2/2 |

统计范围为模块同名核心类及内部类的JaCoCo可执行方法，构造器与静态初始化器不进入方法分母，Lombok等生成代码遵循JaCoCo过滤。Head只剩显式构造器，因此方法覆盖不能记为0%或100%。方法命中仅证明入口执行，不能证明全部分支或语义正确。

该动态口径尚未与论文原先“具名核心方法集合”逐项对齐；论文生成器目前对旧模块硬编码100。为避免将两种分母混用，本次不直接覆盖论文CoreCov或历史TS。后续需统一35模块的方法全集与统计口径，再生成论文列；本表及逐方法XML是已完成补跑的原始证据。
