// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "RateLimiterBuilder.h"

#include <cstddef>
#include <chrono>
#include <type_traits>
#include <vector>

using RateLimitDuration = std::chrono::nanoseconds;

/** 验证突发限流器每周期只允许指定数量的即时请求。 */
void testBurstyPermitLimit() {
    auto limiter = RateLimiterBuilder<int>(2, RateLimitDuration{3600000000000LL}).build();
    SITP_ASSERT_TRUE(limiter->isBursty());
    SITP_ASSERT_FALSE(limiter->isSmooth());
    SITP_ASSERT_TRUE(limiter->tryAcquirePermit());
    SITP_ASSERT_TRUE(limiter->tryAcquirePermit());
    SITP_ASSERT_FALSE(limiter->tryAcquirePermit());
}

/** 验证平滑限流器拒绝紧随首个许可之后的第二次请求。 */
void testSmoothRateLimit() {
    auto limiter = RateLimiterBuilder<int>(RateLimitDuration{60000000000LL}).build();
    SITP_ASSERT_TRUE(limiter->isSmooth());
    SITP_ASSERT_FALSE(limiter->isBursty());
    SITP_ASSERT_TRUE(limiter->tryAcquirePermit());
    SITP_ASSERT_FALSE(limiter->tryAcquirePermit());
}

/** 验证最大等待时间的默认值、链式返回值和更新结果。 */
void testMaxWaitTime() {
    RateLimiterBuilder<int> builder(RateLimitDuration{1000000000LL});
    SITP_ASSERT_EQ(0LL, builder.build()->getConfig().getMaxWaitTime().count());

    auto& returned = builder.withMaxWaitTime(RateLimitDuration{5000000000LL});
    SITP_ASSERT_TRUE(&returned == &builder);
    SITP_ASSERT_EQ(
        RateLimitDuration{5000000000LL}.count(),
        builder.build()->getConfig().getMaxWaitTime().count()
    );
}

/** 验证 C++ 接口在类型层面禁止传入 Java null 对应值。 */
void testNullWaitTimeRejectedByType() {
    using Method = RateLimiterBuilder<int>& (RateLimiterBuilder<int>::*)(RateLimitDuration);
    constexpr bool acceptsNull = std::is_invocable_v<Method, RateLimiterBuilder<int>&, std::nullptr_t>;
    SITP_ASSERT_FALSE(acceptsNull);
}

/** 组装并运行 RateLimiterBuilder 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"bursty_permit_limit", testBurstyPermitLimit},
        {"smooth_rate_limit", testSmoothRateLimit},
        {"max_wait_time", testMaxWaitTime},
        {"null_wait_time_rejected", testNullWaitTimeRejectedByType},
    };
    return sitp_test::runAll(tests);
}
