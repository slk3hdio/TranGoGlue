// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "TimeoutExecutor.h"

#include <chrono>
#include <memory>
#include <thread>

/** 创建指定时长的超时执行器。 */
TimeoutExecutor<int> makeAdditionalTimeoutExecutor(const std::chrono::milliseconds& timeout) {
    auto duration = std::make_shared<Duration>(timeout);
    auto policy = std::make_shared<TimeoutImpl<int>>(TimeoutConfig<int>(duration, true));
    return TimeoutExecutor<int>(policy, 0);
}

/** 验证同步快速任务在超时前返回结果。 */
void testSyncFastExecution() {
    auto executor = makeAdditionalTimeoutExecutor(std::chrono::seconds(1));
    auto wrapped = executor.apply(
        [](SyncExecutionInternal<int>*) { return ExecutionResult<int>::success(41); },
        nullptr
    );

    SITP_ASSERT_EQ(41, wrapped(nullptr).getResult());
}

/** 验证同步慢任务返回超时异常。 */
void testSyncSlowExecutionTimesOut() {
    auto executor = makeAdditionalTimeoutExecutor(std::chrono::milliseconds(20));
    auto wrapped = executor.apply(
        [](SyncExecutionInternal<int>*) {
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            return ExecutionResult<int>::success(42);
        },
        nullptr
    );

    ExecutionResult<int> result = wrapped(nullptr);
    SITP_ASSERT_TRUE(result.getException() != nullptr);
}

/** 验证异步快速任务在超时前返回结果。 */
void testAsyncFastExecution() {
    auto executor = makeAdditionalTimeoutExecutor(std::chrono::seconds(1));
    auto future = std::make_shared<FailsafeFuture<int>>();
    auto wrapped = executor.applyAsync(
        [](AsyncExecutionInternal<int>*) {
            CompletableFuture<ExecutionResult<int>> promise;
            promise.complete(ExecutionResult<int>::success(43));
            return promise;
        },
        Scheduler::DEFAULT.get(),
        future.get()
    );

    SITP_ASSERT_EQ(43, wrapped(nullptr).get().getResult());
}

/** 验证异步慢任务返回超时异常。 */
void testAsyncSlowExecutionTimesOut() {
    auto executor = makeAdditionalTimeoutExecutor(std::chrono::milliseconds(20));
    auto future = std::make_shared<FailsafeFuture<int>>();
    auto wrapped = executor.applyAsync(
        [](AsyncExecutionInternal<int>*) {
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            CompletableFuture<ExecutionResult<int>> promise;
            promise.complete(ExecutionResult<int>::success(44));
            return promise;
        },
        Scheduler::DEFAULT.get(),
        future.get()
    );

    SITP_ASSERT_TRUE(wrapped(nullptr).get().getException() != nullptr);
}

/** 组装并执行超时执行器附加测试。 */
int main() {
    return sitp_test::runAll({
        {"sync_fast_execution", testSyncFastExecution},
        {"sync_slow_timeout", testSyncSlowExecutionTimesOut},
        {"async_fast_execution", testAsyncFastExecution},
        {"async_slow_timeout", testAsyncSlowExecutionTimesOut},
    });
}
