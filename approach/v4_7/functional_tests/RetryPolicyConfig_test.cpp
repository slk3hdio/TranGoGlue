// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "RetryPolicyConfig.h"

#include <chrono>
#include <vector>

/** 验证默认重试次数对应一次总尝试且不允许重试。 */
void testDefaultRetryLimits() {
    RetryPolicyConfig<int> config;
    SITP_ASSERT_EQ(0, config.getMaxRetries());
    SITP_ASSERT_EQ(1, config.getMaxAttempts());
    SITP_ASSERT_FALSE(config.allowsRetries());
}

/** 验证默认退避系数和抖动系数为零。 */
void testDefaultFactors() {
    RetryPolicyConfig<int> config;
    SITP_ASSERT_EQ(0.0, config.getDelayFactor());
    SITP_ASSERT_EQ(0.0, config.getJitterFactor());
}

/** 验证复制构造保留公开配置语义。 */
void testCopyPreservesValues() {
    RetryPolicyConfig<int> original;
    RetryPolicyConfig<int> copied(original);
    SITP_ASSERT_EQ(original.getMaxRetries(), copied.getMaxRetries());
    SITP_ASSERT_EQ(original.getMaxAttempts(), copied.getMaxAttempts());
    SITP_ASSERT_EQ(original.allowsRetries(), copied.allowsRetries());
    SITP_ASSERT_EQ(original.getDelayFactor(), copied.getDelayFactor());
}

/** 验证默认的延迟值不会产生负时长。 */
void testDefaultDurationsAreNonNegative() {
    RetryPolicyConfig<int> config;
    SITP_ASSERT_TRUE(config.getDelayMin().count() >= 0);
    SITP_ASSERT_TRUE(config.getDelayMax().count() >= 0);
    SITP_ASSERT_TRUE(config.getMaxDelay().count() >= 0);
    SITP_ASSERT_TRUE(config.getMaxDuration().count() >= 0);
    SITP_ASSERT_TRUE(config.getJitter().count() >= 0);
}

/** 组装并执行重试配置功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"default_retry_limits", testDefaultRetryLimits},
        {"default_factors", testDefaultFactors},
        {"copy_preserves_values", testCopyPreservesValues},
        {"default_durations_non_negative", testDefaultDurationsAreNonNegative},
    };
    return sitp_test::runAll(tests);
}
