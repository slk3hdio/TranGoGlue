// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "SyncExecutionImpl.h"

#include <list>
#include <memory>
#include <stdexcept>

/** 为同步执行附加测试提供最小可用的 FailsafeExecutor 实现。 */
class TestFailsafeExecutor : public FailsafeExecutor<int> {
public:
    /** 创建不附加策略的测试执行器。 */
    TestFailsafeExecutor() : FailsafeExecutor<int>(std::list<Policy<int>*>{}) {}

    /** 同步调用供应器并返回结果。 */
    int get(std::function<int()> supplier) override { return supplier(); }

    /** 同步调用任务。 */
    void run(std::function<void()> runnable) override { runnable(); }
};

/** 验证同时记录结果与异常时保留两部分状态。 */
void testCombinedRecord() {
    SyncExecutionImpl<int> execution(std::list<Policy<int>*>{});
    execution.record(7, std::make_exception_ptr(std::invalid_argument("boom")));

    ExecutionResult<int> result = execution.getResult();
    SITP_ASSERT_EQ(7, result.getResult());
    SITP_ASSERT_TRUE(result.getException() != nullptr);
    SITP_ASSERT_TRUE(execution.isComplete());
}

/** 验证非独立同步执行返回供应器结果。 */
void testExecuteSyncReturnsResult() {
    TestFailsafeExecutor executor;
    SyncExecutionImpl<int> execution(
        &executor,
        nullptr,
        nullptr,
        [](SyncExecutionInternal<int>*) { return ExecutionResult<int>::successResult(31); }
    );

    SITP_ASSERT_EQ(31, execution.executeSync());
}

/** 验证非独立执行复制得到新对象。 */
void testExecutorBackedCopy() {
    TestFailsafeExecutor executor;
    SyncExecutionImpl<int> execution(
        &executor,
        nullptr,
        nullptr,
        [](SyncExecutionInternal<int>*) { return ExecutionResult<int>::successResult(32); }
    );

    std::unique_ptr<SyncExecutionImpl<int>> copy(execution.copy());
    SITP_ASSERT_TRUE(copy.get() != &execution);
}

/** 验证同步执行把失败结果转换为 FailsafeException。 */
void testExecuteSyncRethrowsFailure() {
    TestFailsafeExecutor executor;
    SyncExecutionImpl<int> execution(
        &executor,
        nullptr,
        nullptr,
        [](SyncExecutionInternal<int>*) {
            return ExecutionResult<int>::exceptionResult(
                std::make_exception_ptr(std::runtime_error("boom"))
            );
        }
    );

    SITP_ASSERT_THROWS(execution.executeSync(), FailsafeException);
}

/** 组装并执行同步执行上下文附加测试。 */
int main() {
    return sitp_test::runAll({
        {"combined_record", testCombinedRecord},
        {"execute_sync_result", testExecuteSyncReturnsResult},
        {"executor_backed_copy", testExecutorBackedCopy},
        {"execute_sync_failure", testExecuteSyncRethrowsFailure},
    });
}
