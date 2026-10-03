// SITP_TEST_COUNT: 2

#include "cpp_test_harness.h"
#include "CircuitBreakerExecutor.h"

#include <memory>
#include <stdexcept>

/** 验证关闭状态在预执行阶段允许继续执行。 */
void testPreExecuteWhenClosed() {
    CircuitBreakerImpl<int> breaker;
    CircuitBreakerExecutor<int> executor(breaker, 0);

    ExecutionResult<int> result = executor.preExecute();

    SITP_ASSERT_TRUE(result.isNonResult());
}

/** 验证失败结果被原样返回且计入执行次数。 */
void testFailureIsRecordedAndReturned() {
    CircuitBreakerImpl<int> breaker;
    CircuitBreakerExecutor<int> executor(breaker, 0);
    ExecutionResult<int> failure = ExecutionResult<int>::exception(
        std::make_shared<std::runtime_error>("boom")
    );

    ExecutionResult<int> returned = executor.onFailure(nullptr, failure);

    SITP_ASSERT_TRUE(returned.getException() != nullptr);
    SITP_ASSERT_EQ(1, breaker.getExecutionCount());
}

/** 组装并执行断路器执行器附加测试。 */
int main() {
    return sitp_test::runAll({
        {"pre_execute_closed", testPreExecuteWhenClosed},
        {"failure_recorded_and_returned", testFailureIsRecordedAndReturned},
    });
}
