// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "CircuitBreakerExecutor.h"

#include <vector>

/** 验证构造函数保存策略索引。 */
void testPolicyIndex() {
    CircuitBreakerImpl<int> breaker;
    CircuitBreakerExecutor<int> first(breaker, 0);
    CircuitBreakerExecutor<int> second(breaker, 3);
    SITP_ASSERT_EQ(0, first.getPolicyIndex());
    SITP_ASSERT_EQ(3, second.getPolicyIndex());
}

/** 验证成功回调会记录一次成功执行。 */
void testSuccessIsRecorded() {
    CircuitBreakerImpl<int> breaker;
    CircuitBreakerExecutor<int> executor(breaker, 0);
    executor.onSuccess(ExecutionResult<int>::success(7));
    SITP_ASSERT_EQ(1, breaker.getSuccessCount());
    SITP_ASSERT_EQ(1, breaker.getExecutionCount());
}

/** 验证关闭状态的断路器允许预执行。 */
void testPreExecuteWhenClosed() {
    CircuitBreakerImpl<int> breaker;
    CircuitBreakerExecutor<int> executor(breaker, 0);
    ExecutionResult<int> result = executor.preExecute();
    SITP_ASSERT_TRUE(result.isNonResult());
    SITP_ASSERT_TRUE(breaker.isClosed());
}

/** 组装并执行断路器执行器功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"policy_index", testPolicyIndex},
        {"success_is_recorded", testSuccessIsRecorded},
        {"pre_execute_closed", testPreExecuteWhenClosed},
    };
    return sitp_test::runAll(tests);
}
