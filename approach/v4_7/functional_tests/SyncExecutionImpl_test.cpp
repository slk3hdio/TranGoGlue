// SITP_TEST_COUNT: 5

#include "cpp_test_harness.h"
#include "SyncExecutionImpl.h"

#include <exception>
#include <list>
#include <vector>

/** 创建不带策略的同步执行上下文。 */
SyncExecutionImpl<int> makeSyncExecution() {
    return SyncExecutionImpl<int>(std::list<Policy<int>*>{});
}

/** 验证同步执行上下文的初始状态。 */
void testInitialState() {
    SyncExecutionImpl<int> execution = makeSyncExecution();
    SITP_ASSERT_TRUE(execution.isPreExecuted());
    SITP_ASSERT_FALSE(execution.isComplete());
    SITP_ASSERT_FALSE(execution.isInterrupted());
    SITP_ASSERT_FALSE(execution.isCancelled());
    SITP_ASSERT_TRUE(execution.getDelay().isZero());
}

/** 验证记录结果会完成执行并更新计数。 */
void testRecordResult() {
    SyncExecutionImpl<int> execution = makeSyncExecution();
    execution.recordResult(7);
    SITP_ASSERT_EQ(7, execution.getResult().getResult());
    SITP_ASSERT_EQ(7, execution.getLastResult());
    SITP_ASSERT_TRUE(execution.isComplete());
    SITP_ASSERT_EQ(1, execution.getAttemptCount());
    SITP_ASSERT_EQ(1, execution.getExecutionCount());
}

/** 验证显式完成会写入 non-result 完成态。 */
void testComplete() {
    SyncExecutionImpl<int> execution = makeSyncExecution();
    execution.complete();
    SITP_ASSERT_TRUE(execution.isComplete());
    SITP_ASSERT_TRUE(execution.getResult().isNonResult());
}

/** 验证仅可中断状态会记录中断。 */
void testInterrupt() {
    SyncExecutionImpl<int> execution = makeSyncExecution();
    execution.setInterruptable(true);
    execution.interrupt();
    SITP_ASSERT_TRUE(execution.isInterrupted());

    SyncExecutionImpl<int> blocked = makeSyncExecution();
    blocked.setInterruptable(false);
    blocked.interrupt();
    SITP_ASSERT_FALSE(blocked.isInterrupted());
}

/** 验证独立执行复制返回自身且取消幂等。 */
void testCopyAndCancel() {
    SyncExecutionImpl<int> execution = makeSyncExecution();
    SITP_ASSERT_TRUE(execution.copy() == &execution);
    SITP_ASSERT_TRUE(execution.cancel());
    SITP_ASSERT_TRUE(execution.isCancelled());
    SITP_ASSERT_FALSE(execution.cancel());
}

/** 组装并执行同步执行上下文功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"initial_state", testInitialState},
        {"record_result", testRecordResult},
        {"complete", testComplete},
        {"interrupt", testInterrupt},
        {"copy_and_cancel", testCopyAndCancel},
    };
    return sitp_test::runAll(tests);
}
