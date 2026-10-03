// SITP_TEST_COUNT: 1

#include "cpp_test_harness.h"
#include "Issue260Test.h"

#include <vector>

/** 验证单线程调度器下的 Issue 260 回归场景。 */
void testSingleThreadSchedulerScenario() {
    Issue260Test fixture;
    fixture.test();
}

/** 组装并执行 Issue 260 回归测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"single_thread_scheduler", testSingleThreadSchedulerScenario},
    };
    return sitp_test::runAll(tests);
}
