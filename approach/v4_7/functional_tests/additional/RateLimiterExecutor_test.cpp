// SITP_TEST_COUNT: 2

#include "cpp_test_harness.h"
#include "RateLimiterExecutor.h"

#include <memory>

/** 创建零等待时间的平滑限流器。 */
std::shared_ptr<RateLimiter<int>> makeAdditionalLimiter() {
    return RateLimiter<int>::smoothBuilder(Duration::ofSeconds(1)).build();
}

/** 验证首个同步许可成功且紧邻请求被拒绝。 */
void testSyncPermitSequence() {
    auto limiter = makeAdditionalLimiter();
    RateLimiterExecutor<int> executor(limiter, 0);

    ExecutionResult<int> accepted = executor.preExecute();
    ExecutionResult<int> rejected = executor.preExecute();

    SITP_ASSERT_TRUE(accepted.isNonResult());
    SITP_ASSERT_TRUE(rejected.getException() != nullptr);
}

/** 验证异步预执行在无许可时返回限流异常。 */
void testAsyncPermitFailure() {
    auto limiter = makeAdditionalLimiter();
    SITP_ASSERT_TRUE(limiter->tryAcquirePermit());
    RateLimiterExecutor<int> executor(limiter, 0);
    auto future = std::make_shared<FailsafeFuture<int>>(nullptr);

    auto resultFuture = executor.preExecuteAsync(Scheduler::DEFAULT(), future);
    ExecutionResult<int> result = resultFuture->get();

    SITP_ASSERT_TRUE(result.getException() != nullptr);
}

/** 组装并执行限流执行器附加测试。 */
int main() {
    return sitp_test::runAll({
        {"sync_permit_sequence", testSyncPermitSequence},
        {"async_permit_failure", testAsyncPermitFailure},
    });
}
