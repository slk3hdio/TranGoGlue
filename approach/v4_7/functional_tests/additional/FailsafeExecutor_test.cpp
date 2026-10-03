// SITP_TEST_COUNT: 6

#include "cpp_test_harness.h"
#include "FailsafeExecutor.h"

#include <memory>
#include <vector>

/** 创建不附加策略的执行器。 */
FailsafeExecutor<int> makeAdditionalExecutor() {
    return FailsafeExecutor<int>(std::vector<std::shared_ptr<Policy<int>>>{});
}

/** 验证上下文供应器能够读取首次尝试状态并返回结果。 */
void testContextualGet() {
    FailsafeExecutor<int> executor = makeAdditionalExecutor();
    ContextualSupplier<int, int> supplier([](ExecutionContext<int>* context) {
        SITP_ASSERT_TRUE(context->isFirstAttempt());
        return 11;
    });
    SITP_ASSERT_EQ(11, executor.get(supplier));
}

/** 验证上下文调用对象可以执行并返回结果。 */
void testReusableCall() {
    FailsafeExecutor<int> executor = makeAdditionalExecutor();
    ContextualSupplier<int, int> supplier([](ExecutionContext<int>*) { return 12; });
    auto call = executor.newCall(supplier);
    SITP_ASSERT_EQ(12, call.execute());
}

/** 验证异步供应器返回预期结果。 */
void testAsyncGet() {
    FailsafeExecutor<int> executor = makeAdditionalExecutor();
    CheckedSupplier<int> supplier([]() { return 21; });
    SITP_ASSERT_EQ(21, executor.getAsync(supplier).get());
}

/** 验证异步任务确实执行副作用。 */
void testAsyncRun() {
    FailsafeExecutor<int> executor = makeAdditionalExecutor();
    int count = 0;
    CheckedRunnable runnable([&count]() { ++count; });
    executor.runAsync(runnable).get();
    SITP_ASSERT_EQ(1, count);
}

/** 验证完成与失败监听器可注册并接收执行事件。 */
void testCompletionListeners() {
    FailsafeExecutor<int> executor = makeAdditionalExecutor();
    int completeCount = 0;
    int failureCount = 0;
    auto complete = EventListener<ExecutionCompletedEvent<int>>::from(
        [&completeCount](std::shared_ptr<ExecutionCompletedEvent<int>>) { ++completeCount; }
    );
    auto failure = EventListener<ExecutionCompletedEvent<int>>::from(
        [&failureCount](std::shared_ptr<ExecutionCompletedEvent<int>>) { ++failureCount; }
    );
    executor.onComplete(complete).onFailure(failure);

    CheckedSupplier<int> supplier([]() -> int { throw std::runtime_error("boom"); });
    SITP_ASSERT_THROWS(executor.get(supplier), std::runtime_error);
    SITP_ASSERT_EQ(1, completeCount);
    SITP_ASSERT_EQ(1, failureCount);
}

/** 验证显式调度器配置保留链式执行器。 */
void testSchedulerConfiguration() {
    FailsafeExecutor<int> executor = makeAdditionalExecutor();
    auto configured = executor.with(Scheduler::DEFAULT());
    SITP_ASSERT_TRUE(configured.getPolicies().empty());
}

/** 组装并执行 Failsafe 执行器附加测试。 */
int main() {
    return sitp_test::runAll({
        {"contextual_get", testContextualGet},
        {"reusable_call", testReusableCall},
        {"async_get", testAsyncGet},
        {"async_run", testAsyncRun},
        {"completion_listeners", testCompletionListeners},
        {"scheduler_configuration", testSchedulerConfiguration},
    });
}
