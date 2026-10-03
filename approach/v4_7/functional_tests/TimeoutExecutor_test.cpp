// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "TimeoutExecutor.h"

#include <exception>
#include <memory>
#include <stdexcept>
#include <vector>

/** 创建一分钟超时策略。 */
std::shared_ptr<TimeoutImpl<int>> makeTimeout() {
    auto duration = std::make_shared<Duration>(std::chrono::minutes(1));
    return std::make_shared<TimeoutImpl<int>>(TimeoutConfig<int>(duration, false));
}

/** 验证构造函数保存策略索引。 */
void testPolicyIndex() {
    auto timeout = makeTimeout();
    TimeoutExecutor<int> first(timeout, 0);
    TimeoutExecutor<int> second(timeout, 2);
    SITP_ASSERT_EQ(0, first.getPolicyIndex());
    SITP_ASSERT_EQ(2, second.getPolicyIndex());
}

/** 验证成功结果不属于超时失败。 */
void testSuccessIsNotFailure() {
    auto timeout = makeTimeout();
    TimeoutExecutor<int> executor(timeout, 0);
    SITP_ASSERT_FALSE(executor.isFailure(ExecutionResult<int>::success(7)));
    SITP_ASSERT_FALSE(executor.isFailure(ExecutionResult<int>(7, std::exception_ptr{})));
}

/** 验证普通异常和 non-result 不被误判成超时。 */
void testOtherResultsAreNotTimeouts() {
    auto timeout = makeTimeout();
    TimeoutExecutor<int> executor(timeout, 0);
    SITP_ASSERT_FALSE(executor.isFailure(ExecutionResult<int>::none()));
    SITP_ASSERT_FALSE(executor.isFailure(
        ExecutionResult<int>::exception(std::make_exception_ptr(std::runtime_error("boom")))
    ));
}

/** 组装并执行超时执行器功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"policy_index", testPolicyIndex},
        {"success_not_failure", testSuccessIsNotFailure},
        {"other_results_not_timeouts", testOtherResultsAreNotTimeouts},
    };
    return sitp_test::runAll(tests);
}
