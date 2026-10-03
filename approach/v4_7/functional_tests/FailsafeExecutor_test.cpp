// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "FailsafeExecutor.h"

#include <memory>
#include <vector>

/** 创建不带策略的执行器。 */
FailsafeExecutor<int> makeExecutor() {
    return FailsafeExecutor<int>(std::vector<std::shared_ptr<Policy<int>>>{});
}

/** 验证构造函数保留空策略集合。 */
void testEmptyPolicies() {
    FailsafeExecutor<int> executor = makeExecutor();
    SITP_ASSERT_TRUE(executor.getPolicies().empty());
}

/** 验证同步 supplier 的返回值可以透传。 */
void testGetReturnsSupplierValue() {
    FailsafeExecutor<int> executor = makeExecutor();
    CheckedSupplier<int> supplier([]() { return 7; });
    SITP_ASSERT_EQ(7, executor.get(supplier));
}

/** 验证同步 runnable 恰好执行一次。 */
void testRunInvokesRunnable() {
    FailsafeExecutor<int> executor = makeExecutor();
    int calls = 0;
    CheckedRunnable runnable([&calls]() { ++calls; });
    executor.run(runnable);
    SITP_ASSERT_EQ(1, calls);
}

/** 组装并执行 Failsafe 执行器功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"empty_policies", testEmptyPolicies},
        {"get_returns_value", testGetReturnsSupplierValue},
        {"run_invokes_runnable", testRunInvokesRunnable},
    };
    return sitp_test::runAll(tests);
}
