// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "RateLimiterExecutor.h"

#include <memory>
#include <vector>

/** 构造平滑限流器供执行器测试使用。 */
std::shared_ptr<RateLimiter<int>> makeLimiter() {
    return RateLimiter<int>::smoothBuilder(Duration::ofMillis(100)).build();
}

/** 验证构造函数保存策略索引。 */
void testPolicyIndex() {
    auto limiter = makeLimiter();
    RateLimiterExecutor<int> first(limiter, 0);
    RateLimiterExecutor<int> second(limiter, 3);
    SITP_ASSERT_EQ(0, first.getPolicyIndex());
    SITP_ASSERT_EQ(3, second.getPolicyIndex());
}

/** 验证第一个许可可立即获取而第二个受到限制。 */
void testSmoothPermitLimit() {
    auto limiter = makeLimiter();
    RateLimiterExecutor<int> executor(limiter, 0);
    SITP_ASSERT_TRUE(limiter->tryAcquirePermits(1));
    SITP_ASSERT_FALSE(limiter->tryAcquirePermits(1));
}

/** 验证许可耗尽时预执行返回失败。 */
void testPreExecuteFailureWhenLimited() {
    auto limiter = makeLimiter();
    RateLimiterExecutor<int> executor(limiter, 0);
    SITP_ASSERT_TRUE(limiter->tryAcquirePermits(1));
    ExecutionResult<int> result = executor.preExecute();
    SITP_ASSERT_FALSE(result.isSuccess());
    SITP_ASSERT_TRUE(result.getException() != nullptr);
}

/** 组装并执行限流执行器功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"policy_index", testPolicyIndex},
        {"smooth_permit_limit", testSmoothPermitLimit},
        {"pre_execute_failure", testPreExecuteFailureWhenLimited},
    };
    return sitp_test::runAll(tests);
}
