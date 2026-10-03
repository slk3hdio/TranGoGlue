// SITP_TEST_COUNT: 1

#include "cpp_test_harness.h"
#include "AdviceListenerTestCase.h"

/** 调用上游自包含测试，验证 before、return 与 throws 三条监听路径。 */
void testAdviceCallbacks() {
    AdviceListenerTestCase testCase;
    testCase.test$$AdviceListener$$onBefore$onReturn$onThrows();
}

/** 组装并执行 AdviceListenerTestCase 功能测试。 */
int main() {
    return sitp_test::runAll({
        {"advice_before_return_throws", testAdviceCallbacks},
    });
}
