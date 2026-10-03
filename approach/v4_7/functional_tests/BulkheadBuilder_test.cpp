// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "BulkheadBuilder.h"

#include <memory>
#include <vector>

/** 验证构建结果遵守最大并发许可数。 */
void testPermitLimit() {
    std::unique_ptr<Bulkhead<int>> bulkhead(BulkheadBuilder<int>(2).build());
    SITP_ASSERT_TRUE(bulkhead->tryAcquirePermit());
    SITP_ASSERT_TRUE(bulkhead->tryAcquirePermit());
    SITP_ASSERT_FALSE(bulkhead->tryAcquirePermit());
}

/** 验证释放许可后可以再次获取。 */
void testReleaseRestoresPermit() {
    std::unique_ptr<Bulkhead<int>> bulkhead(BulkheadBuilder<int>(1).build());
    SITP_ASSERT_TRUE(bulkhead->tryAcquirePermit());
    SITP_ASSERT_FALSE(bulkhead->tryAcquirePermit());
    bulkhead->releasePermit();
    SITP_ASSERT_TRUE(bulkhead->tryAcquirePermit());
}

/** 验证构建结果保留最大并发配置。 */
void testConfigDefaults() {
    std::unique_ptr<Bulkhead<int>> bulkhead(BulkheadBuilder<int>(3).build());
    SITP_ASSERT_EQ(3, bulkhead->getConfig().getMaxConcurrency());
    SITP_ASSERT_EQ(0L, bulkhead->getConfig().getMaxWaitTime().toNanos());
}

/** 验证最大等待时间配置及链式返回。 */
void testMaxWaitTime() {
    BulkheadBuilder<int> builder(2);
    Duration wait = Duration::ofNanos(5000000000L);
    SITP_ASSERT_TRUE(&builder.withMaxWaitTime(wait) == &builder);
    std::unique_ptr<Bulkhead<int>> bulkhead(builder.build());
    SITP_ASSERT_EQ(wait, bulkhead->getConfig().getMaxWaitTime());
}

/** 组装并执行舱壁构建器功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"permit_limit", testPermitLimit},
        {"release_restores_permit", testReleaseRestoresPermit},
        {"config_defaults", testConfigDefaults},
        {"max_wait_time", testMaxWaitTime},
    };
    return sitp_test::runAll(tests);
}
