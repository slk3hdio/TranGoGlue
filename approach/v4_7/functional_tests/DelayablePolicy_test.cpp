// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "DelayablePolicyConfig.h"

#include <vector>

/** 提供可实例化的延迟配置以检查默认状态。 */
template<typename R>
class TestDelayablePolicyConfig final : public DelayablePolicyConfig<R> {
public:
    /** 创建默认测试配置。 */
    TestDelayablePolicyConfig() : DelayablePolicyConfig<R>() {}
};

/** 验证默认固定延迟为零。 */
void testDefaultDelay() {
    TestDelayablePolicyConfig<int> config;
    SITP_ASSERT_EQ(0L, config.getDelay().toNanos().count());
}

/** 验证默认未配置按上下文计算的延迟函数。 */
void testDefaultDelayFunctionMissing() {
    TestDelayablePolicyConfig<int> config;
    SITP_ASSERT_FALSE(static_cast<bool>(config.getDelayFn()));
}

/** 验证默认结果和异常过滤条件均未设置。 */
void testDefaultFiltersMissing() {
    TestDelayablePolicyConfig<int> config;
    SITP_ASSERT_EQ(0, config.getDelayResult());
    SITP_ASSERT_TRUE(config.getDelayException() == nullptr);
}

/** 组装并执行延迟策略配置功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"default_delay", testDefaultDelay},
        {"default_delay_function_missing", testDefaultDelayFunctionMissing},
        {"default_filters_missing", testDefaultFiltersMissing},
    };
    return sitp_test::runAll(tests);
}
