// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "DebugLogExceptionModule.h"

#include <type_traits>

/** 验证模块可以正常构造。 */
void testConstruction() {
    DebugLogExceptionModule module;
    SITP_ASSERT_TRUE(&module != nullptr);
}

/** 验证完成加载入口可以被调用而不抛出异常。 */
void testLoadCompleted() {
    DebugLogExceptionModule module;
    module.loadCompleted();
}

/** 验证翻译结果保留 Module 与 LoadCompleted 类型契约。 */
void testTypeContract() {
    SITP_ASSERT_TRUE((std::is_base_of<Module, DebugLogExceptionModule>::value));
    SITP_ASSERT_TRUE((std::is_base_of<LoadCompleted, DebugLogExceptionModule>::value));
}

/** 组装并执行 DebugLogExceptionModule 功能测试。 */
int main() {
    return sitp_test::runAll({
        {"construction", testConstruction},
        {"load_completed", testLoadCompleted},
        {"type_contract", testTypeContract},
    });
}
