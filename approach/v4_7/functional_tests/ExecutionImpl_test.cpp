// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "ExecutionImpl.h"

#include <exception>
#include <vector>

/** 创建不带策略的执行上下文。 */
ExecutionImpl<int> makeExecution() {
    return ExecutionImpl<int>(std::vector<failsafe::Policy<int>*>{});
}

/** 验证首次尝试的计数和状态。 */
void testRecordAttempt() {
    ExecutionImpl<int> execution = makeExecution();
    SITP_ASSERT_EQ(0, execution.getAttemptCount());
    execution.recordAttempt();
    SITP_ASSERT_EQ(1, execution.getAttemptCount());
    SITP_ASSERT_TRUE(execution.isFirstAttempt());
    SITP_ASSERT_FALSE(execution.isRetry());
}

/** 验证记录成功结果会更新结果和执行计数。 */
void testRecordResult() {
    ExecutionImpl<int> execution = makeExecution();
    execution.preExecute();
    execution.record(ExecutionResult<int>(7, std::exception_ptr{}));
    SITP_ASSERT_TRUE(execution.isPreExecuted());
    SITP_ASSERT_EQ(7, execution.getResult().getResult());
    SITP_ASSERT_EQ(7, execution.getLastResult());
    SITP_ASSERT_EQ(1, execution.getAttemptCount());
    SITP_ASSERT_EQ(1, execution.getExecutionCount());
}

/** 验证取消操作只在第一次调用时成功。 */
void testCancelIsIdempotent() {
    ExecutionImpl<int> execution = makeExecution();
    SITP_ASSERT_FALSE(execution.isCancelled());
    SITP_ASSERT_TRUE(execution.cancel());
    SITP_ASSERT_TRUE(execution.isCancelled());
    SITP_ASSERT_FALSE(execution.cancel());
}

/** 验证空执行的最近结果回退值和耗时边界。 */
void testDefaultsAndTiming() {
    ExecutionImpl<int> execution = makeExecution();
    SITP_ASSERT_EQ(99, execution.getLastResult(99));
    SITP_ASSERT_TRUE(execution.getLatest() == &execution);
    SITP_ASSERT_TRUE(execution.getElapsedTime().count() >= 0.0);
    SITP_ASSERT_TRUE(execution.toString().find("attempts=") != std::string::npos);
}

/** 组装并执行基础执行上下文功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"record_attempt", testRecordAttempt},
        {"record_result", testRecordResult},
        {"cancel_idempotent", testCancelIsIdempotent},
        {"defaults_and_timing", testDefaultsAndTiming},
    };
    return sitp_test::runAll(tests);
}
