// SITP_TEST_COUNT: 1

#include "cpp_test_harness.h"
#include "Issue231Test.h"

#include <vector>

/** 验证超时处理会等待底层执行完成。 */
void testWaitsForExecutionCompletion() {
    Issue231Test fixture;
    fixture.shouldWaitForExecutionCompletion();
}

/** 组装并执行 Issue 231 回归测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"waits_for_execution_completion", testWaitsForExecutionCompletion},
    };
    return sitp_test::runAll(tests);
}
